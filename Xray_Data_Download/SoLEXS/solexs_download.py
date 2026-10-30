"""
Download Aditya-L1 SoLEXS level-1 day files from PRADAN and unzip them into Data/YYYYMMDD/{SDD1,SDD2}/.

Usage:  python solexs_download.py [days_file] [--date DAY] [--out DIR] [--delete-zips] [--dry-run]
See README.md for the login cookie, date formats and options.
"""

# =====================================================================================
# USER SETTINGS
# =====================================================================================
DAYS_FILE  = 'days.txt'    # .txt or .csv with your days
OUTPUT_DIR = '.'           # where Data_zip/ and Data/ go
KEEP_ZIPS  = True          # False = delete zips after unzipping
DRY_RUN    = False         # True = only show what would be done
# =====================================================================================

import re
import sys
import time
import shutil
import zipfile
import argparse
import threading
from pathlib import Path
from datetime import date, datetime, timedelta

import requests

HERE = Path(__file__).resolve().parent
PRADAN_SCRIPT_GLOB = 'solexs_20*.py'   # e.g. solexs_2026Jan01T120000000.py
COOKIE_FILE = 'cookie.txt'             # or paste the browser's Cookie header here; the newer of the two is used
DONE_MARKER = '.complete'              # written in Data/YYYYMMDD/ after a full unzip

MAX_RETRIES = 5
RETRY_WAIT_SECONDS = 30
PAUSE_BETWEEN_FILES = 2                # seconds between downloads, be gentle with the server
CHUNK_SIZE = 8 * 1024 * 1024

URL_PREFIX = 'https://pradan1.issdc.gov.in'            # Aditya-L1 data is on pradan1, not pradan
SESSION_CHECK_PATH = '/al1/protected/payload.xhtml'   # 200 when logged in, 302 to the login page when not
SOLEXS_LEVEL1 = '/al1/protected/downloadData/solexs/level1/'
# Day files live in level1/YYYY/MM/N00_0000/. If a day appears in a PRADAN script, that exact path is used instead.
DAY_SUBFOLDER = 'N00_0000'
FILE_VERSION = 'v1.0'


def _resolve(p):
    p = Path(p).expanduser()
    return p if p.is_absolute() else HERE / p


# ---------------------------------------------------------------- days

def _parse_day(text):
    text = text.strip()
    for fmt in ('%Y-%m-%d', '%Y%m%d', '%Y/%m/%d'):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    raise ValueError(f'cannot read date {text!r} (use YYYY-MM-DD, YYYYMMDD or YYYY/MM/DD)')


def parse_days(lines, source='input'):
    """Sorted unique days (YYYYMMDD) from lines of dates / 'start : end' ranges ('#' notes, csv first column)."""
    days = set()
    for n, line in enumerate(lines, 1):
        line = line.split('#')[0].split(',')[0].strip()
        if not line or line.lower() in ('date', 'day', 'days'):
            continue
        try:
            if ':' in line:
                d0, d1 = (_parse_day(s) for s in line.split(':'))
                if d1 < d0:
                    raise ValueError('range end is before range start')
                days.update(d0 + timedelta(days=i) for i in range((d1 - d0).days + 1))
            else:
                days.add(_parse_day(line))
        except ValueError as e:
            raise ValueError(f'{source} line {n}: {e}') from None
    if any(d > date.today() for d in days):
        print('Warning: some days are in the future')
    return sorted(d.strftime('%Y%m%d') for d in days)


def read_days(days_file=DAYS_FILE):
    days_file = _resolve(days_file)
    if not days_file.exists():
        raise FileNotFoundError(f'days file not found: {days_file}')
    return parse_days(days_file.read_text().splitlines(), days_file.name)


# ---------------------------------------------------------------- PRADAN login + paths

class SessionExpired(Exception):
    pass

class NotOnServer(Exception):
    pass

class NotAvailable(NotOnServer):
    """PRADAN refuses the file (HTTP 401/403) although the login is valid - pradan1 answers a missing day this way."""
    pass


def _cookie_from_txt(path):
    """Cookie from cookie.txt: '#' lines ignored, a leading 'Cookie:' and surrounding quotes are allowed."""
    lines = [l.strip() for l in path.read_text().splitlines() if l.strip() and not l.strip().startswith('#')]
    cookie = ' '.join(lines).strip()
    cookie = re.sub(r'^cookie:\s*', '', cookie, flags=re.I).strip('\'"')
    return cookie or None


