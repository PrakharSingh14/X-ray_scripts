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
import warnings

# Global variables for synchronization
selected_times = {"start_time": None, "end_time": None}
axes_synced = []  # Stores the axes of the subplots
previous_times = []  # Store previously selected start and end times
colors = cycle(["red", "green", "orange", "purple", "black", "cyan", "magenta"])  # Predefined colors for selections
current_color = next(colors)
plot_window = None
binding_id = None
start_line = None
end_line = None
click_tracker = {"zoom_ignore": True, "left_click_count": 0}

#----------------------------------------------------------------------------------------
def select_files():
    """Open file dialog to select two FITS files."""
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    file1 = filedialog.askopenfilename(title="Select the first FITS file (cdte)")
    file2 = filedialog.askopenfilename(title="Select the second FITS file (czt)")
    return file1, file2

#----------------------------------------------------------------------------------------
def on_click(event):
    """Handle mouse clicks for selecting time ranges."""
    global current_color

    if event.inaxes:  # Ensure the click is within a subplot
        x_data = event.xdata

        if event.button == 1:  # Left click for start time
            click_tracker["left_click_count"] += 1

            if click_tracker["zoom_ignore"] and click_tracker["left_click_count"] == 1:
                print("  ")
                print("First left-click on the plot is for zooming.")
                print("Please select the Start time (left-click on the plot).")
                return

            if selected_times["start_time"] is None:
                #History: Kiran Dec 03,2025, To enable user to change the start time
                #--------------------------------------------------------------------------
                for ax in axes_synced:
                    for line in ax.lines:
                        if line.get_label() == "Start Time":
                            line.remove()
                #--------------------------------------------------------------------------
                selected_times["start_time"] = num2date(x_data).strftime("%Y-%m-%d %H:%M:%S.%f")
                print("")
                print(f"Start time selected: {selected_times['start_time']}.")
                # Draw the new dotted line and store the reference to it
                for ax in axes_synced:
                    ax.axvline(x=x_data, color=current_color, linestyle="dotted", label="Start Time")
                plt.draw()
                plt.pause(0.01)
                #History: kiran Dec 03,2025, To enable user to confim the start time or not
                #---------------------------------------------------------------------------
                print("Would you like to confirm the Start time? [y/n].")
                response = input().strip().lower()
                if response == "y":
                    print("")
                    print("Please select the End time (Right-click on the plot)")
                    selected_times["start_time"] = num2date(x_data).strftime("%Y-%m-%d %H:%M:%S.%f")
                elif response == "n":
                    print("You can left-click again to choose a new Start time.")
                    selected_times["start_time"] = None
                else:
                    print("please type yes or no.")
                #--------------------------------------------------------------------------
        elif event.button == 3:  # Right click for end time
            if selected_times["start_time"] is None:
                print("Please select a Start time (left-click on the plot).")
            else:
                #History: Kiran Dec 03,2025, To enable user to change the end time
                #--------------------------------------------------------------------------
                for ax in axes_synced:
                    for line in ax.lines:
                        if line.get_label() == 'End Time':
                            line.remove()
                #--------------------------------------------------------------------------
                selected_times["end_time"] = num2date(x_data).strftime("%Y-%m-%d %H:%M:%S.%f")
                print(f"End time selected: {selected_times['end_time']}.")
                # Draw the new dashed line and store the reference to it
                for ax in axes_synced:
                    ax.axvline(x=x_data, color=current_color, linestyle="dashed", label="End Time")                         
                plt.draw()
                plt.pause(0.01) #History: kiran Dec 03,2025, This will ensure the dashed line will appear immediately with right click 
                #History: kiran Dec 03,2025, To enable user to confirm the end time or not
                #----------------------------------------------------------------------
                print("Would you like to confirm the End time? [y/n].")
                response = input().strip().lower()
                if response == "y":
                   prompt_user_for_confirmation()
                elif response == "n":
                    print("You can right-click again to choose a new End time.")
                    selected_times["end_time"] is None
                else:
                    print("Please type 'y' or 'n'.")
                #-----------------------------------------------------------------------    
