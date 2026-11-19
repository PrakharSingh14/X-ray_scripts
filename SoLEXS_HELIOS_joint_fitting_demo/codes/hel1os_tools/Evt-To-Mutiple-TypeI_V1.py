
#python evt-to-typeI_V03.py --mode CZT1
import numpy as np
import pandas as pd
import argparse
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from astropy.io import fits
from astropy.time import Time
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks
from matplotlib.backends.backend_pdf import PdfPages
import glob
 

def validate_time_format(time_str):
    try:
        return Time(time_str, format='isot', scale='utc').isot        
    except ValueError:
        print(f"\nERROR: Invalid time format '{time_str}'. Expected format: YYYY-MM-DDTHH:MM:SS.sss")
        exit(1)

def parse_arguments():
    parser = argparse.ArgumentParser(description='Generating TypeI spectra from event data')
    parser.add_argument('--mode', type=str, choices=['CDTE1', 'CDTE2', 'CZT1', 'CZT2', 'CDTE_TOTAL', 'CZT_TOTAL'], required=True, help='Choose CDTE1, CDTE2, CZT1, CZT2, or CDTE_TOTAL, CZT_TOTAL for combined light curve of both detectors.')
    return parser.parse_args()


def filter_events(events, mjd_start, mjd_end):
    time_mjd = events['mjd']
    mask = (time_mjd >= mjd_start) & (time_mjd <= mjd_end)
    return events[mask]
#==================================================
def Create_spectrum(Start,End):
    args = parse_arguments()
    # Validate and correct time format
    start_time = validate_time_format(Start)
    date = start_time.split("T")[0]
    end_time = validate_time_format(End)    
    # Load FITS file
    hdul = fits.open('evt.fits')
    # Select the appropriate extension
    if args.mode == 'CDTE1':
        events = hdul[1].data  # CDTE1 events
    elif args.mode == 'CDTE2':
        events = hdul[2].data  # CDTE2 events
    #History; Kiran, Dec 03,2025 included CZT events    
    elif args.mode == 'CZT1':
        events = hdul[3].data  # CZT1 events
    elif args.mode == 'CZT2':
        events = hdul[4].data  # CZT2 events
    elif args.mode == 'CDTE_TOTAL':
        events_cdte1 = hdul[1].data
        events_cdte2 = hdul[2].data
        events = np.concatenate([events_cdte1, events_cdte2])     
    elif args.mode == 'CZT_TOTAL':
        events_czt1 = hdul[3].data
        events_czt2 = hdul[4].data
        events = np.concatenate([events_czt1, events_czt2])
    else:
        raise ValueError("Invalid selection. Choose any of these CDTE1, CDTE2,  CZT1, CZT2, CDTE_TOTAL or CZT_TOTAL")
    # Convert user input to MJD using Astropy
    mjd_start = Time(start_time, format='isot', scale='utc').mjd
    mjd_end = Time(end_time, format='isot', scale='utc').mjd
    # Use the existing MJD column for filtering
    events_filtered = filter_events(events, mjd_start, mjd_end)
    energies = events_filtered['ener']
    if args.mode in ('CDTE1', 'CDTE2', 'CDTE_TOTAL'):
        e0 = 1.9340889076913443
        de = 0.1723735860549766
        nbins = 511
    else:
        e0 = 8.26834831480671
        de = 0.4151411242631124
        nbins = 341
    # ---- FIX: integer-based bin construction ----
    bin_edges = e0 + np.arange(nbins + 1) * de

    # Filter energies to valid range
    mask = (energies >= bin_edges[0]) & (energies < bin_edges[-1])
    energies_filtered = energies[mask]
    Counts = []
    # Iterate over each bin
    for i in range(len(bin_edges) - 1):
        # Get the indices of the X values that fall within this bin
        bin_mask = (energies_filtered >= bin_edges[i]) & (energies_filtered < bin_edges[i + 1])
        # Count how many x_filtered val/home/kiran/15dec2023-reconnectionrates/hls/spectra/TypeIues fall within this bin
        count = len(energies_filtered[bin_mask])
        # Append the count to the list
        Counts.append(count)
    Channels = np.arange(0, len(Counts))
    start_time = pd.to_datetime(start_time)
    end_time = pd.to_datetime(end_time)
    dif = end_time - start_time
    dif_sec = dif.total_seconds()

    stat_err = np.sqrt(Counts)
    if args.mode  == 'CDTE1' or args.mode == 'CDTE2' or args.mode == 'CDTE_TOTAL':
        ancrfile = 'hel1os_cdte_arf_v03.fits'
        respfile = 'hel1os_cdte_srf_v04.fits'
        detname = 'CDTE'
        #backfile = 'cdte_typeI_background_pha.fits'
    else:
        ancrfile = 'hel1os_czt_arf_v03.fits'
        respfile = 'hel1os_czt_srf_v04.fits'
        detname = 'CZT'
        #backfile = 'czt_typeI_background_pha.fits'
    # Extract time strings for filename/home/kiran/15dec2023-reconnectionrates/hls/spectra/TypeIs
    start_time_str = start_time.strftime("%H%M%S")
    end_time_str = end_time.strftime("%H%M%S")
    file_name = f"{args.mode}_typeI_spectra_{start_time_str}_{end_time_str}.fits"

    # Create new PHA file
    cols = [
        fits.Column(name='CHANNEL', format='J', array=np.arange(len(Counts))),
        fits.Column(name='COUNTS', format='J', array=Counts),
        fits.Column(name='STAT_ERR', format='E', array=stat_err),
    ]
    pha_hdu = fits.BinTableHDU.from_columns(fits.ColDefs(cols))
    #history:kkk Feb04,2026
    #--------------------------------------------------------------
    if args.mode  == 'CDTE_TOTAL':
        areascal = 2.0
    if args.mode  == 'CZT_TOTAL':
        areascal = 1.7421875
    if args.mode  == 'CDTE1' or args.mode == 'CDTE2':
        areascal = 1.0
    if args.mode  == 'CZT2':
        areascal = 0.92578125
    if args.mode  == 'CZT1':
        areascal = 0.81640625
    #-------------------------------------------------------------    
    # Update headers
    headers = {
            'EXTNAME': 'SPECTRUM',
            'TELESCOP': 'ADITYA-L1',
            'INSTRUME': 'HEL1OS',
            'RESPFILE': respfile,
            'ANCRFILE': ancrfile,
            'BACKFILE': 'none',
            'CORRFILE': 'none',
            'CORRSCAL': 0.0,
            'AREASCAL': areascal,
            'BACKSCAL': 1.0,
            'HDUCLASS': 'OGIP',
            'HDUCLAS1': 'SPECTRUM',
            'HDUCLAS2': 'TYPE:I',
            'HDUVERS' : '1.2.1',
            'POISSERR': False,
            'CHANTYPE': 'PI',
            'DETNAM':detname,
            'DETCHANS': len(Counts),
            'TLMIN': 0,
            'TLMAX': len(Counts) - 1,
            'EXPOSURE': dif_sec,
            'DATE_OBS': start_time.strftime("%Y-%m-%d"),
            'TIME_OBS': start_time.strftime("%H:%M:%S.%f"),
            'DATE_END': end_time.strftime("%Y-%m-%d"),
            'TIME_END': end_time.strftime("%H:%M:%S.%f"),
            }
    try:
        for key, value in headers.items():
            pha_hdu.header[key] = value
    except Exception as e:
        print(f"Error updating headers: {e}")
    pha_hdu.writeto(file_name, overwrite=True)
    print(f"Generated {file_name}")
    # Verify written headers
    """with fits.open(file_name) as hdul:
        print(f"Headers in generated file {file_name}:")
        print(hdul['SPECTRUM'].header)"""

