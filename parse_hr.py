#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import os
import sys

if len(sys.argv) < 2:
    print 'usage: %s <filename>' % (sys.argv[0])
    sys.exit(1)

data = np.genfromtxt(sys.argv[1], delimiter=',', dtype=np.int, invalid_raise=False)

# filter out non-HR, and leave HR, confidence, local timestamp and app timestamp
hr = data[data[:,0] == 22, :][:, [2,3,4,15]]
hr[:,1] &= 0xff

input_file = os.path.basename(sys.argv[1])
basename = os.path.splitext(input_file)[0]
output = basename + "_hr.csv"

with open(output, 'w') as out:
    out.write("#timestamp,reported_hr,original_hr,confidence,is_drop\n")
    #print hr.shape
    for i in xrange(hr.shape[0]):
        beats, confidence, local_ts, ts = hr[i][:]
        drop = 0
        if confidence == 255:
            #'drop bcz confidence == -1'
            drop = 1
        elif confidence in [0, 1]:
            if i > 0:
                if hr[i-1][1] == 3:
                    beats = hr[i-1][0]
                else:
                    #'drop, bcz prev confidence in [0, 1, 2, 255]'
                    drop = 1
            else:
                drop = 1
        out.write("%d,%d,%d,%d,%d\n" % (ts, beats, hr[i][0], confidence, drop))

print 'Done!'
