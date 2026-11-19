#Nov21,2025
#This code will take evt.fits file has input and gives six TypeII spectral files out of which four correspond to spectra of individual detectors (2CdTe and 2CZT) and two correspond to combined spectra of both CdTe and both CZT detectors seperately

#==========================================================================================================================
#importing required libraries
import numpy as np
from astropy.io import fits
from astropy.table import Table
from astropy.time import Time

# Time conversion from MJD to seconds relative to the first event
def mjd_to_seconds(mjd, mjd_start):
    return (mjd - mjd_start) * 86400  # Convert days to seconds

#==========================================================================================================================
#This Function bins the events into fixed time intervals of given time bin size and generates histograms
def fixed_time_binning(time_mjd, ener, time_bin_size, energy_bins):
    # Converting MJD to seconds relative to the start time
    #History Kiran Dec26-2025 (Using minimum time of all detectors events)
    mjd_start = np.min(Concatinated_time)
    time_seconds = mjd_to_seconds(time_mjd, mjd_start)
    
    # Defining time bins (in seconds) for given time bin size intervals
    num_bins = int(np.ceil((np.max(time_seconds) - np.min(time_seconds)) / time_bin_size))
    time_bins = np.arange(0, num_bins * time_bin_size, time_bin_size)
    
    # Digitizing the time into bins
    time_bin_indices = np.digitize(time_seconds, time_bins) - 1
    
    # Creating an empty list to store histograms for each time bin
    spectra = []
    tstart_values = []
    tstop_values = []
    
    for i in range(len(time_bins) - 1):
        # Filtering the events that fall within the current time bin
        time_mask = (time_bin_indices == i)
        ener_in_bin = ener[time_mask]
        
        # Histogram the energy values into the defined energy bins (511 channels for CdTe and 341 channesl for CZT)
        counts, _ = np.histogram(ener_in_bin, bins=energy_bins)
        
        # Storing the histogram as spectra
        spectra.append(counts)
        
        # Calculating TSTART and TSTOP for this time bin
        tstart_values.append(time_bins[i])
        tstop_values.append(time_bins[i] + time_bin_size)
    
    return spectra, tstart_values, tstop_values, mjd_start