def _cookie_from_script(path):
    m = re.search(r'cookie_string\s*=\s*"([^"]*)"', path.read_text())
    return m.group(1).strip() if m and m.group(1).strip() else None


class Pradan:
    """Login cookie (newest of cookie.txt / solexs_20*.py) and per-day paths from the PRADAN scripts."""

    def __init__(self, cookie_dir=HERE):
        cookie_dir = Path(cookie_dir)
        scripts = sorted(cookie_dir.glob(PRADAN_SCRIPT_GLOB), key=lambda p: p.stat().st_mtime)

        # newest file that actually holds a cookie wins
        sources = [(s, _cookie_from_script) for s in scripts]
        txt = cookie_dir / COOKIE_FILE
        if txt.exists():
            sources.append((txt, _cookie_from_txt))
        self.cookie_file, cookie = None, None
        for f, read in sorted(sources, key=lambda s: s[0].stat().st_mtime, reverse=True):
            cookie = read(f)
            if cookie:
                self.cookie_file = f
                break
        if not cookie:
            raise FileNotFoundError(f'No login cookie in {cookie_dir}: put a PRADAN {PRADAN_SCRIPT_GLOB} script '
                                    f'there, or paste the cookie into {COOKIE_FILE} (see README.md)')
        self.headers = {'Cookie': cookie}
        self.session = requests.Session()

        # day -> exact PRADAN path from any script (newer scripts win)
        self.script_paths = {}
        for s in scripts:
            for p in re.findall(r'"(/al1/protected/downloadData/solexs/level1/[^"]+)"', s.read_text()):
                m = re.search(r'AL1_SLX_L1_(\d{8})_v[\d.]+\.zip', p)
                if m:
                    self.script_paths[m.group(1)] = p

    def describe(self):
        age_h = (time.time() - self.cookie_file.stat().st_mtime) / 3600
        print(f'Cookie from: {self.cookie_file.name}  (downloaded {age_h:.1f} h ago)')
        if age_h > 12:
            print('  -> this is old, the session has probably expired: get a fresh cookie if downloads fail')

    def logged_in(self):
        try:
            r = self.session.get(URL_PREFIX + SESSION_CHECK_PATH, headers=self.headers, timeout=(30, 60), allow_redirects=False)
            return r.status_code == 200
        except requests.RequestException:
            return True        # network trouble is not proof of a logout; the download itself will retry

    def candidate_paths(self, day):
        """Exact path from a PRADAN script if known, else the standard level1/YYYY/MM/N00_0000/ path."""
        if day in self.script_paths:
            return [self.script_paths[day]]
        return [f'{SOLEXS_LEVEL1}{day[:4]}/{day[4:6]}/{DAY_SUBFOLDER}/AL1_SLX_L1_{day}_{FILE_VERSION}.zip?solexs']

    def download_one(self, path, zip_dir):
        """Download one PRADAN path into zip_dir, with resume + retries. Returns the final file path."""
        url = URL_PREFIX + path
        final_file = Path(zip_dir) / Path(path.split('?')[0]).name
        part_file = final_file.with_name(final_file.name + '.part')
        tag = re.search(r'\d{8}', final_file.name).group(0)

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                req_headers = dict(self.headers)
                resume_from = part_file.stat().st_size if part_file.exists() else 0
                if resume_from:
                    req_headers['Range'] = f'bytes={resume_from}-'
                    print(f'  {tag}: resuming from {resume_from/1024**2:.1f} MB')

                with self.session.get(url, headers=req_headers, stream=True, timeout=(30, 600), allow_redirects=False) as r:
                    if r.status_code in (301, 302, 303, 307, 308):
                        raise SessionExpired(f'HTTP {r.status_code} -> {r.headers.get("Location", "")}')
                    if r.status_code in (401, 403):
                        if not self.logged_in():
                            raise SessionExpired(f'HTTP {r.status_code}')
                        raise NotAvailable(f'HTTP {r.status_code}')
                    if r.status_code == 404 or (r.status_code == 500 and 'html' in r.headers.get('Content-Type', '')):
                        raise NotOnServer(url)
                    if r.status_code == 416:            # range not satisfiable: .part is already complete
                        pass
                    elif r.status_code not in (200, 206):
                        raise RuntimeError(f'HTTP {r.status_code}')
                    elif 'html' in r.headers.get('Content-Type', ''):
                        raise SessionExpired('got an HTML page instead of a zip (probably the login page)')
                    else:
                        mode = 'ab' if (resume_from and r.status_code == 206) else 'wb'
                        done = resume_from if mode == 'ab' else 0
                        with open(part_file, mode) as f:
                            for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                                if chunk:
                                    f.write(chunk)
                                    done += len(chunk)
                                    print(f'\r  {tag}: {done/1024**2:.1f} MB', end='', flush=True)
                        print()

                if not zipfile.is_zipfile(part_file):
                    part_file.unlink()
                    raise RuntimeError('downloaded file is not a valid zip (deleted, will retry)')
                part_file.rename(final_file)
                print(f'  {tag}: downloaded {final_file.name} ({final_file.stat().st_size/1024**2:.1f} MB)')
                return final_file

            except (SessionExpired, NotOnServer):
                raise
            except Exception as e:
                print(f'  {tag}: attempt {attempt}/{MAX_RETRIES} failed: {e}')
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_WAIT_SECONDS)
        raise RuntimeError(f'giving up on {url}')

    def keep_alive(self, stop):
        # ping PRADAN every 10 min so the session doesn't time out during long runs
        while not stop.wait(600):
            try:
                requests.get(URL_PREFIX + SESSION_CHECK_PATH, headers=self.headers, timeout=(30, 60))
            except Exception as e:
                print(f'[keep-alive error] {e}')


