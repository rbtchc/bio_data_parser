#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import argparse
import rx
import numpy as np
import time
import matplotlib.pyplot as plot
from rx import Observable
from parser import calc_ts
from parser import parse_raw_acc, acc_data
from parser import parse_raw_ecg, ecg_data
from parser import parse_raw_ppg125, parse_raw_ppg512, ppg125_data, ppg512_data
from filters import acc_bp_filter
from filters import ppg125_pl_filter, ppg125_bp_filter
from filters import ppg512_pl_filter, ppg512_bp_filter
from filters import ecg_hp_filter, ecg_lp_filter, ecg_pl_filter
from filters import acc_flat
from filters import ACC_FS, ECG_FS, PPG_FS_125, PPG_FS_512
from plots import plot_time_domain, plot_freq_domain, plot_annotation
from annotation import parse_annotation, annotation_data

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--export_csv', help='Export to csv file', action='store_true')
    p.add_argument('--fft', help='Apply FFT bandpass filter', action='store_true')
    p.add_argument('--plot_type', nargs=1, default=None, type=int, choices=[0, 5, 9, 12], help='0: Acc, 5: ECG, 9: PPG 125 Hz, 12: PPG 512 Hz)')
    p.add_argument('raw_data_file', nargs=1, help='Specify the raw data file')
    p.add_argument('annotation_file', nargs='?', help='Specify the annotation file')
    return vars(p.parse_args())

def group_key_generator(x):
    return x.split(',')[0]

def group_by_handler(x):
    if x.key == '0':
        x.subscribe(on_next=parse_raw_acc, on_completed=acc_data_handler)
    elif x.key == '5':
        x.subscribe(on_next=parse_raw_ecg, on_completed=ecg_data_handler)
    elif x.key == '9':
        x.subscribe(on_next=parse_raw_ppg125, on_completed=ppg125_data_handler)
    elif x.key == '12':
        x.subscribe(on_next=parse_raw_ppg512, on_completed=ppg512_data_handler)

def bandpass_filter(data, fs, lowcut, highcut, order=3):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = signal.butter(order, [low, high], btype='band')
    return scipy.signal.filtfilt(b, a, data)

def acc_data_handler():
    def output(x):
        if args["export_csv"]:
            np.savetxt(args["acc_csv"], x, delimiter=',')
        if args["plot_type"] and args["plot_type"][0] == 0:
            s = np.square(x[:,1:])
            mag = np.sum(s, axis=1)
            mag = np.column_stack((x[:,0], mag))
            plot_time_domain(ax1, mag)
            plot_freq_domain(ax2, mag[:,1], ACC_FS)

    # pipeline
    if args["fft"]:
        Observable.just(acc_data)             \
                  .map(calc_ts)               \
                  .map(acc_flat)              \
                  .map(lambda x: np.array(x)) \
                  .map(acc_bp_filter) \
                  .subscribe(output)
    else:
        Observable.just(acc_data)             \
                  .map(calc_ts)               \
                  .map(acc_flat)              \
                  .map(lambda x: np.array(x)) \
                  .subscribe(output)

def ecg_data_handler():
    def output(x):
        if args["export_csv"]:
            np.savetxt(args["ecg_csv"], x, delimiter=',')
        if args["plot_type"] and args["plot_type"][0] == 5:
            plot_time_domain(ax1, x)
            plot_freq_domain(ax2, x[:,1], ECG_FS)

    # pipeline
    if args["fft"]:
        Observable.just(ecg_data)             \
                  .map(calc_ts)               \
                  .map(lambda x: np.array(x)) \
                  .map(ecg_pl_filter) \
                  .map(ecg_hp_filter) \
                  .map(ecg_lp_filter) \
                  .subscribe(output)
    else:
        Observable.just(ecg_data)             \
                  .map(calc_ts)               \
                  .map(lambda x: np.array(x)) \
                  .subscribe(output)

def ppg125_data_handler(arg_fname="ppg125_csv", data_type=9, freq=PPG_FS_125, \
                        fn_bp=ppg125_bp_filter, data=ppg125_data):
    def output(x):
        if args["export_csv"]:
            np.savetxt(args[arg_fname], x, delimiter=',')
        if args["plot_type"] and args["plot_type"][0] == data_type:
            plot_time_domain(ax1, x)
            plot_freq_domain(ax2, x[:,1], freq)

    # pipeline
    if args["fft"]:
        Observable.just(data) \
                  .map(calc_ts) \
                  .map(lambda x: np.array(x)) \
                  .map(fn_bp) \
                  .subscribe(output)
    else:
        Observable.just(data) \
                  .map(calc_ts) \
                  .map(lambda x: np.array(x)) \
                  .subscribe(output)


def ppg512_data_handler():
    ppg125_data_handler("ppg512_csv", 12, PPG_FS_512, ppg512_bp_filter, ppg512_data)

def annotation_handler():
    if args["plot_type"]:
        plot_annotation(ax1, annotation_data)

def verbose(x):
    print x

######################################################################

# parse arguments
args = parse_args()

print args

ax1 = ax2 = None
if args["plot_type"]:
    _, (ax1, ax2) = plot.subplots(2, 1)

# prepare something for later use
input_file = os.path.basename(args["raw_data_file"][0])
basename = os.path.splitext(input_file)[0]
args["acc_csv"] = basename + "_acc.csv"
args["ecg_csv"] = basename + "_ecg.csv"
args["ppg125_csv"] = basename + "_ppg125.csv"
args["ppg512_csv"] = basename + "_ppg512.csv"

# Ideally, observables can be executed in different threads.
# However, it's difficult becuase matplotlib can only be executed in
# the main thread and pyplot.show() only can be executed once.
# So, we only take advantage of reactivex to build the data pipeline by
# observable::map().

if args["annotation_file"]:
    a = open(args["annotation_file"])
    alines = a.read().split('\n')
    Observable.from_(alines)                            \
              .filter(lambda x: True if x else False)   \
              .subscribe(on_next=parse_annotation, on_completed=annotation_handler)

f = open(args["raw_data_file"][0])
lines = f.read().split('\n')
Observable.from_(lines)                  \
          .group_by(group_key_generator) \
          .subscribe(group_by_handler)

if args["plot_type"]:
    plot.show()
