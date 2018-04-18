# BIO DATA PARSER
A python script to process and plot ECG and PPG signal of a mysterious file format

# Requirements
Check the requirements.txt and make sure necessary packages are installed.

# Usage
main.py [-h] [--export_csv] [--fft] [--plot_type {0,5,9,12}]
        raw_data_file [annotation_file]

# File Type
* For ACC, type should be 0
* For ECG, type should be 5
* For PPG 125 Hz, type should be 9
* For PPG 512 Hz, type should be 12
