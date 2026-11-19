# Jan 04, 2025
# Code to generate multiple typeI files depending upon the time range selected for analysis
#edited file backfile
import tkinter as tk
from tkinter import filedialog
import pandas as pd
import numpy as np
from itertools import cycle
from astropy.io import fits
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, num2date
from datetime import datetime, timedelta
from itertools import cycle


#----------------------------------------
selected_times = {"start_time": None, "end_time": None}
axes_synced = []  # Stores axes of subplots
previous_times = []  # Store previously selected start and end times
colors = cycle(["red", "green", "orange", "purple", "black", "cyan", "magenta"])  # Predefined colors
current_color = next(colors)
#----------------------------------------
def select_files():
    """Open file dialog to select two FITS files."""
    root = tk.Tk()
    root.withdraw()
    file1 = filedialog.askopenfilename(title="Select the first FITS file (cdte)")
    file2 = filedialog.askopenfilename(title="Select the second FITS file (czt)")
    return file1, file2

#----------------------------------------
def plot_selection(start_time, end_time, color, label_prefix="Current"):
    """Plot vertical lines for start and end times in all subplots."""
    for ax in axes_synced:
        ax.axvline(start_time, color=color, linestyle="dotted", label=f"{label_prefix} Start")
        ax.axvline(end_time, color=color, linestyle="dashed", label=f"{label_prefix} End")
    plt.draw()
    plt.pause(0.01)

def retain_previous_selections():
    """Plot all previous selections with their colors."""
    for start, end, color in previous_times:
        plot_selection(start, end, color, label_prefix="Previous")

def get_time_input():
    date = input("Enter date (yyyymmdd): ").strip()
    stime = input("Enter start time (hhmmss): ").strip()
    etime = input("Enter end time (hhmmss): ").strip()
    stime = f"{date}T{stime[:2]}:{stime[2:4]}:{stime[4:6]}"
    etime = f"{date}T{etime[:2]}:{etime[2:4]}:{etime[4:6]}"
    stime_dt = pd.to_datetime(stime).to_pydatetime()
    etime_dt = pd.to_datetime(etime).to_pydatetime()
    return stime_dt, etime_dt

def Loop_function():
    global selected_times, current_color

    while True:
        # Get user input
        selected_times["start_time"], selected_times["end_time"] = get_time_input()
        
        # Plot current selection
        retain_previous_selections()
        plot_selection(selected_times["start_time"], selected_times["end_time"], current_color)

        # Call your file processing function here
        filter_and_process_files()  # Uncomment and define if needed
        
        # Save current selection to previous list
        previous_times.append((selected_times["start_time"], selected_times["end_time"], current_color))
        current_color = next(colors)

        # Ask user if they want to select another time range
        while True:
            response = input("Would you like to select another time range? [y/n]: ").strip().lower()
            if response == "y":
                break  # Loop will repeat
            elif response == "n":
                print("Exiting the process.")
                plt.close()
                return
            else:
                print("Invalid response. Please type 'y' or 'n'.")

