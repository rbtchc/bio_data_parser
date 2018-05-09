import numpy as np
import re

TYPE_ECG=5
TYPE_PPG125=9
TYPE_PPG512=12
MSEC_PER_SEC = 1000

acc_data = []
ecg_data = []
ppg125_data = []
ppg512_data = []

def convert_ppg_to_mv(v):
    if v >= (1<<22):
        v = v - (1<<23)
    return (v * 3.2 * 1000) / 65536

def convert_ecg_to_mv(v):
    if v >= (1<<22):
        v = v - (1<<23)
    return (v * 1000) / (6 * 2097152)

def is_ecg(t):
    return t == TYPE_ECG

def is_ppg(t):
    return is_ppg125(t) or is_ppg512(t)

def is_ppg125(t):
    return t == TYPE_PPG125

def is_ppg512(t):
    return t == TYPE_PPG512

def parse_raw_acc(x):
    """ Parse one line of raw acc data and add it to acc data """
    items = x.split(',')
    nums = map(int, items)
    ts_ms = nums[15] * MSEC_PER_SEC
    for i in [2, 6, 10]:
        acc_data.append((ts_ms, tuple(nums[i:i+3])))

def parse_raw_hr_signals(x, index, fn, data):
    """ Parse one line of raw ppg/ecg data and add it to ppg/ecg data """
    items = x.split(',')
    # convert ts to ms
    ts_ms = int(items[15]) * MSEC_PER_SEC
    seq = int(items[1])
    # convert signals to mv
    for n in index:
        data.append((ts_ms, seq, fn(int(items[n]))))

def parse_raw_ppg125(x):
    parse_raw_hr_signals(x, range(2, 13, 2), convert_ppg_to_mv, ppg125_data)

def parse_raw_ppg512(x):
    parse_raw_hr_signals(x, range(2, 14), convert_ppg_to_mv, ppg512_data)

def parse_raw_ecg(x):
    """ Parse one line of raw ecg data and add it to ecg data """
    parse_raw_hr_signals(x, range(2,14), convert_ecg_to_mv, ecg_data)

def calc_ts(x):
    base_ms = 0
    data = []
    buf = []
    for l in x:
        new_ms = l[0]
        mv = l[1]
        if base_ms == 0:
            base_ms = new_ms
        elif base_ms != new_ms:
            fraction = float(new_ms - base_ms) / len(buf)
            for i in range(0, len(buf)):
                ts_ms = base_ms + (fraction * i)
                if ts_ms >= new_ms:
                    print "Error: timestamp equal to or larger than new base timestamp"
                data.append((ts_ms, buf[i]))
            base_ms = new_ms
            buf[:] = []
        buf.append(mv)
    return data

def calc_ts_seq(x):
    base_ms = 0
    data = []
    buf = []
    for l in x:
        new_ms = l[0]
        payload = l[1:]
        if base_ms == 0:
            base_ms = new_ms
        elif base_ms != new_ms:
            fraction = float(new_ms - base_ms) / len(buf)
            for i in range(0, len(buf)):
                ts_ms = base_ms + (fraction * i)
                if ts_ms >= new_ms:
                    print "Error: timestamp equal to or larger than new base timestamp"
                data.append([ts_ms, buf[i][0], buf[i][1]])
            base_ms = new_ms
            buf[:] = []
        buf.append(payload)
    return data

def re_sequence(x, new_seq, orig_seq, step):
    '''
    x: input data, column orderd as timestamp, sequence, MV
    new_seq: last new sequence number
    orig_seq; original sequence number
    step: how many data in a sequence number
    '''
    if new_seq == None:
        new_seq = 0
        orig_seq = x[0][1]
    for d in x:
        if (d[1] - orig_seq) > 1:
            new_seq += (d[1] - orig_seq - 1) * step
        orig_seq = d[1]
        d[1] = new_seq = new_seq + 1
    return x, orig_seq, new_seq

def ppg125_reseq(x):
    x, ppg125_reseq.orig_seq, ppg125_reseq.new_seq = re_sequence(x, getattr(ppg125_reseq, 'orig_seq', None), getattr(ppg125_reseq, 'new_seq', None), 6)
    return x

def ppg512_reseq(x):
    x, ppg512_reseq.orig_seq, ppg512_reseq.new_seq = re_sequence(x, getattr(ppg512_reseq, 'orig_seq', None), getattr(ppg512_reseq, 'new_seq', None), 12)
    return x

def ecg_reseq(x):
    x, ecg_reseq.orig_seq, ecg_reseq.new_seq = re_sequence(x, getattr(ecg_reseq, 'orig_seq', None), getattr(ecg_reseq, 'new_seq', None), 12)
    return x


def parse_data(file_obj, signal_type):
    """
    file_obj:    The file obj come from open() or io.BytesIO
    signal_type: 0, 5, 9, or 12
    return:      The list of (timestamp, mv) tuple
    """
    base_ms = 0
    fraction = 0
    buf = []
    data = []
    rule = re.compile("^%d," % signal_type)

    for l in file_obj:
        if not rule.match(l):
            continue

        a = l.rstrip("\n").split(',')
        # extraction
        if is_ecg(signal_type):
            row = a[2:13]
        elif is_ppg125(signal_type):
            row = a[2:13:2]
        elif is_ppg512(signal_type):
            row = a[2:14]
        else:
            print 'unknown type', signal_type
            continue

        # timestamp calculation
        new_base_ms = int(a[15]) * MSEC_PER_SEC
        if base_ms == 0:
	    base_ms = new_base_ms
	elif base_ms != new_base_ms:
            fraction = float(new_base_ms - base_ms) / len(buf)
	    for i in range(0, len(buf)):
                ts_ms = base_ms + (fraction * i)
                # sanity check
		if ts_ms >= new_base_ms:
	            print "Error: timestamp equal to or larger than new base timestamp"
                data.append((ts_ms, buf[i]))
	    base_ms = new_base_ms
	    buf[:] = []

        for i in row:
            if is_ecg(signal_type):
                v = convert_ecg_to_mv(float(i))
            elif is_ppg(signal_type):
                v = convert_ppg_to_mv(float(i))
            buf.append(v)

    return data

if __name__ == "__main__":
    print '-' * 5, 'PPG 512', '-' * 5
    x = '12,20164,8380828,8380830,8380832,8380832,8380835,8380838,8380839,8380841,8380844,8380844,8380847,8380845,12345,1519268239'
    parse_raw_ppg512(x)
    print '\n'.join(map(lambda x: 'ts = %s, mv = %s' % (x[0], x[1]), ppg_data))

    print '-' * 5, 'PPG 125', '-' * 5
    x = "9,99519,17324,8369012,19363,8367862,21051,8366913,22449,8366126,23603,8365479,24560,8364943,12345,1525311794"
    parse_raw_ppg125(x)
    print '\n'.join(map(lambda x: 'ts = %s, mv = %s' % (x[0], x[1]), ppg_data))
