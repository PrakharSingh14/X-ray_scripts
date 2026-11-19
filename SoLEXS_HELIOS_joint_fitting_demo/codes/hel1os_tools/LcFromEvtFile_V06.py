"""
#this codes takes "evt.fits" file as input and as a output it will generate the user defined light curves and simultaneously these light curves will be displayed and saved as .csv file for later use

# User need to give following inputs in a COMMAND LINE:
    1. mode
       User should select any of these CDTE1,CDTE2, CZT1, CZT2, CDTE_TOTAL or CZT_TOTAL, each indicates either individual detector or combined detector
       eg: "mode CZT1" will give light curve of CZT1 detector only
           "mode CZT_TOTAL" will give combined light curve from both CZT detectors

    2. start_time
       User should give desired start time in format (yyyy-mm-ddThh:mm:ss.sss). It defines from which light curve will start and should be between the event file time period (12hrs)
       eg: "start_time 2025-10-15T13:00:00.000"
       
    3. end_time
       User should give desired end time in format (yyyy-mm-ddThh:mm:ss.sss). It defines where light curve ends and should be between the event file time period (12hrs)
       eg: "end_time 2025-10-15T14:30:00.000"

    4. time_bin_size
       User should give desired time bin size in seconds , it will define the cadence of the light curve
       eg: "time_bin_size 10"

    5. output file 
       User can give the desired name for the output file or light curve will saved in default file name "binned_lightcurve.csv".
       eg: "LightCurve.csv"

example COMMAND LINE with all above inputs is given below:    
"python LcFromEvtFile.py 2>/dev/null --fits_file evt.fits --mode CZT1 --start_time 2025-10-15T13:00:00.000 --end_time 2025-10-15T14:30:00.000 --time_bin_size 10 --output LightCurve.csv"

After running command line a prompt will appear as shown below:

CDTE FULL ENERGY RANGE 5 - 90 keV, CZT FULL ENERGY RANGE 20 - 200 keV
USER SHOULD ENTER 1 or 2
   
1. LIGHT CURVES WITH USER DEFINED ENERGY RANGE(S)
   User will be asked to:
   Enter Emin and Emax in keV (Seperated by space):= (For example: 30 90)
   Note: user can give multiple energy ranges by following the prompt(Would you like to generate another energy bin? [y/n])
   
2. LIGHT CURVES WITH USER DEFINED FIXED ENERGY BIN SIZE FOR FULL ENERGY RANGE
   User will be asked to:
   Enter desired energy bin size in keV (for example: 20)
   As a output, light curves will be in the following energy bins
   For CZT : 20 - 40, 40 - 60, 60 - 80,.. upto 200 keV
   For CdTe :5  - 25, 25 - 45, 45 - 65,.. upto 90 keV
   Note: MAX 10 energy bins light curves will be displayed, However, all bins data is stored in .csv file

ENTER 1 or 2 :

"""
# Importing required libraries
import numpy as np
import pandas as pd
import argparse
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.dates as mdates
from astropy.io import fits
from astropy.time import Time

# Function to validate and fix time format - check in place to make sure that the user enters the correct time format. 
def validate_time_format(time_str):
    try:
        return Time(time_str, format='isot', scale='utc').isot
    except ValueError:
        print(f"\nERROR: Invalid time format '{time_str}'. Expected format: YYYY-MM-DDTHH:MM:SS.sss")
        exit(1)

# Function to filter events within the flare time range 
def filter_events(events, mjd_start, mjd_end):
    time_mjd = events['mjd']
    mask = (time_mjd >= mjd_start) & (time_mjd <= mjd_end) 
    return events[mask]


