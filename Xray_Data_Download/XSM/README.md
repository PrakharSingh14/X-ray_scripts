# XSM data download (Chandrayaan-2 XSM, by day)

Downloads **Chandrayaan-2 XSM** (Solar X-ray Monitor) day files from ISRO's
[PRADAN](https://pradan.issdc.gov.in) portal for any list of days, and unzips each day into a tidy folder.
You can use it as a **Python script** (`xsm_download.py`) or as a **Jupyter notebook** (`download_xsm_days.ipynb`).
Both use the same code.

---

## Quick start

1. **Install:** Python 3.8+ with `requests` (`pip install -r requirements.txt`). Jupyter is only needed for the notebook.
2. **Log in to PRADAN and give the login cookie:** save the PRADAN script `xsm_<timestamp>.py` into this folder, *or*
   paste the cookie into `cookie.txt` (see [Getting the login cookie](#getting-the-login-cookie)).
3. **List your days** in `days.txt` (see [Giving dates](#giving-dates)).
4. **Run** one of these:
   ```bash
   python xsm_download.py
   ```
   or open `download_xsm_days.ipynb` and run all cells.

You can stop it and run it again at any time. Finished days are skipped and half-done downloads resume.

---

## Files in this folder

| File | What it is | Do you edit it? |
|---|---|---|
| `xsm_download.py` | All the code. Run it directly, or the notebook imports it | Only the **USER SETTINGS** block at the top |
| `download_xsm_days.ipynb` | Notebook version | Only the **Settings** cell |
| `days.txt` | Your list of days (it explains the format at the top) | **Yes** |
| `days.csv` | Example of the same list as a CSV | Optional |
| `xsm_20*.py` | Your PRADAN login script (you download it). Holds the cookie | No. **Never share it** |
| `cookie.txt` | Alternative to the script: paste the cookie here | Optional. **Never share it** |
| `requirements.txt` | Python dependency (`requests`) | No |

Keep `xsm_download.py` and the notebook in the same folder.

---

## What you can change

Set these in the **USER SETTINGS** block of `xsm_download.py`, or in the **Settings** cell of the notebook:

| Setting | Default | Meaning |
|---|---|---|
| `DAYS_FILE` | `'days.txt'` | File with your days (`.txt` or `.csv`). A name in this folder or a full path |
| `DAYS` *(notebook only)* | `None` | List days directly instead of a file, e.g. `['2025-09-09', '2024-05-10 : 2024-05-12']` |
| `OUTPUT_DIR` | `'.'` | Where `Data_zip/` and `Data/` are created. Use a big disk for many days |
| `KEEP_ZIPS` | `True` | `False` deletes each zip after unzipping |
| `DRY_RUN` | `False` | `True` only prints what would happen, without downloading anything |

Nothing else needs changing.

---

## Getting the login cookie

PRADAN only serves data to logged-in users, so the code needs your **login cookie**. There are two ways to give it.
Use either one: you don't need both.

### Option A: PRADAN script (easiest)

1. Go to <https://pradan.issdc.gov.in> and **log in**.
2. Open the **Chandrayaan-2 → XSM** data and **select any one file**. Which day doesn't matter, because the days you get
   come from `days.txt`.
3. **Download the generated script** (not the data). You get `xsm_<timestamp>.py`, e.g. `xsm_2026Jan01T120000000.py`.
4. Put it **in this folder** without renaming it. The name must start with `xsm_20`.

### Option B: paste the cookie into `cookie.txt`

1. Log in to PRADAN in the browser and open developer tools (**Cmd+Option+I**, or **F12** on Windows/Linux).
2. Go to the **Network** tab, reload the page, and click the first request.
3. Under **Headers → Request Headers**, right-click the **`Cookie:`** value → **Copy value**.
4. Paste it into `cookie.txt` in this folder, below the `#` notes, and save. It looks like:
   ```
   FGTServer=XXXXXXXX...; JSESSIONID=XXXXXXXX...; OAuth_Token_Request_State=XXXXXXXX-XXXX-...
   ```
   Copy the **whole** line. A leading `Cookie:` or quotes are fine.

### Which one is used?

- The **newest** file that holds a cookie is used: the latest `xsm_20*.py`, or `cookie.txt` if you saved it more recently.
  So when the cookie expires, just refresh whichever one you prefer.
- The cookie works as long as your PRADAN login session lasts. **Stay logged in** in the browser while downloading.
  You only need a new cookie when you see `SESSION EXPIRED`.
- The run prints which file it took the cookie from, e.g. `Cookie from: cookie.txt (downloaded 0.2 h ago)`.

> The cookie gives access to your PRADAN account, like a password. Don't share `xsm_20*.py` or `cookie.txt`, or
> commit them to git (`.gitignore` already excludes them). Log out of PRADAN when you are done to end the session.
>
> **Sharing this folder** as a zip or copy (not through git)? First delete your `xsm_20*.py` files, and empty
> `cookie.txt` back to its `#` notes. `Data/` and `Data_zip/` can also be left out.

---

## Giving dates

One date or range per line, in `days.txt` (or the first column of a `.csv`):

```
2025-09-09                  # YYYY-MM-DD
20250909                    # YYYYMMDD
2025/09/09                  # YYYY/MM/DD
2024-05-10 : 2024-05-12     # range, both ends included (3 days)
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
│   └── ch2_xsm_20250909_v1.zip          one zip per day, as served by PRADAN
└── Data/
    └── 20250909/
        ├── raw/                         level-1: ch2_xsm_20250909_v1_level1.fits / .hk / .sa  (+ .xml labels)
        └── calibrated/                  level-2: ch2_xsm_20250909_v1_level2.pha / .lc / .gti  (+ .xml labels)
```

- **`calibrated/`** holds the ready-to-use spectrum (`.pha`), light curve (`.lc`) and good-time intervals (`.gti`).
- **`raw/`** holds the level-1 data you need to make your own spectra/light curves with the XSM software (`xsmgenspec`, `xsmgenlc`).
- A hidden `.complete` file marks a finished day. Delete the day's folder to redo it.

### Disk space

| Per day | Size |
|---|---|
| Zip | ~20-25 MB |
| Unzipped (`raw/` + `calibrated/`) | ~200 MB (the level-1 `.fits` is ~175 MB) |

Set `KEEP_ZIPS=False` to delete the zips once they are unzipped.

---

## Command-line options

Options override the USER SETTINGS:

```bash
python xsm_download.py                                   # days from DAYS_FILE
python xsm_download.py my_days.csv                       # another days file
python xsm_download.py --date 2025-09-09 --date "2024-05-10 : 2024-05-12"   # days without a file
python xsm_download.py --out /Volumes/Data/xsm           # store elsewhere
python xsm_download.py --delete-zips
python xsm_download.py --dry-run                         # check before downloading
python xsm_download.py -h                                # all options
```

The script exits with code 1 if any day was not finished, which is useful in batch jobs.

---

## How it works

For each day the script:
1. **Skips** it if `Data/YYYYMMDD/` is already complete.
2. **Unzips only** if the zip is already in `Data_zip/`.
3. Otherwise **downloads** it. PRADAN stores XSM days in `auto/YYYY/` (2022 onwards) and in release folders such as
   `23Feb2022/` (2021 data), so the likely folder is tried first. If a day appears in one of your `xsm_20*.py`
   scripts, that exact path is used.
4. **Unzips right away** into `raw/` and `calibrated/`, then optionally deletes the zip.

Downloads **resume** from `.part` files, **retry** 5 times, are **checked** to be valid zips, and a background ping keeps
the PRADAN session alive during long runs. At the end, a **summary** lists each day's status.

---

## Troubleshooting

| Message | What to do |
|---|---|
| `No login cookie in ...` | Put a PRADAN `xsm_20*.py` script in this folder, or paste the cookie into `cookie.txt` (see [Getting the login cookie](#getting-the-login-cookie)) |
| `SESSION EXPIRED / NOT AUTHORISED` | Log in to PRADAN again, put a fresh `xsm_*.py` or `cookie.txt` into this folder and re-run. Finished days are kept |
| `NOT LOGGED IN: PRADAN rejected this cookie` | Checked before downloading: the cookie is expired or incomplete. Log in again and refresh `xsm_*.py` / `cookie.txt` |
| `NOT AVAILABLE on PRADAN (HTTP 401, although logged in)` | Your login is fine, but PRADAN refuses that one day's file (e.g. not released yet). Check the day on the portal. If it is listed there, select that day when you download the `xsm_*.py` script, so its exact path is used |
| `Cookie ... downloaded 30.0 h ago` warning | The cookie may have expired. If downloads fail, get a fresh one |
| `NOT FOUND on PRADAN` | No data for that day (e.g. before XSM started in Sep 2019, a data gap, or not released yet). Check the day on the portal. If it is in a new release folder, add the folder name to `RELEASE_FOLDERS` in `xsm_download.py`, or just select that day when you download the login script |
| `cannot read date ...` | Fix the date format on the named line (see [Giving dates](#giving-dates)) |
| `attempt 1/5 failed` | Network hiccup. It retries automatically. If all attempts fail, re-run later |
| Notebook doesn't see edits to `xsm_download.py` | Re-run the Run cell (it reloads the module) or restart the kernel |

Days are downloaded one at a time, with a short pause in between, to be gentle with PRADAN. The server has session download limits and
may temporarily block heavy automated use.
