# Xray_Data_Download

**Download tools for solar X-ray data from PRADAN: Chandrayaan-2 XSM and Aditya-L1 SoLEXS.**

Simple, re-runnable downloaders for two Indian solar X-ray instruments, whose data is on ISRO's PRADAN portal:

| Folder | Instrument | Mission | Portal | What you get per day |
|---|---|---|---|---|
| [`XSM/`](XSM/) | Solar X-ray Monitor | Chandrayaan-2 | [pradan.issdc.gov.in](https://pradan.issdc.gov.in) | Level-1 (`raw/`) and level-2 (`calibrated/`: spectrum, light curve, GTI) |
| [`SoLEXS/`](SoLEXS/) | Solar Low Energy X-ray Spectrometer | Aditya-L1 | [pradan1.issdc.gov.in](https://pradan1.issdc.gov.in) | Level-1 spectrum, light curve and GTI for each detector (`SDD1/`, `SDD2/`) |

You give a list of **days**, and each tool downloads the day files and unzips them into `Data/YYYYMMDD/`.

## How to use

Each folder is self-contained. Go into the one you need and follow its README:

- **[XSM/README.md](XSM/README.md)**
- **[SoLEXS/README.md](SoLEXS/README.md)**

In short:
1. `pip install -r requirements.txt` (only `requests` is needed)
2. Log in to PRADAN and save the generated download script into the folder. This gives the tool your login cookie.
3. Write your days in `days.txt`, e.g. `2025-09-09` or a range `2025-09-01 : 2025-09-05`
4. Run `python xsm_download.py` / `python solexs_download.py`, or the notebook in the same folder

Both tools:
- resume interrupted downloads and skip days that are already done, so re-running is always safe;
- check your login before starting, and tell you clearly when it has expired;
- report days with no data on PRADAN instead of stopping;
- download one day at a time, to stay within PRADAN's usage limits.

## Requirements

- Python 3.8+ and `requests`
- Jupyter, only if you want to use the notebooks
- A PRADAN account (free registration on the portal). The data itself is downloaded under your own login.

## Note on login cookies

The PRADAN download scripts (`xsm_20*.py`, `solexs_20*.py`) and `cookie.txt` contain **your login session**.
They are excluded by `.gitignore`. Never commit or share them.