# Function to bin CdTe events into user-defined time intervals - this is in units of seconds. 
def bin_events(time_mjd, ener, time_bin_size, energy_bins):
    args = parse_arguments()
    mjd_start = np.min(time_mjd)
    time_seconds = (time_mjd - mjd_start) * 86400  # Convert MJD to seconds
    num_bins = int(np.ceil((np.max(time_seconds) - np.min(time_seconds)) / time_bin_size))
    time_bins = np.arange(0, num_bins * time_bin_size, time_bin_size)
    time_bin_indices = np.digitize(time_seconds, time_bins) - 1
    spectra = []
    timestamps = []
    for i in range(len(time_bins) - 1):
        time_mask = (time_bin_indices == i)
        ener_in_bin = ener[time_mask]
        if args.mode  == 'CDTE1' or args.mode == 'CDTE2' or args.mode == 'CDTE_TOTAL':
            ener_in_bin = ener_in_bin[ener_in_bin >= 5]  # Filter out energies < 5 keV
        #History: Kiran, Dec 03,2025, added else condition to include CZT dtectors
        else:
            ener_in_bin = ener_in_bin[ener_in_bin >= 20]  # Filter out energies < 20 keV
        counts, _ = np.histogram(ener_in_bin, bins=energy_bins)
        spectra.append(counts)
        timestamps.append(Time(mjd_start + time_bins[i] / 86400, format='mjd').isot)
    return spectra, timestamps

# Argument parser - what does this do? This allows the user to provide inputs at the command prompt! Please make sure that the arguments are passed correctly and in order. 
def parse_arguments():
    parser = argparse.ArgumentParser(description='Time and energy binning of FITS event data.')
    parser.add_argument('--fits_file', type=str, required=True, help='Input FITS event file.')
    #History: Kiran, Dec 03,2025, modifed below parser to include CZT detector  
    parser.add_argument('--mode', type=str, choices=['CDTE1', 'CDTE2', 'CZT1', 'CZT2', 'CDTE_TOTAL', 'CZT_TOTAL'], required=True, help='Choose CDTE1, CDTE2, CZT1, CZT2, or CDTE_TOTAL, CZT_TOTAL for combined light curve of both detectors.')

    parser.add_argument('--start_time', type=str, required=True, help='Start time in UTC (e.g., 2024-09-12T00:00:02.801).')
    parser.add_argument('--end_time', type=str, required=True, help='End time in UTC (e.g., 2024-09-12T00:05:00.000).')
    parser.add_argument('--time_bin_size', type=float, required=True, help='Time bin size in seconds.')
    #History: Kiran, Dec 03,2025,commented below parser argument
    #parser.add_argument('--energy_bin_size', type=float, required=True, help='Energy bin size in keV.')
    parser.add_argument('--output', type=str, default='binned_lightcurve.csv', help='Output CSV filename.')
    return parser.parse_args()

