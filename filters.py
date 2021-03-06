import scipy
import numpy as np
from scipy import signal

ACC_FS = 100
ECG_FS = 512
PPG_FS_125 = 125 # need to skip ambient light data 
PPG_FS_512 = 512 # don't skip any received data, ambient data has been skipped by the watch

LOW_PASS_CUTOFF = 5
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

def acc_bp_filter(data, fs=ACC_FS):
    for i in range(2,5):
        data[:,i] = butter_bandpass_filter(data[:,i], fs, HIGH_PASS_CUTOFF, LOW_PASS_CUTOFF)
    return data

def ppg125_bp_filter(x, fs=PPG_FS_125):
    x[:,2] = butter_bandpass_filter(x[:,2], fs, HIGH_PASS_CUTOFF, LOW_PASS_CUTOFF)
    return x

def ppg512_bp_filter(x):
    return ppg125_bp_filter(x, PPG_FS_512)

def ecg_bp_filter(x, fs=ECG_FS):
    x[:,2] = butter_bandpass_filter(x[:,2], fs, HIGH_PASS_CUTOFF, LOW_PASS_CUTOFF)
    return x

def ecg_pl_filter(x):
    """ A map function to perform power line noise filter against ecg data
    Input: numpy array
    Output: numpy array
    """
    x[:,2] = power_line_noise_filter(x[:,2], ECG_FS)
    return x

def acc_mag_filter(x):
    filtered = x[:,1]
    # ??
    return x

