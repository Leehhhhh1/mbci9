import time
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from scipy.fftpack import fft
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from threading import Thread


class Animation_EEG(FigureCanvas):
    def __init__(self, width=10, height=0.25, dpi=110, num_channels=32):
        self.num_channels = num_channels # 通道数
        self.fig, self.axs = plt.subplots(self.num_channels, 1, figsize=(width, self.num_channels * height), dpi=dpi, sharey=False)
        plt.subplots_adjust(hspace=0.5, top=0.99, bottom=0.01)
        super(Animation_EEG, self).__init__(self.fig)

        # 数据内容
        self.len = 1250 # 数据长度
        self.downsamples = 250 # 降采样率
        self.data_eeg = np.zeros((self.num_channels, self.len)) # 数据
        self.x = np.linspace(0, self.len, self.len) # x轴数据
        self.y = self.data_eeg # y轴数据

        # 图像内容
        self.lines = [] # 创建图像线条
        self.colors = ["#A6CEE3", "#1F78B4", "#B2DF8A", "#33A02C", "#FB9A99", "#E31A1C", "#FDBF6F", "#FF7F00",
                       "#CAB2D6", "#6A3D9A", "#FFFF99", "#B15928", "#8DD3C7", "#FFFFB3", "#BEBADA", "#FB8072",
                       "#80B1D3", "#FDB462", "#B3DE69", "#FCCDE5", "#D9D9D9", "#BC80BD", "#CCEBC5", "#FFED6F",
                       "#9ECAE1", "#3182BD", "#74C476", "#31A354", "#FD8D3C", "#E6550D", "#756BB1", "#54278F"]  # 图像颜色
        self.is_updating = False #是否存在更新

        # 设置 x 轴刻度每 250 个点显示一个标签
        def format_func(value, tick_number):
            if value % self.downsamples == 0:
                return f'{int(value / self.downsamples)}'
            else:
                return ''

        # 初始化图像
        for i in range(self.num_channels):
            # 使用 text() 设置标签在左上角
            self.axs[i].text(-0.14, 1.07, f"(μV)", transform=self.axs[i].transAxes, fontsize=6, ha='left', va='top')
            self.axs[i].text(-0.15, 0.5, f"C{i + 1}", transform=self.axs[i].transAxes, fontsize=10, ha='left', va='center', weight='bold')
            # 设置x轴刻度
            self.axs[i].xaxis.set_major_formatter(ticker.FuncFormatter(format_func))
            self.axs[i].xaxis.set_major_locator(ticker.MultipleLocator(self.downsamples))
            # 初始化EEG
            line, = self.axs[i].plot(self.x, self.y[i], lw=1, color=self.colors[i % 32])
            self.lines.append(line)
    plt.show()
    # 更新图像
    def update_animate(self):
        # print("update")
        # self.y = data
        for i in range(self.num_channels):
            self.lines[i].set_ydata(self.y[i])

            # 计算当前通道数据的最小值和最大值
            y_min = np.min(self.y[i])
            y_max = np.max(self.y[i])

            # 设置 y 轴范围，留出一些边距
            margin = 0.1 * (y_max - y_min)  # 10% 的边距
            self.axs[i].set_ylim(y_min - margin, y_max + margin)
        self.draw()
        # self.flush_events()

    # 更新y数据
    def update_y(self, data):
        self.data_eeg = np.hstack((self.data_eeg, data))
        # len_data = len(self.data_eeg[0])
        self.y = self.data_eeg[:, -self.len:]
        # for i in range(self.num_channels):
        #     self.lines[i].set_ydata(self.y[i])
        # self.draw_idle()
        self.update_animate()
        # self.data_eeg = self.data_eeg[:, len_data - self.len:]
        # data = np.round(data, 2)
        # print(np.shape(data))
        # self.data_eeg = data
        # self.y = data


