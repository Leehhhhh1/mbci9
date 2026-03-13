import numpy as np
import pyqtgraph as pg
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QVBoxLayout


class EEGPlotWidget(QWidget):
    def __init__(self, num_channels, fs, seconds=5):  # fs降采样率
        super().__init__()

        self.num_channels = num_channels
        self.fs = fs
        self.seconds = seconds
        self.buffer_len = fs * seconds

        # 环形缓冲区
        self.data = np.zeros((num_channels, self.buffer_len))
        self.write_ptr = 0

        # PyQtGraph 设置
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        pg.setConfigOptions(antialias=False)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.plots = []
        self.curves = []

        # EEG_COLORS = [
        #     (31, 120, 180, 180),
        #     (51, 160, 44, 180),
        #     (227, 26, 28, 180),
        #     (255, 127, 0, 180),
        #     (106, 61, 154, 180),
        # ]
        channel_names = [
                "Fp1","Fp2",
                "F7","F3","Fz","F4","F8",
                "FC5","FC1","FC2","FC6",
                "T3","C3","Cz","C4","T4",
                "CP5","CP1","CP2","CP6",
                "P7","P3","Pz","P4","P8",
                "PO7","PO3","PO4","PO8",
                "O1","Oz","O2"
        ]


        self.pw = pg.PlotWidget()    # 创建画布
        self.layout.addWidget(self.pw)


        self.pw.showAxis('left')
        self.pw.showGrid(x=False, y=False)
        self.pw.setBackground((245,245,245))
        self.pw.setXRange(0, self.buffer_len)
        # self.pw.setYRange(-self.num_channels*120,120)
        self.curves = []
        self.ticks = []
        self.offset = 125
        self.pw.setYRange(
            -self.offset * (self.num_channels - 1) - self.offset,
            self.offset
        )
        self.pw.enableAutoRange(y=False)

        for ch in range(self.num_channels):
            # base_color = EEG_COLORS[ch % len(EEG_COLORS)]
            # alpha = 160 + (ch // len(EEG_COLORS)) * 20
            pen = pg.mkPen(color=(30,30,30),  width=1, cosmetic=True)
            curve = self.pw.plot(pen=pen)     # 保存曲线对象
            self.curves.append(curve)
            pos = -ch * self.offset
            label = channel_names[ch]
            self.ticks.append((pos,label))
        self.pw.getAxis('left').setTicks([self.ticks])
        self.pw.getAxis('left').setWidth(60)
        axis = self.pw.getAxis('left')
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        axis.setTickFont(font)

        # pw.hideAxis('bottom')
        # pw.showAxis('left')
        # pw.setLabel('left',f'{channel_names[ch]}', **{'font-size': '14pt'})
        # pw.getAxis('left').setStyle(showValues=False)
        # pw.getAxis('left').setWidth(50)
        #
        # base_color = EEG_COLORS[ch % len(EEG_COLORS)]
        # alpha = 160 + (ch // len(EEG_COLORS)) * 20
        # pen = pg.mkPen((*base_color[:3], min(alpha, 220)), width=1)
        # curve = pw.plot(pen=pen)     # 保存曲线对象
        # self.layout.addWidget(pw)   # 画布添加到布局
        #
        # self.plots.append(pw)
        # self.curves.append(curve)
        #
        # # 只给最后一个通道显示 x 轴
        # self.plots[-1].showAxis('bottom')

    def update_y(self, data):
        n = data.shape[1]

        if n >= self.buffer_len:
            self.data = data[:, -self.buffer_len:]
            self.write_ptr = 0
        else:
            end = self.write_ptr + n
            if end <= self.buffer_len:
                self.data[:, self.write_ptr:end] = data
            else:
                end = end % self.buffer_len
                first = self.buffer_len - self.write_ptr
                self.data[:, self.write_ptr:] = data[:, :first]
                self.data[:, :end] = data[:, first:]
            self.write_ptr = end

        # 连续时间轴
        display = np.roll(self.data, -self.write_ptr, axis=1)

        x = np.arange(self.buffer_len)

        max_val = np.max(np.abs(display))
        if max_val > 0:
            scale = (self.offset * 2) / max_val
        else:
            scale = 1
        # uv_per_div = 30
        # scale = 1 / uv_per_div

        for ch in range(self.num_channels):
            y = display[ch] * scale
            y = y - self.offset * ch
            self.curves[ch].setData(x, y)