#==========================================================================================================================
# Function to create a Type II spectra file for CZT detectors with given time bin size binning
def czt_spectra(events, output_filename, detname):
    # Extracting time and energy from 'TIME' and 'ENER' columns
    time_mjd = events['MJD']
    energy_column = events['ener']
    
    # Defining the time bin size (20-second intervals)
    time_bin_size = 20
    
    # Defining energy binning (341 channels between 8.26834831480671 and 150 keV)
    energy_bins = np.arange(8.26834831480671, 8.26834831480671 + 341 * 0.4151411242631124, 0.4151411242631124)
    
    # Bining events by time and creating histograms for each time bin
    spectra, tstart_values, tstop_values, mjd_start = fixed_time_binning(time_mjd, energy_column, time_bin_size, energy_bins)
    
    # Converting MJD start and end times to DATE-OBS and TIME-OBS, DATE-END and TIME-END
    time_obj_start = Time(mjd_start, format='mjd')
    time_obj_end = Time(np.max(time_mjd), format='mjd')
    date_obs = time_obj_start.utc.strftime('%Y-%m-%d')
    time_obs = time_obj_start.utc.strftime('%H:%M:%S.%f')
    date_end = time_obj_end.utc.strftime('%Y-%m-%d')
    time_end = time_obj_end.utc.strftime('%H:%M:%S.%f')
    
    # Preparing the data for each spectrum (counts, stat_err, exposure, tstart, tstop)
    counts_data = np.array(spectra)  # Shape (number of time bins, 341)
    ener_edges  = np.array(energy_bins)
    stat_err_data = np.sqrt(counts_data)  # Poisson errors as sqrt of counts
    exposure_data = np.full(len(tstart_values), 20.0)  # Constant exposure time of 20 seconds
    spec_num_data = np.arange(len(tstart_values))  # SPEC_NUM as the row number (0, 1, 2, ...)
    channel_data = np.tile(np.arange(341) +1 , (len(tstart_values), 1))  # Array from 1 to 341 repeated for each spectrum
    tstart_data = np.array(tstart_values)
    tstop_data = np.array(tstop_values)
    
    # defining columns in the spectral file
    col_spec_num = fits.Column(name='SPEC_NUM', format='I', array=spec_num_data)
    col_channel = fits.Column(name='CHANNEL', format='341J', array=channel_data)
    col_counts = fits.Column(name='COUNTS', format='341D', array=counts_data)
    col_stat_err = fits.Column(name='STAT_ERR', format='341D', array=stat_err_data)
    col_exposure = fits.Column(name='EXPOSURE', format='D', array=exposure_data)
    col_tstart = fits.Column(name='TSTART', format='D', array=tstart_data)
    col_tstop = fits.Column(name='TSTOP', format='D', array=tstop_data)
    #history: kiran 09feb2026(regarding area scale)
    if detname == 'CZT1':
        areascal = 0.81640625
    if detname == 'CZT2':
        areascal = 0.92578125
    # Defining columns as a ColDefs object
    coldefs = fits.ColDefs([col_spec_num, col_channel, col_counts, col_stat_err, col_exposure, col_tstart, col_tstop])
    
    # Creating the SPECTRUM extension using the ColDefs object
    spectrum_hdu = fits.BinTableHDU.from_columns(coldefs)
    spectrum_hdu.header['TSTART'] = mjd_start
    spectrum_hdu.header['TSTOP'] = np.max(time_mjd)
    spectrum_hdu.header['EXTNAME'] = 'SPECTRUM'
    spectrum_hdu.header['TELESCOP'] = 'ADITYA-L1'
    spectrum_hdu.header['INSTRUME'] = 'HEL1OS'
    spectrum_hdu.header['HDUCLASS'] = 'OGIP'
    spectrum_hdu.header['RESPFILE'] = 'none'
    spectrum_hdu.header['ANCRFILE'] = 'none'    
    spectrum_hdu.header['BACKFILE'] = 'none'
    spectrum_hdu.header['CORRFILE'] = 'none'
    spectrum_hdu.header['BACKSCAL'] = 1.0
    spectrum_hdu.header['AREASCAL'] = areascal
    spectrum_hdu.header['CORRSCAL'] = 0.0
    spectrum_hdu.header['HDUVERS'] = '1.2.1'
    spectrum_hdu.header['TLMIN2'] = 1
    spectrum_hdu.header['TLMAX2'] = 341
    spectrum_hdu.header['CHANTYPE'] = 'PI'
    spectrum_hdu.header['DETCHANS'] = 341
    spectrum_hdu.header['DETNAM'] = detname
    spectrum_hdu.header['DATE_OBS'] = date_obs
    spectrum_hdu.header['TIME_OBS'] = time_obs
    spectrum_hdu.header['DATE_END'] = date_end
    spectrum_hdu.header['TIME_END'] = time_end
    spectrum_hdu.header['FILENAME'] = output_filename

    # Creating the Primary extension (can be left empty)
    primary_hdu = fits.PrimaryHDU()    

    # Writing the FITS file with both Primary and SPECTRUM extensions
    hdul = fits.HDUList([primary_hdu, spectrum_hdu])
    hdul.writeto(output_filename, overwrite=True)

    print(f"Type II spectra created: {output_filename}")