def main_function():
    Date = input("Enter date (yyyymmdd): ").strip()
    stime = input("Enter start time (hhmmss): ").strip()
    etime = input("Enter end time (hhmmss): ").strip()
    Stime = f"{Date[:4]}-{Date[4:6]}-{Date[6:8]}T{stime[:2]}:{stime[2:4]}:{stime[4:6]}.000"
    Etime = f"{Date[:4]}-{Date[4:6]}-{Date[6:8]}T{etime[:2]}:{etime[2:4]}:{etime[4:6]}.000"
    global_start = pd.to_datetime(validate_time_format(Stime))    
    global_end =  pd.to_datetime(validate_time_format(Etime))

    if global_start >= global_end:
        print("Start time must be earlier than end time.")
        return
    cadence = int(input("Enter fixed time interval for spectrum generation (in seconds): "))
    if cadence <= 0:
        print("Cadence must be a positive integer.")
        return
    current_start = global_start
    while current_start < global_end:
        current_end = current_start + pd.Timedelta(seconds=cadence)
        if current_end > global_end:
            current_end = global_end
        st = current_start.strftime("%H%M%S")
        et = current_end.strftime("%H%M%S")
        START = f"{Date[:4]}-{Date[4:6]}-{Date[6:8]}T{st[:2]}:{st[2:4]}:{st[4:6]}.000"
        END = f"{Date[:4]}-{Date[4:6]}-{Date[6:8]}T{et[:2]}:{et[2:4]}:{et[4:6]}.000"
        Create_spectrum(START,END)
        # 🔹 IMPORTANT: Update current_start
        current_start = current_end

if __name__ == "__main__":
    main_function()

#==================================================================
