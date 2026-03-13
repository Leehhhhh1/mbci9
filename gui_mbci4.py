import sys

import PyQt5.QtGui as QtGui
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QScrollArea, QComboBox, QVBoxLayout, QWidget
from PyQt5.QtGui import QColor
from ui_mbci3 import Ui_MainWindow
from ui_filter import Ui_Filter
from impedance_test import ImpedanceWidget
from animate4 import Animation_EEG, Animation_Spectrogram
from connection_multi_new3 import  Trans
import preprocessing
import parameter
from eeg_plot import EEGPlotWidget
import numpy as np
import time


# pyuic5 -o ui_mbci.py ui_mbci.ui
# self.pushButton_switch.clicked.connect(MainWindow.start_data_stream)

class MainWindow(QMainWindow, Ui_MainWindow):
    trigger = QtCore.pyqtSignal(str)
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.resize(2000, 1000)

        self.num_connection = 0 # 当前连接数
        self.flag_transmit = True # 传输状态 True：start False：stop
        self.flag_impedance = True # 阻抗状态 True: start False: stop
        self.flag = True

        self.num_channels = 32  # 通道数
        self.samples = 250 # 采样率
        self.downsamples = 250 # 降采样率
        self.trans = Trans()
        # self.udp = UdpSend()
        '''
            脑电图显示
        '''
        # 左侧脑电图
        self.eeg_widget = EEGPlotWidget(num_channels=self.num_channels,fs=self.downsamples)

        # 创建滑条窗口
        # self.scroll_EEG = QScrollArea()
        self.scroll_EEG.setWidget(self.eeg_widget)
        self.vertical_bar = self.scroll_EEG.verticalScrollBar()
        self.vertical_bar.setValue(120)
        self.scroll_EEG.setWidgetResizable(True)
        self.lineEdit.returnPressed.connect(self.handle_input)

        #创建阻抗检测模块
        # self.impedancewidget = ImpedanceWidget(self.trans)
        # self.scrollArea_impedance.setWidget(self.impedancewidget)
        # self.scrollArea_impedance.setWidgetResizable(True)


        # 右侧频谱图
        # 创建下拉菜单 (QComboBox)
        self.combobox_channel.addItem("ALL Channels")
        for i in range(1, self.num_channels + 1):
            self.combobox_channel.addItem("Channel " + str(i))
        self.combobox_channel.currentIndexChanged.connect(self.channel_change)

        # 创建一个垂直布局，先添加下拉菜单，再添加 spectrogram
        # self.layout = QVBoxLayout()
        # self.layout.addWidget(self.combobox_channel)  # 添加下拉菜单到布局
        # 创建频谱图
        self.animation_spectrogram = Animation_Spectrogram(width=3, height=2, dpi=100, num_channels=self.num_channels,
                                                           samples=self.samples)
        self.verticalLayout_spectrogram.addWidget(self.animation_spectrogram)


        '''
            槽函数设置
        '''
        # 创建数据传输的连接进程

        self.trans.connected_signal.connect(self.append_output)
        self.trans.animate_signal.connect(self.update_animate)
        self.trans.impedance_signal.connect(self.update_impedance)
        # self.trans.num_singal.connect(self.multi_num)

        self.trigger.connect(self.trans.sample_change)


        # 页面切换时给出提示
        # 按钮槽函数
        self.pushButton_switch.clicked.connect(self.start_data_stream)
        self.pushButton_filter.clicked.connect(self.open_filter)
        self.pushButton_start.clicked.connect(self.start_impedance)
        self.pushButton_start.clicked.connect(self.update_impedance)

        self.trans.start()
        self.trans.start_connect()
        self.trans.data_save()
        self.trans.udp()
    # 设置波形图下拉菜单（多连接使用）
    # def multi_num(self,num):
    #     self.multi_comboBox.currentIndexChanged.connect(self.multi_channel_change)
    #     self.multi_comboBox.addItem("设备 " + str(num))
        # self.impedancetest.impedance_test(num)


    # 结束
    def closeEvent(self, event):
        try:
            if hasattr(self,"trans"):
                self.trans.stop_all()

            if hasattr(self, "animation_spectrogram"):
                self.animation_spectrogram.deleteLater()

            if hasattr(self, "eeg_widget"):
                self.eeg_widget.deleteLater()
        except Exception as e:
            print("closeEvent",e)

    # trigger发送
    def handle_input(self):
        text = self.lineEdit.text()
        self.lineEdit.clear()
        self.plainTextEdit_connect.appendPlainText(f"发送的Trigger：{text}")
        self.trigger.emit(text)
        # self.trigger.connect(self.udp)

    # 显示连接（多连接使用）
    def append_output(self, message):
        self.label.setText(f"当前连接数: {self.trans.value-1}")
        # self.num_connection = self.num_connection + 1
        self.plainTextEdit_connect.appendPlainText(message)

    def connect_finished(self):
        self.trans.queue_connect.put('开始通信！')
        self.trans.start_event_EEG.set()
        self.trans.start_event.set()
        # self.trans.flag=True

    def impedance_start(self):
        self.trans.queue_connect.put('开始阻抗检测！')
        self.trans.start_event.set()
        self.trans.impedance_flag = True

    # 数据传输按钮槽函数
    def start_data_stream(self):
        try:
            if self.flag_transmit:
                self.trans.queue_control.put('@')
                self.trans.queue_control.put('B')
                self.connect_finished()
                self.pushButton_switch.setText("停止数据传输")
            else:
                self.pushButton_switch.setText("开始数据传输")
                self.trans.queue_control.put('S')
            self.flag_transmit = not self.flag_transmit
        except Exception as e:
            print("start_data_stream Error", e)

    # 打开filter界面槽函数
    def open_filter(self):
        self.window_filter = Window_filter()
        self.window_filter.show()

    # 更新动画 animate_signal信号槽函数
    def update_animate(self, data):
        self.eeg_widget.update_y(data)
        self.animation_spectrogram.update_y(data)
        # time.sleep(0.05)

    # 更换频谱可见通道
    def channel_change(self, id):
        self.animation_spectrogram.channel_visible(id)

    #更新波形通道
    # def multi_channel_change(self,id):
    #     self.trans.id=id
    #     # 只有在数据传输暂停时才手动显示缓存波形
    #     if not self.flag:
    #         thread_id = id + 1
    #         receiver = self.trans.threads.get(thread_id)
    #         data = receiver.latest_data
    #         if data is not None :
    #             try:
    #                 # 清理并更新缓存（防止数据重叠）
    #                 self.trans.data_preprocess_eeg = np.concatenate((self.trans.data_preprocess_eeg, data), axis=1)
    #                 self.trans.data_preprocess_eeg = self.trans.data_preprocess_eeg[:, -2000:]
    #                 # 预处理波形数据
    #                 data_preprocessed = preprocessing(self.trans.data_preprocess_eeg,self.trans.num_channels,self.trans.sample,1)
    #                 data_preprocessed = np.round(data_preprocessed, 2)[:, 375:-375]
    #                 # 发射信号更新波形图
    #                 self.animation_eeg.update_y(data_preprocessed)
    #                 self.animation_eeg.update_animate()
    #                 self.animation_spectrogram.update_y(data_preprocessed)
    #                 self.animation_spectrogram.update_animate()
    #
    #             except Exception as e:
    #                 print(f"[设备切换绘图错误] {e}")


    # 开始阻抗检测
    def start_impedance(self):
        try:
            if self.flag_impedance:
                self.flag = True
                self.trans.queue_control.put('!')
                self.impedance_start()
                self.pushButton_start.setText("停止")

            else:
                self.flag = False
                self.pushButton_start.setText("开始")
                self.trans.queue_control.put('s')
                self.trans.impedance_flag = False
            self.flag_impedance = not self.flag_impedance
        except Exception as e:
            print("start_impedance",e)

    # 更新阻抗值
    def update_impedance(self, data):
        try:
            if not self.flag_impedance:
                self.sum_channels = self.num_channels * self.trans.value   # 总通道数
                self.eeg_impedence = np.zeros((self.sum_channels, self.downsamples * 10))
                self.eeg_impedence = np.hstack((self.eeg_impedence, data))
                self.eeg_impedence = self.eeg_impedence[:, -self.downsamples * 10:]
                impedance = preprocessing.get_impedance(self.eeg_impedence)
                for id in range(self.sum_channels):
                    self.impedancewidget.sum_channels_text[id].setText(
                        "<div style='text-align: center; font-size: 10pt; font-family: Microsoft YaHei UI;'>" +
                        self.impedancewidget.eightchannels[id%8] + '<br>' + '{:.2f}'.format(impedance[id]) + 'KΩ</div>')
                    if impedance[id] > parameter.impedance_max:
                        color = QColor(220, 20, 60)
                    elif impedance[id] < parameter.impedance_min:
                        color = QColor(50, 205, 50)
                    else:
                        color = QColor(255, 140, 0)
                    self.impedancewidget.sum_channels_text[id].setStyleSheet(f"background-color: {color.name()};")
                    id += 1
        except Exception as e:
            # print(2)
            # print(f"[DEBUG] Received data shape: {data.shape}")
            print("update_impedance",e)


# 创建滤波器窗口
class Window_filter(QWidget, Ui_Filter):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.spinBox_low.setValue(parameter.low_cutoff)
        self.spinBox_high.setValue(parameter.high_cutoff)
        self.spinBox_notch_freq.setValue(parameter.notch_freq)

        self.pushButton_Confirm.clicked.connect(self.confirmFilter)
        self.pushButton_Cancel.clicked.connect(self.cancelFilter)
        self.pushButton_Reset.clicked.connect(self.resetFilter)

    # 确认滤波器参数修改
    def confirmFilter(self):
        parameter.low_cutoff = int(self.spinBox_low.text())
        parameter.high_cutoff = int(self.spinBox_high.text())
        parameter.notch_freq = int(self.spinBox_notch_freq.text())

    # 重设滤波器参数修改
    def resetFilter(self):
        self.spinBox_low.setValue(parameter.low_cutoff)
        self.spinBox_high.setValue(parameter.high_cutoff)
        self.spinBox_notch_freq.setValue(parameter.notch_freq)

    # 关闭窗口
    def cancelFilter(self):
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