#==========================================================================================================================
# Function to create a Type II spectra file for CdTe detectors with given time bin size binning
def cdte_spectra(events, output_filename, detname):
    # Extracting time and energy from 'TIME' and 'ENER' columns
    time_mjd = events['MJD']
    energy_column = events['ener']
    
    # Defining the time bin size (20-second intervals)
    time_bin_size = 20
    
    # Defining energy binning (511 channels between 1.9340889076913443 and 90 keV)
    energy_bins = np.arange(1.9340889076913443, 1.9340889076913443 + 511 * 0.1723735860549766, 0.1723735860549766)
    
    # Bining events by time and creating histograms for each time bin
    spectra, tstart_values, tstop_values, mjd_start = fixed_time_binning(time_mjd, energy_column, time_bin_size, energy_bins)
    
    # Converting MJD start and end times to DATE-OBS and TIME-OBS, DATE-END and TIME-END
    time_obj_start = Time(mjd_start, format='mjd')
    time_obj_end = Time(np.max(time_mjd), format='mjd')
    date_obs = time_obj_start.utc.strftime('%Y-%m-%d')
    time_obs = time_obj_start.utc.strftime('%H:%M:%S.%f')
    date_end = time_obj_end.utc.strftime('%Y-%m-%d')
    time_end = time_obj_end.utc.strftime('%H:%M:%S.%f')
    
    # Preparing the data for each spectrum (counts, stat_err, exposure, tstart, tstop)
    counts_data = np.array(spectra)  # Shape (number of time bins, 511)
    ener_edges  = np.array(energy_bins)
    stat_err_data = np.sqrt(counts_data)  # Poisson errors as sqrt of counts
    exposure_data = np.full(len(tstart_values), 20.0)  # Constant exposure time of 20 seconds
    spec_num_data = np.arange(len(tstart_values))  # SPEC_NUM as the row number (0, 1, 2, ...)
    channel_data = np.tile(np.arange(511) + 1, (len(tstart_values), 1))  # Array from 1 to 511 repeated for each spectrum
    tstart_data = np.array(tstart_values)
    tstop_data = np.array(tstop_values)
    
    # defining columns in the spectral file
    col_spec_num = fits.Column(name='SPEC_NUM', format='I', array=spec_num_data)
    col_channel = fits.Column(name='CHANNEL', format='511J', array=channel_data)
    col_counts = fits.Column(name='COUNTS', format='511D', array=counts_data)
    col_stat_err = fits.Column(name='STAT_ERR', format='511D', array=stat_err_data)
    col_exposure = fits.Column(name='EXPOSURE', format='D', array=exposure_data)
    col_tstart = fits.Column(name='TSTART', format='D', array=tstart_data)
    col_tstop = fits.Column(name='TSTOP', format='D', array=tstop_data)

    # Defining columns as a ColDefs object
    coldefs = fits.ColDefs([col_spec_num, col_channel, col_counts, col_stat_err, col_exposure, col_tstart, col_tstop])
    
    # Creating the SPECTRUM extension using the ColDefs object
    spectrum_hdu = fits.BinTableHDU.from_columns(coldefs)
    spectrum_hdu.header['TSTART'] = mjd_start
    spectrum_hdu.header['TSTOP'] = np.max(time_mjd)
    spectrum_hdu.header['EXTNAME'] = 'SPECTRUM'
    spectrum_hdu.header['TELESCOP'] = 'ADITYA-L1'
    spectrum_hdu.header['INSTRUME'] = 'HEL1OS'
    spectrum_hdu.header['HDUCLASS'] = 'OGIP'
    spectrum_hdu.header['RESPFILE'] = 'none'
    spectrum_hdu.header['ANCRFILE'] = 'none'    
    spectrum_hdu.header['BACKFILE'] = 'none'
    spectrum_hdu.header['CORRFILE'] = 'none'
    spectrum_hdu.header['BACKSCAL'] = 1.0
    spectrum_hdu.header['AREASCAL'] = 1.0
    spectrum_hdu.header['CORRSCAL'] = 0.0
    spectrum_hdu.header['HDUVERS'] = '1.2.1'
    spectrum_hdu.header['TLMIN2'] = 1
    spectrum_hdu.header['TLMAX2'] = 511
    spectrum_hdu.header['CHANTYPE'] = 'PI'
    spectrum_hdu.header['DETCHANS'] = 511
    spectrum_hdu.header['DETNAM'] = detname
    spectrum_hdu.header['DATE_OBS'] = date_obs
    spectrum_hdu.header['TIME_OBS'] = time_obs
    spectrum_hdu.header['DATE_END'] = date_end
    spectrum_hdu.header['TIME_END'] = time_end
    spectrum_hdu.header['FILENAME'] = output_filename

    # Creating the Primary extension (can be left empty)
    primary_hdu = fits.PrimaryHDU()

    # Write the FITS file with both Primary and SPECTRUM extensions
    hdul = fits.HDUList([primary_hdu, spectrum_hdu])
    hdul.writeto(output_filename, overwrite=True)

    print(f"Type II spectra created: {output_filename}")

