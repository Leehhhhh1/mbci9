import os
import queue
import sys
import time
from queue import Empty, Queue
import numpy as np
from socket import *
from PyQt5 import QtCore
from PyQt5.QtCore import QObject
from threading import Thread, Event
from preprocessing import preprocessing
from datetime import datetime


class TcpReceiver(Thread):  # 处理接受到的数据
    def __init__(self, client_socket, device_id, run, queue_save, queue_saveOld):
        super().__init__()
        self.client_socket = client_socket
        self.value = device_id
        self.queue_data = Queue()  # 线程安全的数据队列
        self.queue_save = queue_save
        self.queue_saveOld = queue_saveOld
        self.running = run
        self.head, self.byte_len, self.channel = 0xA0, 3, 32
        self.buffer = bytearray()
        self.frame_len = self.byte_len * self.channel + 3  # 一帧数据的字节长度

    def run(self):
        while self.running:
            try:
                info = self.client_socket.recv(8192)
                self.queue_saveOld.put(info)
                # print("recv info", type(info),len(info))
                if not info:
                    break
                data = self.return_data(info)
                # print("receiver data", type(data), len(data), len(data[1]))
                if data:
                    block = np.asarray(data)
                    # print("recv block", block.shape)
                    self.queue_data.put(block.T)  # 传递数据
                    self.queue_save.put(block)
            except Exception as e:
                print("Tcp_receiver run Error", e)

    def stop(self):
        self.running = False
        self.client_socket.shutdown(SHUT_RDWR)
        self.client_socket.close()

    def return_data(self, data):  # 解码
        self.buffer += data
        frames = []
        while self.running:
            frame = self.parse_frame()
            if frame is None:
                break
            frames.append(frame)
        return frames

    def parse_frame(self):
        try:
            idx = self.buffer.index(self.head)  # 取索引
        except ValueError:
            del self.buffer[:-1]  # 删除垃圾帧
            return None
        if idx > 0:
            del self.buffer[:idx]
        if len(self.buffer) < self.frame_len:
            return None
        raw_data = self.buffer[:self.frame_len]  # 返回一帧数据
        del self.buffer[:self.frame_len]  # 删除后继续处理下一帧
        return self.decode(raw_data)

    def decode(self, data):
        result = []
        interval = 2
        for i in range(self.channel):
            unit = data[interval: interval + self.byte_len]
            interval += self.byte_len
            decoded_num = (unit[0] << 16 | unit[1] << 8 | unit[2])
            if decoded_num & 0x800000:
                decoded_num -= 16777216
            result.append(decoded_num * 0.02235)
        return result


class TcpSend(Thread):  # 发送tcp请求
    def __init__(self, client_socket, queue_control, running):
        super().__init__(daemon=True)
        self.client_socket = client_socket
        self.queue_control = queue_control
        self.running = running

    def run(self):
        try:
            while self.running:
                if not self.queue_control.empty():
                    data = self.queue_control.get()
                    print(data)
                    self.client_socket.sendall(data.encode("utf-8"))

                else:
                    time.sleep(0.1)
                # data_1 = 'a'
                # print('发送的mark为：',data_1)
                # self.client_socket.sendall(data_1.encode("utf-8"))
        except Exception as e:
            print("Tcp_send Error", e)


class TcpSave(Thread):  # 保存数据
    def __init__(self, queue_save, running, start_event_EEG):
        super().__init__()
        self.start_event_EEG = start_event_EEG
        self.running = running
        self.queue_save = queue_save
        # self.queue_saveNew = queue_saveNew

    def run(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f'{timestamp}.txt', 'w', encoding="utf-8") as f1:
            while self.running:
                try:
                    data = self.queue_save.get(timeout=0.5)
                    # data_1 = self.queue_saveNew.get(timeout = 0.5)
                    # f1.write(data_1)
                    np.savetxt(f1, data, fmt='%.2f')
                except Empty:
                    continue
                except Exception as e:
                    print("Tcp_save Error:", e)


class TcpSaveOld(Thread):  # 保存数据
    def __init__(self, queue_saveOld, running, start_event_EEG):
        super().__init__()
        self.start_event_EEG = start_event_EEG
        self.running = running
        self.queue_saveOld = queue_saveOld

    def run(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f'{timestamp}_bin.bin', 'ab') as f1:
            while self.running:
                try:
                    data_1 = self.queue_saveOld.get(timeout=0.5)
                    f1.write(data_1)
                except Empty:
                    continue
                except Exception as e:
                    print("Tcp_saveOld Error:", e)


