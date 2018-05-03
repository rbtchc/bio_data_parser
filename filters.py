import scipy
import numpy as np
from scipy import signal

ACC_FS = 20
ECG_FS = 512
PPG_FS_125 = 125 # need to skip ambient light data 
PPG_FS_512 = 512 # don't skip any received data, ambient data has been skipped by the watch

LOW_PASS_CUTOFF = 35
HIGH_PASS_CUTOFF = 0.5

def power_line_noise_filter(data, fs, f0=65.0, Q=30.0):
    w0 = f0 / (fs/2)
    b, a = signal.iirnotch(w0, Q)
    return scipy.signal.filtfilt(b, a, data)

def butter_filter(data, fs, f1, f2=None, btype='band', order=3):
    nyq = 0.5 * fs
    cutoff = [f1/nyq, f2/nyq] if btype == 'band' else f1/nyq
    b, a = scipy.signal.butter(order, cutoff, btype=btype, analog=False)
    return scipy.signal.filtfilt(b, a, data)

def butter_bandpass_filter(data, fs, lowcut, highcut, order=3):
    return butter_filter(data, fs, lowcut, highcut, 'band', order)

def high_pass_filter(data, fs, cutoff, order=3):
    return butter_filter(data, fs, cutoff, btype='highpass', order=order)

def low_pass_filter(data, fs, cutoff, order=3):
    return butter_filter(data, fs, cutoff, btype='lowpass', order=order)

def acc_bp_filter(data, fs=100):
    for i in range(1,4):
        data[:,i] = butter_bandpass_filter(data[:,i], fs, HIGH_PASS_CUTOFF, LOW_PASS_CUTOFF)
    return data

def ppg125_pl_filter(x):
    """ A map function to perform power line noise filter against ppg125 data
    Input: numpy array
    Output: numpy array
    """
    x[:,1] = power_line_noise_filter(x[:,1], PPG_FS_125)
    return x

def ppg125_hp_filter(x):
    """ A map function to perform high pass filter against ppg125 data
    Input: numpy array
    Output: numpy array
    """
    x[:,1] = high_pass_filter(x[:,1], PPG_FS_125, HIGH_PASS_CUTOFF)
    return x

def ppg125_lp_filter(x):
    """ A map function to perform low pass filter against ppg125 data
    Input: numpy array
    Output: numpy array
    """
    x[:,1] = high_pass_filter(x[:,1], PPG_FS_125, LOW_PASS_CUTOFF)
    return x

def ppg125_bp_filter(x, fs=PPG_FS_125):
    x[:,1] = butter_bandpass_filter(x[:,1], fs, HIGH_PASS_CUTOFF, LOW_PASS_CUTOFF)
    return x

def ppg512_bp_filter(x):
    return ppg125_bp_filter(x, PPG_FS_512)

def ppg512_pl_filter(x):
    """ A map function to perform power line noise filter against ppg512 data
    Input: numpy array
    Output: numpy array
    """
    x[:,1] = power_line_noise_filter(x[:,1], PPG_FS_512)
    return x

def ppg512_hp_filter(x):
    """ A map function to perform high pass filter against ppg512 data
    Input: numpy array
    Output: numpy array
    """
    x[:,1] = high_pass_filter(x[:,1], PPG_FS_512, HIGH_PASS_CUTOFF)
    return x

def ppg512_lp_filter(x):
    """ A map function to perform low pass filter against ppg512 data
    Input: numpy array
    Output: numpy array
    """
    x[:,1] = low_pass_filter(x[:,1], PPG_FS_512, LOW_PASS_CUTOFF)
    return x

def ecg_pl_filter(x):
    """ A map function to perform power line noise filter against ecg data
    Input: numpy array
    Output: numpy array
    """
    x[:,1] = power_line_noise_filter(x[:,1], ECG_FS)
    return x

def ecg_hp_filter(x):
    """ A map function to perform high pass filter against ecg data
    Input: numpy array
    Output: numpy array
    """
    x[:,1] = high_pass_filter(x[:,1], ECG_FS_512, HIGH_PASS_CUTOFF)
    return x

def ecg_lp_filter(x):
    """ A map function to perform low pass filter against ecg data
    Input: numpy array
    Output: numpy array
    """
    x[:,1] = low_pass_filter(x[:,1], ECG_FS_512, LOW_PASS_CUTOFF)
    return x

def acc_mag_filter(x):
    filtered = x[:,1]
    # ??
    return x

def acc_flat(x):
    """ A map function to simply the acc data format
    Input: list, e.g. [(timestamp, (x, y, z))]
    Output: list, e.g. [[timestamp, x, y, z]]
    """
    return [[i[0], i[1][0], i[1][1], i[1][2]] for i in x]