#==========================================================================================================================
# Function to create a combined Type II spectra file of both CZT detectors with given time bin size binning
def Combined_czt_spectra(events1,events2,output_filename, detname):
    # Extracting time and energy from 'TIME' and 'ENER' columns
    time_mjd1 = events1['MJD']
    energy_column1 = events1['ener']
    time_mjd2 = events2['MJD']
    energy_column2 = events2['ener']
    time_mjd = np.concatenate([time_mjd1, time_mjd2])
    energy_column = np.concatenate([energy_column1, energy_column2])
    # Defining the time bin size (20-second intervals)
    time_bin_size = 20
    
    # Defining energy binning (341 channels between 8.26834831480671 and 150 keV)
    energy_bins = np.arange(8.26834831480671, 8.26834831480671 + 341 * 0.4151411242631124, 0.4151411242631124)
    
    # Bining events by time and creating histograms for each time bin
    spectra, tstart_values, tstop_values, mjd_start = fixed_time_binning(time_mjd, energy_column, time_bin_size, energy_bins)
    
    # Converting MJD start and end times to DATE-OBS and TIME-OBS, DATE-END and TIME-END
    time_obj_start = Time(mjd_start, format='mjd')
    time_obj_end = Time(np.max(time_mjd), format='mjd')
    date_obs = time_obj_start.utc.strftime('%Y-%m-%d')
    time_obs = time_obj_start.utc.strftime('%H:%M:%S.%f')
    date_end = time_obj_end.utc.strftime('%Y-%m-%d')
    time_end = time_obj_end.utc.strftime('%H:%M:%S.%f')
    
    # Preparing the data for each spectrum (counts, stat_err, exposure, tstart, tstop)
    counts_data = np.array(spectra)  # Shape (number of time bins, 341)
    ener_edges  = np.array(energy_bins)
    stat_err_data = np.sqrt(counts_data)  # Poisson errors as sqrt of counts
    exposure_data = np.full(len(tstart_values), 20.0)  # Constant exposure time of 20 seconds
    spec_num_data = np.arange(len(tstart_values))  # SPEC_NUM as the row number (0, 1, 2, ...)
    channel_data = np.tile(np.arange(341) + 1, (len(tstart_values), 1))  # Array from 1 to 341 repeated for each spectrum
    tstart_data = np.array(tstart_values)
    tstop_data = np.array(tstop_values)
    
    # Create the PHA columns
    col_spec_num = fits.Column(name='SPEC_NUM', format='I', array=spec_num_data)
    col_channel = fits.Column(name='CHANNEL', format='341J', array=channel_data)
    col_counts = fits.Column(name='COUNTS', format='341D', array=counts_data)
    col_stat_err = fits.Column(name='STAT_ERR', format='341D', array=stat_err_data)
    col_exposure = fits.Column(name='EXPOSURE', format='D', array=exposure_data)
    col_tstart = fits.Column(name='TSTART', format='D', array=tstart_data)
    col_tstop = fits.Column(name='TSTOP', format='D', array=tstop_data)

    # Define columns as a ColDefs object
    coldefs = fits.ColDefs([col_spec_num, col_channel, col_counts, col_stat_err, col_exposure, col_tstart, col_tstop])
    
    # Create the SPECTRUM extension using the ColDefs object
    spectrum_hdu = fits.BinTableHDU.from_columns(coldefs)
    spectrum_hdu.header['TSTART'] = mjd_start
    spectrum_hdu.header['TSTOP'] = np.max(time_mjd)
    spectrum_hdu.header['EXTNAME'] = 'SPECTRUM'
    spectrum_hdu.header['TELESCOP'] = 'ADITYA-L1'
    spectrum_hdu.header['INSTRUME'] = 'HEL1OS'
    spectrum_hdu.header['HDUCLASS'] = 'OGIP'
    spectrum_hdu.header['RESPFILE'] = 'none'
    spectrum_hdu.header['ANCRFILE'] = 'none'    
    spectrum_hdu.header['BACKFILE'] = 'none'
    spectrum_hdu.header['CORRFILE'] = 'none'
    spectrum_hdu.header['BACKSCAL'] = 1.0
    spectrum_hdu.header['AREASCAL'] = 1.7421875 #accounting for two dectors area (#history kkk Feb9-2026)
    spectrum_hdu.header['CORRSCAL'] = 0.0
    spectrum_hdu.header['HDUVERS'] = '1.2.1'
    spectrum_hdu.header['TLMIN2'] = 1
    spectrum_hdu.header['TLMAX2'] = 341
    spectrum_hdu.header['CHANTYPE'] = 'PI'
    spectrum_hdu.header['DETCHANS'] = 341
    spectrum_hdu.header['DETNAM'] = detname
    spectrum_hdu.header['DATE_OBS'] = date_obs
    spectrum_hdu.header['TIME_OBS'] = time_obs
    spectrum_hdu.header['DATE_END'] = date_end
    spectrum_hdu.header['TIME_END'] = time_end
    spectrum_hdu.header['FILENAME'] = output_filename

    # Create the Primary extension (can be left empty)
    primary_hdu = fits.PrimaryHDU()
    # Write the FITS file with both Primary and SPECTRUM extensions
    hdul = fits.HDUList([primary_hdu, spectrum_hdu])
    hdul.writeto(output_filename, overwrite=True)

    print(f"Type II spectra created: {output_filename}")