# ---------------------------------------------------------------- unzip

def existing_zip(day, zip_dir):
    """Already-downloaded zip for this day (any version), or None."""
    found = sorted(Path(zip_dir).glob(f'AL1_SLX_L1_{day}_v*.zip'))
    return found[-1] if found else None


def flat_name(member):
    """'AL1_SLX_L1_20250909_v1.0/SDD2/x.pi.gz' -> 'SDD2/x.pi.gz' (drops the zip's top folder)."""
    parts = Path(member).parts
    return Path(*parts[1:]) if len(parts) > 1 and parts[0].startswith('AL1_SLX_L1_') else Path(member)


def is_done(dest):
    return (Path(dest) / DONE_MARKER).exists()


def unzip_day(zip_file, dest):
    """Unzip into dest/{SDD1,SDD2}/, then write the done marker."""
    dest = Path(dest)
    with zipfile.ZipFile(zip_file) as zf:
        for m in zf.infolist():
            if m.is_dir():
                continue
            out = dest / flat_name(m.filename)
            out.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(m) as src, open(out, 'wb') as dst:
                shutil.copyfileobj(src, dst)
    (dest / DONE_MARKER).touch()


# ---------------------------------------------------------------- pipeline

def run(days=None, days_file=DAYS_FILE, output_dir=OUTPUT_DIR, keep_zips=KEEP_ZIPS,
        dry_run=DRY_RUN, cookie_dir=HERE):
    """Download + unzip every day, one at a time. `days` (list of date strings/ranges) wins over `days_file`.
    Returns {day: status}."""
    days = parse_days(days, 'days list') if days is not None else read_days(days_file)
    out = _resolve(output_dir)
    zip_dir, data_dir = out / 'Data_zip', out / 'Data'
    print(f'{len(days)} days | output: {out} | keep zips: {keep_zips}' + (' | DRY RUN' if dry_run else ''))

    todo = [d for d in days if not is_done(data_dir / d)]
    status = {d: 'already done' for d in days if d not in todo}
    need_download = [d for d in todo if existing_zip(d, zip_dir) is None]
    print(f'{len(status)} already done, {len(todo) - len(need_download)} to unzip only, {len(need_download)} to download')
    if not todo:
        return _summary(status)

    pradan = None
    if need_download:
        pradan = Pradan(cookie_dir)
        pradan.describe()
        if not dry_run and not pradan.logged_in():
            print('\nNOT LOGGED IN: PRADAN rejected this cookie. Log in to PRADAN again, put a fresh solexs_*.py '
                  '(or cookie.txt) into this folder and re-run.')
            status.update({d: 'skipped (session expired)' for d in need_download})
            todo = [d for d in todo if d not in need_download]      # zips already here can still be unzipped
    if not dry_run:
        zip_dir.mkdir(parents=True, exist_ok=True)

    def process(day):
        """Download (if needed) + unzip one day. Returns its status; SessionExpired is passed up."""
        z = existing_zip(day, zip_dir)
        try:
            if z is None:
                paths = pradan.candidate_paths(day)
                if dry_run:
                    return f'would download ({paths[0].split("level1/")[1].split("?")[0]})'
                reason = 'NOT FOUND on PRADAN'
                for path in paths:
                    try:
                        z = pradan.download_one(path, zip_dir)
                        break
                    except NotAvailable as e:
                        reason = f'NOT AVAILABLE on PRADAN ({e}, although logged in)'
                    except NotOnServer:
                        pass
                    finally:
                        time.sleep(PAUSE_BETWEEN_FILES)
                else:
                    return reason
                result = 'downloaded + unzipped'
            elif dry_run:
                return f'would unzip {z.name}'
            else:
                result = 'unzipped'
            unzip_day(z, data_dir / day)
            if not keep_zips:
                z.unlink()
            return result
        except SessionExpired:
            raise
        except Exception as e:
            return f'FAILED: {e}'

    expired = False                 # after a session expiry only days with a local zip are still unzipped
    ka_stop = threading.Event()
    if need_download and not dry_run:
        threading.Thread(target=pradan.keep_alive, args=(ka_stop,), daemon=True).start()
    try:
        for day in todo:
            if expired and existing_zip(day, zip_dir) is None:
                status[day] = 'skipped (session expired)'
                continue
            try:
                status[day] = process(day)
            except SessionExpired as e:
                expired = True
                status[day] = 'skipped (session expired)'
                print(f'\nSESSION EXPIRED / NOT AUTHORISED: {e}\n'
                      'Log in to PRADAN again, put a fresh solexs_*.py (or cookie.txt) into this folder and re-run '
                      '(finished days are kept, partial downloads resume).')
    finally:
        ka_stop.set()
    return _summary(status)


