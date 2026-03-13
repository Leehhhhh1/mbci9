from PyQt5.QtWidgets import QWidget,QTextEdit,QLabel
from PyQt5.QtGui import QPixmap
from connection_multi_new3 import Trans
from threading import Thread


class ImpedanceWidget(QWidget):
    def __init__(self,trans):
        super().__init__()
        self.trans = trans
        self.eightchannels = ["Fp1", "Fp2", "C3", "C4", "T7", "T8", "O1", "O2"]  # 八导名称
        self.sum_channels_text = []  # 总通道数名称
        # self.impedance_test(1)
        self.trans.num_signal.connect(self.impedance_test)


    # def impedance_test(self,num):
    #     num_=num-1
    #     x_offset = 460 * (num_ % 4)           #x轴偏移量
    #     y_offset = 560 * (num_ // 4)          #y轴偏移量
    #     label = QLabel(self)
    #     pixmap = QPixmap('background.png')
    #     label.setPixmap(pixmap)
    #     label.setGeometry(x_offset,y_offset,pixmap.width(),pixmap.height())            #每行四个
    #     label.show()
    #
    #     for i in range(8):
    #         text = QTextEdit(self)
    #         text.setReadOnly(True)
    #         text.setFixedSize(75,56)
    #         text.setStyleSheet("font-size: 15px;background-color:rgba(255,0,0,250)")
    #         text.setText( "<div style='text-align: center;  font-family: Microsoft YaHei UI;'>" +
    #                              self.eightchannels[i] + '<br>>' + str(50) + 'kΩ</div>')
    #         self.positions = [
    #             (120, 95), (250, 95),  # Fp1, Fp2
    #             (100, 260), (300, 260),  # C3, C4
    #             (10, 260), (385, 260),  # T7, T8
    #             (105, 445), (275, 445),  # O1, O2
    #         ]
    #         x,y=self.positions[i]
    #         text.move(x+x_offset,y+y_offset)
    #         text.show()
    #         self.sum_channels_text.append(text)
    #
    #     self.setMinimumSize(460 * 4, 560 * ((num+3)//4))   # widget所需要的大小