#==========================================================================================================================
# Function to create a combined Type II spectra file of both CdTe detectors with given time bin size binning
def Combined_cdte_spectra(events1,events2,output_filename, detname):
    # Extracting time and energy from 'TIME' and 'ENER' columns
    time_mjd1 = events1['MJD']
    energy_column1 = events1['ener']
    time_mjd2 = events2['MJD']
    energy_column2 = events2['ener']
    time_mjd = np.concatenate([time_mjd1, time_mjd2])
    energy_column = np.concatenate([energy_column1, energy_column2])
    
    # Defining the time bin size
    time_bin_size = 20  # 1 minute in seconds
    
    # Defining energy binning (511 channels between 1.9340889076913443 and 90 keV)
    energy_bins = np.arange(1.9340889076913443, 1.9340889076913443 + 511 * 0.1723735860549766, 0.1723735860549766)
    
    # Bining events by time and creating histograms for each time bin
    spectra, tstart_values, tstop_values, mjd_start = fixed_time_binning(time_mjd, energy_column, time_bin_size, energy_bins)
    
    # Converting MJD start and end times to DATE-OBS and TIME-OBS, DATE-END and TIME-END
    time_obj_start = Time(mjd_start, format='mjd')
    time_obj_end = Time(np.max(time_mjd), format='mjd')
    date_obs = time_obj_start.utc.strftime('%Y-%m-%d')
    time_obs = time_obj_start.utc.strftime('%H:%M:%S.%f')
    date_end = time_obj_end.utc.strftime('%Y-%m-%d')
    time_end = time_obj_end.utc.strftime('%H:%M:%S.%f')
    
    # Preparing the data for each spectrum (counts, stat_err, exposure, tstart, tstop)
    counts_data = np.array(spectra)  # Shape (number of time bins, 511)
    ener_edges  = np.array(energy_bins)
    stat_err_data = np.sqrt(counts_data)  # Poisson errors as sqrt of counts
    exposure_data = np.full(len(tstart_values), 20.0)  # Constant exposure time of 20 seconds
    spec_num_data = np.arange(len(tstart_values))  # SPEC_NUM as the row number (0, 1, 2, ...)
    channel_data = np.tile(np.arange(511)+1, (len(tstart_values), 1))  # Array from 1 to 511 repeated for each spectrum
    tstart_data = np.array(tstart_values)
    tstop_data = np.array(tstop_values)
    
    # defining columns of the spectra
    col_spec_num = fits.Column(name='SPEC_NUM', format='I', array=spec_num_data)
    col_channel = fits.Column(name='CHANNEL', format='511J', array=channel_data)
    col_counts = fits.Column(name='COUNTS', format='511D', array=counts_data)
    col_stat_err = fits.Column(name='STAT_ERR', format='511D', array=stat_err_data)
    col_exposure = fits.Column(name='EXPOSURE', format='D', array=exposure_data)
    col_tstart = fits.Column(name='TSTART', format='D', array=tstart_data)
    col_tstop = fits.Column(name='TSTOP', format='D', array=tstop_data)

    # Defining columns as a ColDefs object
    coldefs = fits.ColDefs([col_spec_num, col_channel, col_counts, col_stat_err, col_exposure, col_tstart, col_tstop])
    
    # Creating the SPECTRUM extension using the ColDefs object
    spectrum_hdu = fits.BinTableHDU.from_columns(coldefs)
    spectrum_hdu.header['TSTART'] = mjd_start
    spectrum_hdu.header['TSTOP'] = np.max(time_mjd)
    spectrum_hdu.header['EXTNAME'] = 'SPECTRUM'
    spectrum_hdu.header['TELESCOP'] = 'ADITYA-L1'
    spectrum_hdu.header['INSTRUME'] = 'HEL1OS'
    spectrum_hdu.header['HDUCLASS'] = 'OGIP'
    spectrum_hdu.header['RESPFILE'] = 'none'
    spectrum_hdu.header['ANCRFILE'] = 'none'    
    spectrum_hdu.header['BACKFILE'] = 'none'
    spectrum_hdu.header['CORRFILE'] = 'none'
    spectrum_hdu.header['BACKSCAL'] = 1.0
    spectrum_hdu.header['AREASCAL'] = 2.0 #accounting for two dectros area (#history kkk Feb4-2026)
    spectrum_hdu.header['CORRSCAL'] = 0.0
    spectrum_hdu.header['HDUVERS'] = '1.2.1'
    spectrum_hdu.header['TLMIN2'] = 1
    spectrum_hdu.header['TLMAX2'] = 511
    spectrum_hdu.header['CHANTYPE'] = 'PI'
    spectrum_hdu.header['DETCHANS'] = 511
    spectrum_hdu.header['DETNAM'] = detname
    spectrum_hdu.header['DATE_OBS'] = date_obs
    spectrum_hdu.header['TIME_OBS'] = time_obs
    spectrum_hdu.header['DATE_END'] = date_end
    spectrum_hdu.header['TIME_END'] = time_end
    spectrum_hdu.header['FILENAME'] = output_filename

    # Creating the Primary extension (can be left empty)
    primary_hdu = fits.PrimaryHDU()
    # Writing FITS file with both Primary and SPECTRUM extensions
    hdul = fits.HDUList([primary_hdu, spectrum_hdu])
    hdul.writeto(output_filename, overwrite=True)

    print(f"Type II spectra created: {output_filename}")