def _summary(status):
    print('\nSummary:')
    for day in sorted(status):
        print(f'  {day}: {status[day]}')
    bad = [d for d, s in status.items() if s.startswith(UNFINISHED)]
    if bad:
        print(f'\n{len(bad)} day(s) not finished: {", ".join(sorted(bad))}')
        for key, hint in UNFINISHED_HINTS.items():
            if any(status[d].startswith(key) for d in bad):
                print(f'  {key}: {hint}')
    return status


UNFINISHED_HINTS = {
    'skipped':       'login expired - refresh solexs_*.py or cookie.txt and re-run',
    'NOT FOUND':     'no file at the usual PRADAN path - check the day on the portal',
    'NOT AVAILABLE': 'no SoLEXS file for this day at the usual path (data gap, before data started, or not released yet) '
                     '- check the day on the portal; if it is listed, select it when you download the solexs_*.py '
                     'script so its exact path is used',
    'FAILED':        'network/server problem - re-run later',
}
UNFINISHED = tuple(UNFINISHED_HINTS)


def main(argv=None):
    ap = argparse.ArgumentParser(description='Download + unzip Aditya-L1 SoLEXS level-1 day files from PRADAN.')
    ap.add_argument('days_file', nargs='?', default=DAYS_FILE, help=f'days file (default: {DAYS_FILE})')
    ap.add_argument('--date', action='append', metavar='DAY', help='day or "start : end" range; repeatable, replaces the days file')
    ap.add_argument('--out', default=OUTPUT_DIR, help='where Data_zip/ and Data/ are created')
    ap.add_argument('--delete-zips', action='store_true', default=not KEEP_ZIPS, help='delete each zip once unzipped')
    ap.add_argument('--dry-run', action='store_true', default=DRY_RUN, help='only show what would be done')
    args = ap.parse_args(argv)

    # paths typed on the command line are relative to where you run it from; the defaults to this folder
    days_file = args.days_file if args.days_file == DAYS_FILE else Path(args.days_file).resolve()
    out = args.out if args.out == OUTPUT_DIR else Path(args.out).resolve()
    try:
        status = run(days=args.date, days_file=days_file, output_dir=out,
                     keep_zips=not args.delete_zips, dry_run=args.dry_run)
    except (FileNotFoundError, ValueError) as e:
        print(f'ERROR: {e}')
        return 1
    return 1 if any(s.startswith(UNFINISHED) for s in status.values()) else 0


if __name__ == '__main__':
    sys.exit(main())
