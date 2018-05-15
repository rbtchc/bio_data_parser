#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import matplotlib.pyplot as plot
import numpy as np
import os
import rx

from annotation import parse_annotation, annotation_data
from filters import acc_bp_filter, ppg125_bp_filter, ppg512_bp_filter, ecg_bp_filter, ecg_pl_filter
from filters import ACC_FS, ECG_FS, PPG_FS_125, PPG_FS_512
from parser import calc_ts, ppg125_reseq, ppg512_reseq, ecg_reseq, acc_reseq
from parser import parse_raw_acc, acc_data
from parser import parse_raw_ecg, ecg_data
from parser import parse_raw_ppg125, ppg125_data
from parser import parse_raw_ppg512, ppg512_data
from parser import parse_raw_hr, hr_data
from plots import plot_time_domain, plot_freq_domain, plot_annotation
from rx import Observable

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--export_csv', help='Export to csv file', action='store_true')
    p.add_argument('--fft', help='Apply FFT bandpass filter', action='store_true')
    p.add_argument('--plot_type', default=None, type=int, choices=[0, 5, 9, 12], \
                   help='0: Acc, 5: ECG, 9: PPG 125 Hz, 12: PPG 512 Hz)')
    p.add_argument('raw_data_file', help='Specify the raw data file')
    p.add_argument('annotation_file', nargs='?', help='Specify the annotation file')
    return vars(p.parse_args())

def default_plot_fn(ax1, ax2, x, freq):
    plot_time_domain(ax1, x[:,1:])
    plot_freq_domain(ax2, x[:,2], freq)

def acc_plot_fn(ax1, ax2, x, freq):
    s = np.square(x[:,2:])
    mag = np.sum(s, axis=1)
    mag = np.column_stack((x[:,1], mag))

    plot_time_domain(ax1, mag)
    plot_freq_domain(ax2, mag[:,1], freq)

def data_handler(arg_fname, data_type, freq, fn_filters, data, fn_reseq, plot_fn=default_plot_fn):
    def output(x):
        if args["export_csv"]:
            np.savetxt(args[arg_fname], x, delimiter=',')

        if args["plot_type"] != None and args["plot_type"] == data_type:
            plot_fn(ax1, ax2, x, freq)

    x = Observable.just(data) \
                  .map(calc_ts) \
                  .map(fn_reseq) \
                  .map(lambda x: np.array(x))

    if args["fft"]:
        for f in fn_filters:
            x = x.map(f)

    x.subscribe(output)

def acc_data_handler():
    data_handler("acc_csv", 0, ACC_FS, [acc_bp_filter], acc_data, acc_reseq, acc_plot_fn)

def ecg_data_handler():
    data_handler("ecg_csv", 5, ECG_FS, [ecg_pl_filter, ecg_bp_filter], ecg_data, ecg_reseq)

def ppg125_data_handler():
    data_handler("ppg125_csv", 9, PPG_FS_125, [ppg125_bp_filter], ppg125_data, ppg125_reseq)

def ppg512_data_handler():
    data_handler("ppg512_csv", 12, PPG_FS_512, [ppg512_bp_filter], ppg512_data, ppg512_reseq)

def hr_data_handler():
    if not args["export_csv"]:
        return

    with open(args['hr_csv'], 'w') as out:
        out.write("#timestamp,reported_hr,original_hr,confidence,is_drop\n")
        #print hr.shape
        for i in xrange(len(hr_data)):
            beats, confidence, local_ts, ts = hr_data[i][:]
            drop = 0
            if confidence == 255:
                #'drop bcz confidence == -1'
                drop = 1
            elif confidence in [0, 1]:
                if i > 0:
                    if hr_data[i-1][1] == 3:
                        beats = hr_data[i-1][0]
                    else:
                        #'drop, bcz prev confidence in [0, 1, 2, 255]'
                        drop = 1
                else:
                    drop = 1
            out.write("%d,%d,%d,%d,%d\n" % (ts, beats, hr_data[i][0], confidence, drop))


def group_key_generator(x):
    return x.split(',')[0]

_group_by_handlers = {
        '0':  {"on_next": parse_raw_acc,    "on_completed": acc_data_handler},
        '5':  {"on_next": parse_raw_ecg,    "on_completed": ecg_data_handler},
        '9':  {"on_next": parse_raw_ppg125, "on_completed": ppg125_data_handler},
        '12': {"on_next": parse_raw_ppg512, "on_completed": ppg512_data_handler},
        '22': {"on_next": parse_raw_hr,     "on_completed": hr_data_handler}
        }

def group_by_handler(x):
    # silently drop unknow lines
    if x.key not in _group_by_handlers.keys():
        return
    x.subscribe(**_group_by_handlers[x.key])

def annotation_handler():
    if args["plot_type"] != None:
        plot_annotation(ax1, annotation_data)

if __name__ == "__main__":
    # parse arguments
    args = parse_args()
    print args

    ax1 = ax2 = None
    if args["plot_type"] != None: _, (ax1, ax2) = plot.subplots(2, 1)

    # prepare something for later use
    basename = os.path.splitext(os.path.basename(args["raw_data_file"]))[0]
    for n in ["acc", "ecg", "ppg125", "ppg512", "hr"]:
        args[n+"_csv"] = basename + "_" + n + ".csv"

    # Ideally, observables can be executed in different threads.
    # However, it's difficult becuase matplotlib can only be executed in
    # the main thread and pyplot.show() only can be executed once.
    # So, we only take advantage of reactivex to build the data pipeline by
    # observable::map().

    if args["annotation_file"]:
        Observable.from_(open(args["annotation_file"])) \
                  .map(lambda x: x.strip()) \
                  .filter(lambda x: True if x else False) \
                  .subscribe(on_next=parse_annotation, on_completed=annotation_handler)

    Observable.from_(open(args["raw_data_file"])) \
              .map(lambda x: x.strip()) \
              .group_by(group_key_generator) \
              .subscribe(group_by_handler)

    if args["plot_type"] != None: plot.show()