# Loading the event data and creating the spectral file with fixed time binning
filename = 'evt.fits'
hdul = fits.open(filename)
#===========================================================================
#History Kiran Dec26-2025 (To find minimum time of all detectors events)
mjd1 = hdul[1].data['MJD']
mjd2 = hdul[2].data['MJD']
mjd3 = hdul[3].data['MJD']
mjd4 = hdul[4].data['MJD']
Concatinated_time = np.concatenate([mjd1,mjd2,mjd3,mjd4])
#===========================================================================
# Processing the cdte1-events (HDU extension 1)
events_CdTe1 = hdul[1].data
cdte_spectra(events_CdTe1, 'CdTe1_TypeII_spectra.fits', detname='CdTe1')

# Processing the cdte2-events (HDU extension 2)
events_CdTe2 = hdul[2].data
cdte_spectra(events_CdTe2, 'CdTe2_TypeII_spectra.fits', detname='CdTe2')

# Processing the czt1-events (HDU extension 3)
events_czt1 = hdul[3].data
czt_spectra(events_czt1, 'CZT1_TypeII_spectra.fits', detname='CZT1')

# Processing the czt2-events (HDU extension 4)
events_czt2 = hdul[4].data
czt_spectra(events_czt2, 'CZT2_TypeII_spectra.fits', detname='CZT2')

# Processing the cdte1-events (HDU extension 1)
Combined_cdte_spectra(events_CdTe1,events_CdTe2, 'CdTe_Combined_TypeII_spectra.fits', detname='CdTe')
Combined_czt_spectra(events_czt1,events_czt2, 'CZT_Combined_TypeII_spectra.fits', detname='CZT')