#----------------------------------------------------------------------------------------
def filter_and_process_files():
    """Filter the rows in both FITS files and generate Type I PHA files."""
    start_time = pd.to_datetime(selected_times["start_time"])
    end_time = pd.to_datetime(selected_times["end_time"])

    for fits_file, output_name in zip([fits1_path, fits2_path], ["cdte", "czt"]):
        with fits.open(fits_file) as hdul:
            spectrum_data = hdul['SPECTRUM'].data
            header = hdul['SPECTRUM'].header
            areascal = hdul['SPECTRUM'].header['AREASCAL'] #history:kkk Feb04,2026
            tstart = spectrum_data['TSTART']
            tstop = spectrum_data['TSTOP']

            # Convert start and end times to seconds
            start_time_seconds = (start_time - pd.to_datetime(header['DATE_OBS'] + ' ' + header['TIME_OBS'])).total_seconds()
            end_time_seconds = (end_time - pd.to_datetime(header['DATE_OBS'] + ' ' + header['TIME_OBS'])).total_seconds()
            bin_size = tstop[0] - tstart[0]
            start_row = int(np.round(start_time_seconds / bin_size))
            end_row   = int(np.round(end_time_seconds / bin_size))
            # Sum the counts over the selected rows
            summed_counts = np.sum(spectrum_data['COUNTS'][start_row:end_row + 1], axis=0)
            summed_stat_err = np.sqrt(np.sum(spectrum_data['STAT_ERR'][start_row:end_row + 1]**2, axis=0))
            summed_exposure = np.sum(spectrum_data['EXPOSURE'][start_row:end_row])

            #Set ANCRFILE and RESPFILE based on the file type
            if output_name == "cdte":
                ancrfile = 'hel1os_cdte_arf_v03.fits'
                respfile = 'hel1os_cdte_srf_v04.fits' #History Kiran Dec 03,2025, changing from V03 to V04 
                DETNAME = 'CDTE'
                #backfile = 'cdte_typeI_background_pha.fits' #History: Kiran Dec 03,2025 removing the background file
            elif output_name == "czt":
                ancrfile = 'hel1os_czt_arf_v03.fits'
                respfile = 'hel1os_czt_srf_v04.fits'#History Kiran Dec 03,2035, changing from V03 to V04 
                DETNAME = 'CZT'
                #backfile = 'czt_typeI_background_pha.fits' #History: Kiran Dec 03,2025

            # Extract time strings for filenames
            #=================================================================================================
            Adjusted_start_time_seconds = tstart[start_row] 
            Adjusted_end_time_seconds = tstop[end_row-1]
            time_obs_str = header['TIME_OBS']  # Example: '12:00:00'
            time_obs = pd.to_datetime(time_obs_str, format='%H:%M:%S.%f')
            time_obs = time_obs.floor('S')
            start_time_delta = timedelta(seconds=Adjusted_start_time_seconds)
            end_time_delta = timedelta(seconds=Adjusted_end_time_seconds)

            # Add the timedelta to the observation time (time_obs) to get the correct times
            Adjusted_start_time = time_obs + start_time_delta
            Adjusted_end_time = time_obs + end_time_delta
            start_time_str = Adjusted_start_time.strftime("%H%M%S")  # E.g., "120045" for 12:00:45
            end_time_str =  Adjusted_end_time.strftime("%H%M%S")  # E.g., "120100" for 12:01:00
            detname = hdul['SPECTRUM'].header['DETNAM']
            #=================================================================================================
            file_name = f"{detname}_typeI_spectra_{start_time_str}_{end_time_str}.fits"

            # Create new PHA file
            cols = [
                fits.Column(name='CHANNEL', format='J', array=np.arange(len(summed_counts))+1),
                fits.Column(name='COUNTS', format='J', array=summed_counts),
                fits.Column(name='STAT_ERR', format='E', array=summed_stat_err),
            ]
            pha_hdu = fits.BinTableHDU.from_columns(fits.ColDefs(cols))

            # Update headers
            headers = {
                    'EXTNAME': 'SPECTRUM',
                    'TELESCOP': 'ADITYA-L1',
                    'INSTRUME': 'HEL1OS',
                    'RESPFILE': respfile,
                    'ANCRFILE': ancrfile,
                    'BACKFILE': 'none', #backfile, #History: Kiran Dec 03,2025
                    'CORRFILE': 'none',
                    'CORRSCAL': 0.0,
                    'AREASCAL': areascal, #history:kkk Feb04,2026
                    'BACKSCAL': 1.0,
                    'HDUCLASS': 'OGIP',
                    'HDUCLAS1': 'SPECTRUM',
                    'HDUCLAS2': 'TYPE:I',
                    'HDUVERS' : '1.2.1',
                    'POISSERR': False,
                    'CHANTYPE': 'PI',
                    'DETNAM': DETNAME,
                    'DETCHANS': len(summed_counts),
                    'TLMIN': 1,
                    'TLMAX': len(summed_counts),
                    'EXPOSURE': summed_exposure,
                    'DATE_OBS': start_time.strftime("%Y-%m-%d"),
                    'TIME_OBS': Adjusted_start_time.strftime("%H:%M:%S.%f"),
                    'DATE_END': end_time.strftime("%Y-%m-%d"),
                    'TIME_END': Adjusted_end_time.strftime("%H:%M:%S.%f"),
                    'TSTART': float(tstart[start_row]),
                    'TSTOP': float(tstop[end_row]),
                    }

            try:
                for key, value in headers.items():
                    pha_hdu.header[key] = value
            except Exception as e:
                print(f"Error updating headers: {e}")

            pha_hdu.writeto(file_name, overwrite=True)
            print(f"TypeI file Generated: {file_name}")

            # Verify written headers
            """with fits.open(file_name) as hdul:
                print(f"Headers in generated file {file_name}:")
                print(hdul['SPECTRUM'].header)"""

#----------------------------------------------------------------------------------------
def load_time_profile(fits_file):
    with fits.open(fits_file) as hdul:
        spectrum_data = hdul['SPECTRUM'].data
        tstart = spectrum_data['TSTART']
        tstop = spectrum_data['TSTOP']
        counts = np.sum(spectrum_data['COUNTS'], axis=1)

        # Generate a timeline based on the midpoint of tstart and tstop
        time_midpoints = tstart + (tstop - tstart) / 2

        header = hdul['SPECTRUM'].header
        base_time = pd.to_datetime(header['DATE_OBS'] + ' ' + header['TIME_OBS'])
        times = [base_time + pd.to_timedelta(tm, unit='s') for tm in time_midpoints]

    return pd.DataFrame({"Time": times, "Counts": counts})

#---------------------------------------------------------------------------------------
def plot_lightcurves(cdte_df, czt_df):
    """Plot lightcurves for the provided dataframes."""
    global axes_synced

    fig, axes = plt.subplots(2, 1, figsize=(8,5), sharex=True, dpi=150)

    # Plot CdTe data
    axes[0].plot(cdte_df['Time'], cdte_df['Counts'], label="CdTe")
    axes[0].set_title("CdTe Lightcurve", fontsize=15)
    axes[0].set_ylabel("Counts", fontsize=12)
    axes[0].set_yscale("log")
    axes[0].legend()

    # Plot CZT data
    axes[1].plot(czt_df['Time'], czt_df['Counts'], label="CZT")
    axes[1].set_title("CZT Lightcurve", fontsize=15)
    axes[1].set_ylabel("Counts", fontsize=12)
    axes[1].set_xlabel("Time", fontsize=12)
    axes[1].set_yscale("log")
    axes[1].legend()

    # Apply date formatter and store axes
    for ax in axes:
        ax.xaxis.set_major_formatter(DateFormatter("%H:%M:%S"))
        axes_synced.append(ax)

    date = cdte_df['Time'][0].strftime('%Y-%m-%d')
    plt.text(0, -0.15, f'{date}', transform=plt.gca().transAxes, fontsize=12, verticalalignment='top')
    plt.tight_layout()
    plt.show(block=False)  # Show plot non-blocking so we can enter times
 #----------------------------------------------------------------------------------------
# Main execution
if __name__ == "__main__":
    # Select files
    fits1_path, fits2_path = select_files()
    
    # Load data
    cdte_df = load_time_profile(fits1_path)
    czt_df = load_time_profile(fits2_path)
   
    # Plot lightcurves
    plot_lightcurves(cdte_df, czt_df)

    # Start function
    Loop_function()

    # Keep the final plot open after exiting
    plt.show()

