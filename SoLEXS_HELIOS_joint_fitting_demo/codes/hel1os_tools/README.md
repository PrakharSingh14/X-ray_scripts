# HEL1OS tools

Analysis tools provided by the **HEL1OS team**, included here **unmodified**. All of them read the level-1 event file
`evt.fits` (or Type-II spectra made from it) from the folder they are run in.

| Tool | What it does |
|---|---|
| `Evt-To-Mutiple-TypeI_V1.py` | Type-I spectra for a series of time bins (asks for date, start, end, bin length). **Used by `notebooks/1_make_spectra.ipynb`.** |
| `evt-to-typeI_V03.py` | one Type-I spectrum for a given time range (`--mode CDTE1 --start_time ... --end_time ...`) |
| `evt-to-TypeII-V04.py` | Type-II spectra (spectrum vs time) of each detector and of both CdTe / both CZT together |
| `TypeII-to-TypeI-Promt-based-V02.py` | Type-I spectra from a Type-II file, time ranges typed at the prompt |
| `TypeII-to-TypeI-GUI-based-V06.py` | the same, with time ranges selected on a plot |
| `LcFromEvtFile_V06.py` | light curves from `evt.fits` in user-defined energy bands (plot + `.csv`) |

The spectra refer to the response files by name (`hel1os_cdte_srf_v04.fits`, `hel1os_cdte_arf_v03.fits`, ...), so
copy the responses from `resources/hel1os_responses/` next to the spectra before loading them in XSPEC.
