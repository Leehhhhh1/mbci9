import numpy as np
# impedance
channels = ['Fpz', 'Fp1', 'Fp2', 'Fz',  'F3', 'F4',  'F6', 'F7', 'F8',  'FCz',  'Cz',  'C3', 'C4',  'T7', 'T8',  'Pz',  'P3', 'P4',  'P7', 'P8',  'Oz', 'O1', 'O2']
flag_channels = np.zeros(21) # 选择导联位置


impedance_max = 10
impedance_min = 0

impedance_range = [5, 10, 20, 50]
impedance_color = [[0, 102, 204], [0, 204, 0], [255, 204, 0], [255, 128, 0], [255, 0, 0]] # 蓝色 绿色 黄色 橙色 红色
# filter
notch_freq = 50 # 陷波频率
low_cutoff = 4 # 带通滤波器的低频截止频率
high_cutoff = 90 # 带通滤波器的高频截止频率