class UdpSend(Thread):
    def __init__(self, ip, port, running, start_event, trigger_queue):
        super().__init__()
        self.udp_client_socket = None
        self.start_event = start_event
        self.ip = ip
        self.port = port
        self.running = running
        self.trigger_queue = trigger_queue

    def run(self):
        self.udp_client_socket = socket(AF_INET, SOCK_DGRAM)
        self.udp_client_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        try:
            # sys.stdin = os.fdopen(0, "r")  # 打开标准输入流
            # ser = serial.Serial('COM9', 9600)  # 根据实际串口号修改，如 COM1，COM2，或 /dev/ttyUSB0 等
            while self.running:
                if self.start_event.is_set():
                    # if ser.in_waiting > 0:  # 检查是否有数据可读
                    #     num = ser.read(1).decode('utf-8').strip()
                    if not self.trigger_queue.empty():
                        num = self.trigger_queue.get()
                        print("发送的mark数据是:", num)
                        self.udp_client_socket.sendto(num.encode('utf-8'), (self.ip, self.port))
                        # if self.queue_control:
                        #     switch_data = self.queue_control.get()
                        #     print("switch_data:",switch_data)
                        #     client_socket.sendto(switch_data.encode('utf-8'), (self.ip, self.port))
                        #     if switch_data == '!' or switch_data == '@':
                        #         start_ = 'b'
                        #         client_socket.sendto(start_.encode('utf-8'), (self.ip, self.port))
                        # time.sleep(1)
                        # start_data='a'
                        # Client_socket.sendto(start_data.encode('utf-8'), (self.ip, self.port))
                        # start_data='s'
                        # Client_socket.sendto(start_data.encode('utf-8'), (self.ip, self.port))

                time.sleep(0.001)
        except Exception as e:
            print('Udp_send error:', e)
            self.udp_client_socket.close()

    def stop(self):
        try:
            sys.stdin.close()
        except Exception as e:
            pass
        if self.udp_client_socket:
            self.udp_client_socket.close()


