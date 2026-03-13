import numpy as np
import mne
from scipy import signal
from scipy.fftpack import fft

def preprocessing(data_EEG, num_channels, sample, downsample, notch_freq = 50, low_cutoff = 1, high_cutoff = 45): #（通道， 时间）
    if sample == 0:
        return data_EEG
    # Fp1, Fp2, F3, F4, C3, Cz, C4, Pz
    data_channels = np.asarray(data_EEG,dtype=np.float64)
    # 去除基线漂移，使用高通滤波器
    cutoff_freq = 0.5  # 高通滤波器的截止频率
    nyquist = 0.5 * sample
    normal_cutoff = cutoff_freq / nyquist
    filtered_data_channels = data_channels
    if 0 < normal_cutoff < 1:
        b, a = signal.butter(1, normal_cutoff, btype='high')
        filtered_data_channels = signal.filtfilt(b, a, data_channels, padlen=150, axis=1)

    # 陷波滤波器，去除特定频率的噪声（如50Hz或60Hz电源噪声）
    nyquist = 0.5 * sample
    quality_factor = 30  # 品质因数（决定滤波器的宽度，通常取值在30-50之间）
    normalized_notch_freq = notch_freq / nyquist
    notched_data_channels = filtered_data_channels
    if 0 <= normalized_notch_freq <= 1:
        b, a = signal.iirnotch(normalized_notch_freq, quality_factor)
        notched_data_channels = signal.filtfilt(b, a, filtered_data_channels, axis=1)

    # 带通滤波器，用于去除低频（如基线漂移）和高频噪声（如肌电噪声）
    nyquist = 0.5 * sample
    low = low_cutoff / nyquist
    high = high_cutoff / nyquist
    buttered_data_channels = notched_data_channels
    if 0 <= low and high <= 1 and low <= high:
        b, a = signal.butter(4, [low, high], btype='band')
        buttered_data_channels = signal.filtfilt(b, a, notched_data_channels, padlen=150, axis = 1)

    # down sampled to sample/downsample Hz 降采样
    data_down_channels = buttered_data_channels
    if downsample != 1:
        data_down_channels = mne.filter.resample(buttered_data_channels, down=downsample, npad='auto', axis=1,
                                                 window='boxcar', n_jobs=1, pad='reflect_limited', verbose=None)
    return data_down_channels #（通道， 时间）

def get_impedance(data):
    len_data = len(data[0])
    fft_data = fft(data)
    fft_amp0 = np.array(np.abs(fft_data) / len_data / 2)
    fft_amp1 = fft_amp0[:, 0: int(len_data / 2)]
    power_31_2hz = fft_amp1[:, 312]
    a = 5.64534481e-07
    b = 2.35829413e-01
    c = -4.74977582e+00
    impedance = a * power_31_2hz * power_31_2hz  + b * power_31_2hz + c
    return np.abs(impedance)
    # # 拟合方程: y = -0.02x² + 3.66x + -5.76
    # a = -0.02
    # b = 3.66
    # c = -5.76
    # impedance = a * power_31_2hz * power_31_2hz + b * power_31_2hz + c
    # return np.abs(impedance)

# if __name__ == "__main__":
#     raw_data = np.random.rand(8, 2500)
#     data = preprocessing(raw_data, 2000, 8)
#     #data = get_impedance(raw_data, samples=250)
#     print(data)