# Main function
def main():
    args = parse_arguments()
    
    # Validate and correct time format
    start_time = validate_time_format(args.start_time)
    date = start_time.split("T")[0]
    end_time = validate_time_format(args.end_time)
    
    # Load FITS file
    hdul = fits.open(args.fits_file)
    
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
    #History: Kiran, Dec 03,2025 , added option for user deifned energy range light curve    
    print("  ")
    print("CDTE FULL ENERGY RANGE 5 - 90 keV, CZT FULL ENERGY RANGE 20 - 200 keV")
    print("USER SHOULD ENTER 1 or 2")
    print("   ")
    print("1. LIGHT CURVES WITH USER DEFINED ENERGY RANGE(S)")
    print("   User will be asked to:")
    print("   Enter Emin and Emax in keV (Seperated by space):= (For example: 30 90)")
    print("   Note: user can give multiple energy ranges by following the prompt(Would you like to generate another energy bin? [y/n])") 
    print("   ")
    print("2. LIGHT CURVES WITH USER DEFINED FIXED ENERGY BIN SIZE FOR FULL ENERGY RANGE")
    print("   User will be asked to:")
    print("   Enter desired energy bin size in keV (for example: 20)")
    print("   As a output, light curves will be in the following energy bins")
    print("   For CZT : 20 - 40, 40 - 60, 60 - 80,.. upto 200 keV")
    print("   For CdTe :5  - 25, 25 - 45, 45 - 65,.. upto 90 keV")
    print("   Note: MAX 10 energy bins light curves will be displayed, However, all bins data is stored in .csv file")
    print("   ")
    option = input("ENTER 1 or 2 : ")
    if option == '1':
    # option 1 logic
        Emin, Emax = map(float,input("Enter Emin and Emax in keV (Seperated by space): ").split())
        energy_bins = np.arange(Emin, Emax + 1, Emax - Emin)
        spectra, timestamps = bin_events(events_filtered['mjd'], events_filtered['ener'], args.time_bin_size, energy_bins)
        csv_data = pd.DataFrame(spectra, columns=[f'{energy_bins[i]:.2f}-{energy_bins[i+1]:.2f} keV' for i in range(len(energy_bins) - 1)])
        csv_data.insert(0, 'Time (UTC)', timestamps)
        csv_data['Time (UTC)'] = pd.to_datetime(csv_data['Time (UTC)'])
        csv_data.set_index('Time (UTC)', inplace=True)
        print("Would you like to generate another energy bin? [y/n]")
        response = input().strip().lower()
        while response == 'y':
            New_Emin, New_Emax = map(float, input("Enter new Emin and Emax in keV (Seperated by space): ").split())
            energy_bins = np.arange(New_Emin, New_Emax + 1, New_Emax - New_Emin)
            spectra, timestamps = bin_events(events_filtered['mjd'], events_filtered['ener'], args.time_bin_size, energy_bins)
        
            # Create new dataframe for the new energy bins
            df = pd.DataFrame(spectra, columns=[f'{energy_bins[i]:.2f}-{energy_bins[i+1]:.2f} keV' for i in range(len(energy_bins) - 1)])
            df.insert(0, 'Time (UTC)', timestamps)
            df['Time (UTC)'] = pd.to_datetime(df['Time (UTC)'])
            df.set_index('Time (UTC)', inplace=True)
        
            # Append new data to the existing dataframe
            csv_data = pd.concat([csv_data, df.iloc[:, 0]], axis=1)
        
            print("Would you like to generate another energy bin? [y/n]")
            response = input().strip().lower()

        if response == 'n':
            print("Given Energy bins taken")
        else:
            print("Invalid response. Please type 'y' or 'n'.")
    elif option == '2':
        # option 2 logic
        energy_bin_size = float(input("Enter desired energy bin size in keV: "))
        if args.mode == 'CDTE1' or args.mode == 'CDTE2' or args.mode == 'CDTE_TOTAL':
            energy_bins = np.arange(5, 91, energy_bin_size)
        else:
            energy_bins = np.arange(20, 201, energy_bin_size)
        spectra, timestamps = bin_events(events_filtered['mjd'], events_filtered['ener'], args.time_bin_size, energy_bins)
        csv_data = pd.DataFrame(spectra, columns=[f'{energy_bins[i]:.2f}-{energy_bins[i+1]:.2f} keV' for i in range(len(energy_bins) - 1)])
        csv_data.insert(0, 'Time (UTC)', timestamps)
        csv_data['Time (UTC)'] = pd.to_datetime(csv_data['Time (UTC)'])
        csv_data.set_index('Time (UTC)', inplace=True)
    else:
        print("Invalid selection. Please choose either '1' or '2'.")           
    

    csv_data.to_csv(args.output)    
    print(f"CSV file saved as '{args.output}'")
    print(" ")
    
    # Plot first 10 energy bins
    plt.figure(figsize=(10, 6),  dpi = 150)
    for col in csv_data.columns[:10]:
        plt.step(csv_data.index, csv_data[col], label=col)
    plt.xlabel("Time (UTC)", fontsize = '15')
    plt.ylabel("Counts", fontsize = '15')
    plt.yscale('log')  # Set y-axis to log scale
    #plt.title(f'Lightcurve with Energy bin {args.energy_bin_size:.0f} keV and Time bin {args.time_bin_size:.0f} sec', fontsize = '18')
    plt.title(f'Lightcurve with {args.time_bin_size:.0f} sec binning', fontsize = '18')
    plt.text(0, -0.06, f'{date:}',transform=plt.gca().transAxes,fontsize=10,verticalalignment='top')
    plt.legend()
    #plt.xticks(rotation=45)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.savefig('ligthcurve.png', dpi = 150)
    plt.show()

if __name__ == "__main__":
    main()