class Animation_Spectrogram(FigureCanvas):
    def __init__(self, width=5, height=4, dpi=100, num_channels=40, samples=250):
        self.num_channels = num_channels # 通道数
        self.fig, self.axs = plt.subplots(1, 1, figsize=(8, 15))
        super(Animation_Spectrogram, self).__init__(self.fig)

        # 数据内容
        self.len = 250 # 数据长度
        self.samples = samples # 采样率     频率分辨率 = 采样频率 / 信号长度
        self.interval = 1 / self.samples # 采样间隔
        self.downsamples = 250 # 降采样率
        self.data_eeg = np.zeros((self.num_channels, self.len)) # 数据
        self.x = np.linspace(0, self.len, self.len) # x轴数据
        self.y = self.data_eeg # y轴数据

        # 初始化频谱图 基于FFT绘制频谱图
        fft_data = fft(self.y)
        fft_amp0 = np.array(np.abs(fft_data) / self.len / 2)
        self.fft_amp1 = fft_amp0[:, 0: int(self.len / 2)]
        self.freq1 = self.samples * np.array(range(0, int(self.len / 2))) / self.len
        self.psd = np.abs(self.fft_amp1) ** 2
        self.average = np.mean(self.psd, axis=0)
        self.psd = np.vstack((self.psd, self.average))
        self.show = [[10 * np.log10(self.psd) if t != 0 else 0 for t in channel]for channel in self.psd]

        # 图像内容
        self.lines = [] # 创建图像线条
        self.is_updating = False  # 是否有更新
        self.colors = ["#A6CEE3", "#1F78B4", "#B2DF8A", "#33A02C", "#FB9A99", "#E31A1C", "#FDBF6F", "#FF7F00",
                       "#CAB2D6", "#6A3D9A", "#FFFF99", "#B15928", "#8DD3C7", "#FFFFB3", "#BEBADA", "#FB8072",
                       "#80B1D3", "#FDB462", "#B3DE69", "#FCCDE5", "#D9D9D9", "#BC80BD", "#CCEBC5", "#FFED6F",
                       "#9ECAE1", "#3182BD", "#74C476", "#31A354", "#FD8D3C", "#E6550D", "#756BB1", "#54278F"]  # 图像颜色
        self.axs.set_ylim(0, 10)
        self.axs.set_xlim(0, 60)
        self.axs.text(-0.1, 1.05, f"(μV)", transform=self.axs.transAxes, fontsize=8, ha='left', va='top')
        self.axs.set_xlabel("Spectrum(Hz)", fontsize=12)
        self.flag_visible = 0 # 显示通道


        for i in range(self.num_channels + 1):
            line, = self.axs.plot(self.freq1, self.show[i], color=self.colors[i % 32], lw=1)
            self.lines.append(line)

        self.channel_visible(0)

    # 更新图像
    def update_animate(self):
        for i in range(self.num_channels + 1):
            self.lines[i].set_ydata(self.show[i])
        # 根据显示的频道获得最大值
        if self.flag_visible == 0:
            y_max = np.max(self.show)
        elif self.flag_visible == 1:
            y_max = np.max(self.show[self.num_channels])
        else:
            y_max = np.max(self.show[self.flag_visible - 2])

        # 设置 y 轴范围，留出一些边距
        margin = 0.1 * y_max  # 10% 的边距
        self.axs.set_ylim(0, y_max + margin)
        self.draw()
        self.flush_events()

    # 结束 退出线程
    def stop(self):
        # print("stop")
        self.is_updating = False
        if self.thread_update:
            self.thread_update.join()

    # 线程 循环更新图像
    def start_update(self):
        while self.is_updating:
            self.update_animate()
            time.sleep(0.2)

    # 更新y数据
    def update_y(self, data):
        self.data_eeg = np.hstack((self.data_eeg, data))
        len_data = len(self.data_eeg[0])
        self.y = self.data_eeg[:, -self.len:]

        fft_data = fft(self.y)
        fft_amp0 = np.array(np.abs(fft_data) / self.len / 2)
        self.fft_amp1 = fft_amp0[:, 0: int(self.len / 2)]
        # self.freq1 = self.samples * np.array(range(0, int(self.len / 2))) / self.len
        # 计算功率谱密度
        self.psd = np.abs(self.fft_amp1) ** 2
        # 计算平均值
        self.average = np.mean(self.psd, axis=0)
        self.psd = np.vstack((self.psd, self.average))
        # self.show = self.psd
        self.show = 10 * np.log10(self.psd)
        # self.show = [[10 * np.log10(self.psd) if t != 0 else 0 for t in channel] for channel in self.psd]
        self.data_eeg = self.data_eeg[:, len_data - self.len:]

    # 改变通道可见性 0 全可见  1: 平均可见 其他：仅序号数可见
    def channel_visible(self, id):
        self.flag_visible = id
        if id == 0:
            for i in range(self.num_channels):
                self.lines[i].set_visible(True)
        elif id == 1:
            for i in range(self.num_channels):
                self.lines[i].set_visible(False)
            self.lines[self.num_channels].set_visible(True)
        else:
            for i in range(self.num_channels + 1):
                if i == id - 2:
                    # print(i)
                    self.lines[i].set_visible(True)
                else:
                    self.lines[i].set_visible(False)
        self.draw()