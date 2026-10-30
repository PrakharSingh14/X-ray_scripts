# SoLEXS data download (Aditya-L1 SoLEXS, by day)

Downloads **Aditya-L1 SoLEXS** (Solar Low Energy X-ray Spectrometer) **level-1** day files from ISRO's
[PRADAN](https://pradan1.issdc.gov.in) portal for any list of days, and unzips each day into a tidy folder.
You can use it as a **Python script** (`solexs_download.py`) or as a **Jupyter notebook** (`download_solexs_days.ipynb`).
Both use the same code.

PRADAN stores data as **one zip per UTC day** (00:00-24:00), so you list days, not times or events.

---

## Quick start

1. **Install:** Python 3.8+ with `requests` (`pip install -r requirements.txt`). Jupyter is only needed for the notebook.
2. **Log in to PRADAN and give the login cookie:** save the PRADAN script `solexs_<timestamp>.py` into this folder, *or*
   paste the cookie into `cookie.txt` (see [Getting the login cookie](#getting-the-login-cookie)).
3. **List your days** in `days.txt` (see [Giving dates](#giving-dates)).
4. **Run** one of these:
   ```bash
   python solexs_download.py
   ```
   or open `download_solexs_days.ipynb` and run all cells.

You can stop it and run it again at any time. Finished days are skipped and half-done downloads resume.

---

## Files in this folder

| File | What it is | Do you edit it? |
|---|---|---|
| `solexs_download.py` | All the code. Run it directly, or the notebook imports it | Only the **USER SETTINGS** block at the top |
| `download_solexs_days.ipynb` | Notebook version | Only the **Settings** cell |
| `days.txt` | Your list of days (it explains the format at the top) | **Yes** |
| `days.csv` | Example of the same list as a CSV | Optional |
| `solexs_20*.py` | Your PRADAN login script (you download it). Holds the cookie | No. **Never share it** |
| `cookie.txt` | Alternative to the script: paste the cookie here | Optional. **Never share it** |
| `requirements.txt` | Python dependency (`requests`) | No |

Keep `solexs_download.py` and the notebook in the same folder.

---

## What you can change

Set these in the **USER SETTINGS** block of `solexs_download.py`, or in the **Settings** cell of the notebook:

| Setting | Default | Meaning |
|---|---|---|
| `DAYS_FILE` | `'days.txt'` | File with your days (`.txt` or `.csv`). A name in this folder or a full path |
| `DAYS` *(notebook only)* | `None` | List days directly instead of a file, e.g. `['2025-09-09', '2025-01-01 : 2025-01-03']` |
| `OUTPUT_DIR` | `'.'` | Where `Data_zip/` and `Data/` are created |
| `KEEP_ZIPS` | `True` | `False` deletes each zip after unzipping |
| `DRY_RUN` | `False` | `True` only prints what would happen, without downloading anything |

Nothing else needs changing.

---

## Getting the login cookie

PRADAN only serves data to logged-in users, so the code needs your **login cookie**. There are two ways to give it.
Use either one: you don't need both.

> Aditya-L1 data is on **`pradan1.issdc.gov.in`**, a different server from Chandrayaan-2 (`pradan.issdc.gov.in`).
> A cookie from one does not work on the other, so take it from the Aditya-L1 side.

### Option A: PRADAN script (easiest)

1. Go to <https://pradan1.issdc.gov.in> and **log in**.
2. Open the **Aditya-L1 → SoLEXS** data and **select any one file**. Which day doesn't matter, because the days you
   get come from `days.txt`.
3. **Download the generated script** (not the data). You get `solexs_<timestamp>.py`, e.g. `solexs_2026Jan01T120000000.py`.
4. Put it **in this folder** without renaming it. The name must start with `solexs_20`.

### Option B: paste the cookie into `cookie.txt`

1. Log in to <https://pradan1.issdc.gov.in> in the browser and open developer tools (**Cmd+Option+I**, or **F12** on
   Windows/Linux).
2. Go to the **Network** tab, reload the page, and click the first request.
3. Under **Headers → Request Headers**, right-click the **`Cookie:`** value → **Copy value**.
4. Paste it into `cookie.txt` in this folder, below the `#` notes, and save. It looks like:
   ```
   FGTServer=XXXXXXXX...; JSESSIONID=XXXXXXXX...; OAuth_Token_Request_State=XXXXXXXX-XXXX-...
   ```
   Copy the **whole** line. A leading `Cookie:` or quotes are fine.

### Which one is used?

- The **newest** file that holds a cookie is used: the latest `solexs_20*.py`, or `cookie.txt` if you saved it more
  recently. So when the cookie expires, just refresh whichever one you prefer.
- The cookie works as long as your PRADAN login session lasts. **Stay logged in** in the browser while downloading.
  You only need a new cookie when you see `SESSION EXPIRED`.
- The run prints which file it took the cookie from, e.g. `Cookie from: cookie.txt (downloaded 0.2 h ago)`.

> The cookie gives access to your PRADAN account, like a password. Don't share `solexs_20*.py` or `cookie.txt`, or
> commit them to git (`.gitignore` already excludes them). Log out of PRADAN when you are done to end the session.
>
> **Sharing this folder** as a zip or copy (not through git)? First delete your `solexs_20*.py` files, and empty
> `cookie.txt` back to its `#` notes. `Data/` and `Data_zip/` can also be left out.

---

## Giving dates

One date or range per line, in `days.txt` (or the first column of a `.csv`):

```
2025-09-09                  # YYYY-MM-DD
20250909                    # YYYYMMDD
2025/09/09                  # YYYY/MM/DD
2025-01-01 : 2025-01-03     # range, both ends included (3 days)
```

- Anything after `#` is a note. Blank lines are ignored, and so is a header line `date` / `day` / `days`.
- Order and duplicates don't matter: days are sorted and de-duplicated.
- **Not accepted:** day-first dates (`09-09-2025`), month names (`9 Sep 2025`), or times (`2025-09-09 04:30`).
  The script stops and names the bad line.

---

## Output

```
OUTPUT_DIR/
├── Data_zip/
│   └── AL1_SLX_L1_20250909_v1.0.zip         one zip per day, as served by PRADAN
└── Data/
    └── 20250909/
        ├── SDD1/                            detector 1: AL1_SOLEXS_20250909_SDD1_L1.pi.gz / .lc.gz / .gti.gz
        └── SDD2/                            detector 2: AL1_SOLEXS_20250909_SDD2_L1.pi.gz / .lc.gz / .gti.gz
```

- **SDD1 and SDD2** are SoLEXS's two detectors. Each has a spectrum file (`.pi.gz`), a light curve (`.lc.gz`) and
  good-time intervals (`.gti.gz`).
- **A detector folder can be incomplete.** If a detector was not observing that day, its folder may hold only the
  `.gti.gz` file.
- The files are **gzipped FITS** and are kept compressed: astropy (`fits.open`), XSPEC and ds9 read `.gz` files directly.
- A hidden `.complete` file marks a finished day. Delete the day's folder to redo it.
- **Size:** a zip is about 2-10 MB per day, and an unzipped day is similar.

---

## Command-line options

Options override the USER SETTINGS:

```bash
python solexs_download.py                                   # days from DAYS_FILE
python solexs_download.py my_days.csv                       # another days file
python solexs_download.py --date 2025-09-09 --date "2025-01-01 : 2025-01-03"   # days without a file
python solexs_download.py --out /Volumes/Data/solexs        # store elsewhere
python solexs_download.py --delete-zips
python solexs_download.py --dry-run                         # check before downloading
python solexs_download.py -h                                # all options
```

The script exits with code 1 if any day was not finished, which is useful in batch jobs.

---

## How it works

For each day the script:
1. **Skips** it if `Data/YYYYMMDD/` is already complete.
2. **Unzips only** if the zip is already in `Data_zip/`.
3. Otherwise **downloads** it from `level1/YYYY/MM/N00_0000/AL1_SLX_L1_YYYYMMDD_v1.0.zip` on PRADAN. If a day appears
   in one of your `solexs_20*.py` scripts, that exact path is used instead.
4. **Unzips right away** into `SDD1/` and `SDD2/`, then optionally deletes the zip.

Downloads happen one at a time, **resume** from `.part` files, **retry** 5 times, are **checked** to be valid zips,
and a background ping keeps the PRADAN session alive during long runs. The login is checked before the first download.
At the end, a **summary** lists each day's status.

---

## Troubleshooting

| Message | What to do |
|---|---|
| `No login cookie in ...` | Put a PRADAN `solexs_20*.py` script in this folder, or paste the cookie into `cookie.txt` (see [Getting the login cookie](#getting-the-login-cookie)) |
| `NOT LOGGED IN: PRADAN rejected this cookie` | Checked before downloading: the cookie is expired, incomplete, or from the Chandrayaan-2 server. Log in to `pradan1` again and refresh `solexs_*.py` / `cookie.txt` |
| `SESSION EXPIRED / NOT AUTHORISED` | Log in to PRADAN again, put a fresh `solexs_*.py` or `cookie.txt` into this folder and re-run. Finished days are kept |
| `NOT AVAILABLE on PRADAN (HTTP 401, although logged in)` | Your login is fine, but there is no SoLEXS file for that day at the usual path. This is how this server reports a missing day: a data gap, a day before data started, or not released yet. Check the day on the portal. If it is listed there, select that day when you download the `solexs_*.py` script, so its exact path is used |
| `Cookie ... downloaded 30.0 h ago` warning | The cookie may have expired. If downloads fail, get a fresh one |
| `cannot read date ...` | Fix the date format on the named line (see [Giving dates](#giving-dates)) |
| `attempt 1/5 failed` | Network hiccup. It retries automatically. If all attempts fail, re-run later |
| Notebook doesn't see edits to `solexs_download.py` | Re-run the Run cell (it reloads the module) or restart the kernel |

Days are downloaded one at a time, with a short pause in between, to be gentle with PRADAN. The server has session
download limits and may temporarily block heavy automated use.