class Trans(QObject):
    connected_signal = QtCore.pyqtSignal(str)
    animate_signal = QtCore.pyqtSignal(object)
    impedance_signal = QtCore.pyqtSignal(object)
    num_signal = QtCore.pyqtSignal(int)

    ip = '192.168.0.255'  # udp连接板子的ip
    port = 8087  # udp连接板子的端口号
    ip_port = ('', 8086)  # 本机的地址
    start_event_EEG = Event()
    start_event = Event()

    def __init__(self):
        super().__init__()

        self.sample, self.downsample = 250, 1
        self.receive, self.udp_thread, self.sender = None, None, None
        self.Server_socket, self.client_socket = None, None
        self.threads = {}

        self.queue_connect = Queue()  # 返回连接信息
        self.queue_control = Queue()  # 获得控制信息
        self.multi_num = Queue()  # 传递设备连接次序
        self.queue_save = Queue()
        self.save_old = Queue()
        self.trigger_queue = Queue() #发送trigger信息

        self.impedance_flag = False
        self.run_flag = True
        self.id = 0
        self.value = 1
        self.connect_flag = True
        self.num_channels = 32
        self.data_preprocess_eeg = np.zeros((self.num_channels, 2500))

    def tcp_transmission(self):  # 创建tcp连接
        self.Server_socket = socket(AF_INET, SOCK_STREAM)
        self.Server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.Server_socket.bind(self.ip_port)
        self.Server_socket.listen(128)
        print('listening...')
        self.queue_connect.put('\nlistening...')
        # while self.connect_flag:
        self.client_socket, addr = self.Server_socket.accept()
        # print(f'\n已连接第{self.value}台设备,{addr}')
        self.queue_connect.put(f'\n已连接第{self.value}台设备,{addr}')
        # self.multi_num.put(self.value)
        self.num_signal.emit(self.value)
        self.receive = TcpReceiver(self.client_socket, self.value, self.running, self.queue_save, self.save_old)
        self.receive.daemon = True
        self.receive.start()
        self.sender = TcpSend(self.client_socket, self.queue_control, self.running)
        self.sender.daemon = True
        self.sender.start()
        self.threads[self.value] = (self.receive, self.sender)

        # self.value += 1                     #value-1 为连接个数

    def check_connect(self):  # 传递连接信息
        while self.running:
            if not self.queue_connect.empty():
                try:
                    data = self.queue_connect.get(timeout=0.5)
                    self.connected_signal.emit(data)
                except Empty:
                    continue
                except Exception as e:
                    print("check connect error:", e)
            time.sleep(0.1)


    def check_data(self):  # 传递数据流信息
        while self.running:
            if not self.impedance_flag:  # 波形显示
                if self.start_event_EEG.is_set():  # 开始波形检测标志
                    # if self.flag:                  #实时波形检测
                    try:
                        id_ = self.id + 1
                        data = self.threads[id_][0].queue_data.get(timeout=0.5)
                        # print("recv check_data", type(data), data.shape)
                        self.data_preprocess_eeg = np.concatenate((self.data_preprocess_eeg, data),
                                                                  axis=1)  # 拼接数据 axis=1 为横向拼接 ； axis=0 为纵向拼接
                        self.data_preprocess_eeg = self.data_preprocess_eeg[:, -2000:]
                        data_preprocessed = preprocessing(self.data_preprocess_eeg, self.num_channels, self.sample, self.downsample)
                        print(f"采样率为:{self.sample},降采样比例为：{self.downsample}")
                        data_preprocessed = np.round(data_preprocessed, 2)[:, 375: -375]  # 保留 2 位小数的四舍五入
                        self.animate_signal.emit(data_preprocessed)
                    except (EOFError, BrokenPipeError):
                        print("check_data EEG: queue closed, exit thread")
                        break
                    except queue.Empty:
                        continue
                    except Exception as e:
                        print("check_data EEG Error", e)
                else:
                    time.sleep(0.05)
            else:  # 阻抗检测
                try:
                    value = self.value - 1  # 实际连接个数
                    all_data = []
                    for i in range(value):
                        id_ = i + 1
                        data = self.threads[id_][0].queue_data.get(timeout=0.5)[:, -self.sample:]
                        all_data.append(data)
                        # print(f"[DEBUG] Received data shape: {id_}+{data.shape}")
                    self.data_preprocess = np.concatenate(all_data, axis=0)
                    # print(f"[DEBUG] Received data shape: {self.data_preprocess.shape}")
                    # self.data_preprocess = self.data_preprocess[:, -2500:]
                    self.impedance_signal.emit(self.data_preprocess)
                except (EOFError, BrokenPipeError):
                    print("check_data impedance: queue closed, exit thread")
                    break
                except Exception as e:
                    print("check_data impedance Error", e)

    # def udp_transmission(self):    #发送udp信号
    #     Client_socket = socket(AF_INET, SOCK_DGRAM)
    #     Client_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    #     try:
    #         sys.stdin = os.fdopen(0, "r")  # 打开标准输入流
    #         # ser = serial.Serial('COM9', 9600)  # 根据实际串口号修改，如 COM1，COM2，或 /dev/ttyUSB0 等
    #         while self.running:
    #             if self.start_event.is_set():
    #                 # if ser.in_waiting > 0:  # 检查是否有数据可读
    #                     # num = ser.read(1).decode('utf-8').strip()
    #                 num = input("请输入: ")
    #                 print("接收到的数据:", num)
    #                 Client_socket.sendto(num.encode('utf-8'), (self.ip, self.port))
    #                 if self.queue_control:
    #                     switch_data=self.queue_control.get()
    #                     print(switch_data)
    #                     Client_socket.sendto(switch_data.encode('utf-8'), (self.ip, self.port))
    #                     if switch_data =='!' or switch_data == '@':
    #                         start_='b'
    #                         Client_socket.sendto(start_.encode('utf-8'), (self.ip, self.port))
    # time.sleep(1)
    # start_data='a'
    # Client_socket.sendto(start_data.encode('utf-8'), (self.ip, self.port))
    # start_data='s'
    # Client_socket.sendto(start_data.encode('utf-8'), (self.ip, self.port))

    #         time.sleep(0.1)
    # except Exception as e:
    #     print(f'\n---控制端关闭---{e}')
    #     Client_socket.close()

    def start_connect(self):  # 启动连接
        self.running = True

        Thread(target=self.check_connect, daemon=True).start()
        Thread(target=self.tcp_transmission, daemon=True).start()

    def data_save(self):  # 保存数据
        self.running = True

        save_thread = TcpSave(self.queue_save, self.running, self.start_event_EEG)
        save_thread.start()

        save_threadOld = TcpSaveOld(self.save_old, self.running, self.start_event_EEG)
        save_threadOld.start()

    def udp(self):  # Udp控制
        self.running = True
        self.udp_thread = UdpSend(self.ip, self.port, self.running, self.start_event, self.trigger_queue)
        self.udp_thread.daemon = True
        self.udp_thread.start()

    def start(self):  # 数据流传输
        self.running = True

        # udp_=Thread(target=self.udp_transmission)
        # udp_.daemon=True
        # udp_.start()
        Thread(target=self.check_data, daemon=True).start()

    def stop_all(self):  # 安全退出
        self.start_event.clear()
        self.start_event_EEG.clear()
        try:
            self.queue_control.put('S')
        except Exception as e:
            pass
        for id, (recv, send) in self.threads.items():
            try:
                recv.stop()
            except Exception as e:
                print(f"[Trans] stop receiver {id} error:", e)
        self.threads.clear()
        try:
            if hasattr(self, "Server_socket"):
                self.Server_socket.close()
            if hasattr(self, "udp_thread"):
                self.udp_thread.stop()
        except Exception:
            pass

    def sample_change(self, trigger):
        if trigger == '1':
            self.sample = 250
            self.downsample = 1
        elif trigger == '2':
            self.sample = 500
            self.downsample = 2
        elif trigger == '3':
            self.sample = 1000
            self.downsample = 4
        self.trigger_queue.put(trigger)