#----------------------------------------------------------------------------------------
def prompt_user_for_confirmation():
    """Prompt the user to confirm their selection."""
    global previous_times, current_color

    # Generate files and print their names
    filter_and_process_files()
    print("Start and End times are adjusted to data boundaries of Type II files")
    print(" ")
    print("Would you like to generate another Type-I file with a new time range? [y/n].")
    response = input().strip().lower()

    if response == "y":
        previous_times.append((selected_times["start_time"], selected_times["end_time"], current_color))
        current_color = next(colors)  # Change to the next color for the new selection
        retain_plot_with_context()
    elif response == "n":
        print("Exiting the process.")
        plt.close()
    else:
        print("Invalid response. Please type 'y' or 'n'.")
        prompt_user_for_confirmation()
#---------------------------------------------------------------------------------------------
def retain_plot_with_context():
    """Retain the current plot and add previous selections for context."""
    global selected_times

    # Plot previous selections as vertical lines in all subplots
    for start, end, color in previous_times:
        start_time_num = pd.to_datetime(start).to_pydatetime()
        end_time_num = pd.to_datetime(end).to_pydatetime()
        for ax in axes_synced:
            ax.axvline(start_time_num, color=color, linestyle="dotted", label="Previous Start")
            ax.axvline(end_time_num, color=color, linestyle="dashed", label="Previous End")

    # Reset current selection
    selected_times["start_time"] = None
    selected_times["end_time"] = None

    # Redraw the plot
    plt.gcf().canvas.mpl_connect('button_press_event', on_click)
    plt.show()

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

            # Find rows within the selected time range
            #===========================================================================================================
            #HISTORY Dec26-2025 Kiran (make sure rows are selected near data boundaries)
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
                respfile = 'hel1os_czt_srf_v04.fits'  #History Kiran Dec 03,2035, changing from V03 to V04 
                DETNAME = 'CZT'
                #backfile = 'czt_typeI_background_pha.fits' #History: Kiran Dec 03,2025

            # Extract time strings for filenames
            #HISTORY Kiran Dec26-2025 (naming files with ture times)
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
            file_name = f"{detname}_typeI_spectra_{start_time_str}_{end_time_str}.fits"
            #=================================================================================================

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
                    'TIME_OBS': start_time.strftime("%H:%M:%S.%f"),
                    'DATE_END': end_time.strftime("%Y-%m-%d"),
                    'TIME_END': end_time.strftime("%H:%M:%S.%f"),
                    'TSTART': float(tstart[start_row]),
                    'TSTOP': float(tstop[end_row]),
                    }

            try:
                for key, value in headers.items():
                    pha_hdu.header[key] = value
            except Exception as e:
                print(f"Error updating headers: {e}")

            pha_hdu.writeto(file_name, overwrite=False)
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
    global plot_window, binding_id

    fig, axes = plt.subplots(2, 1,figsize = (8,5) ,sharex=True, dpi = 150)

    # Plot CdTe data
    axes[0].plot(cdte_df['Time'], cdte_df['Counts'], label="CdTe")
    axes[0].set_title("CdTe Lightcurve", fontsize = '15')
    axes[0].set_ylabel("Counts", fontsize = '12')
    axes[0].set_yscale("log")
    axes[0].legend()

    # Plot CZT data
    axes[1].plot(czt_df['Time'], czt_df['Counts'], label="CZT")
    axes[1].set_title("CZT Lightcurve", fontsize = '15')
    axes[1].set_ylabel("Counts", fontsize = '12')
    axes[1].set_yscale("log")
    axes[1].set_xlabel("Time", fontsize = '12')
    axes[1].legend()

    # Apply date formatter
    for ax in axes:
        Time = DateFormatter("%H:%M:%S")
        ax.xaxis.set_major_formatter(Time)
        axes_synced.append(ax)
    date = cdte_df['Time'][0].strftime('%Y-%m-%d')  
    # Connect zoom synchronization
    plot_window = plt.gcf()
    binding_id = plt.gcf().canvas.mpl_connect('button_press_event', on_click)
    plt.text(0, -0.15, f'{date:}',transform=plt.gca().transAxes,fontsize=12,verticalalignment='top')
    plt.tight_layout()
    print("")
    print("Ignore libGL error, left click anywhere on the plot")
    print("")
    plt.show()


#----------------------------------------------------------------------------------------
# Main execution logic
if __name__ == "__main__":
    # Select files
    fits1_path, fits2_path = select_files()

    # Load data
    cdte_df = load_time_profile(fits1_path)
    czt_df = load_time_profile(fits2_path)

    # Plot lightcurves
    plot_lightcurves(cdte_df, czt_df)
    


