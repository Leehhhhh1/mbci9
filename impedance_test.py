from PyQt5.QtWidgets import QWidget,QTextEdit,QLabel
from PyQt5.QtGui import QPixmap
from connection_multi_new3 import Trans
from threading import Thread
from ui_impedance import Ui_Impedance


class ImpedanceWidget(QWidget,Ui_Impedance):
    def __init__(self,trans):
        super().__init__()
        self.setupUi(self)
        self.trans = trans
        self.channels = [self.FP1, self.FP2, self.F7, self.F8, self.F3, self.F4, self.Fz, self.FC5,
                        self.FC1,self.FC2,self.FC6,self.T3,self.C3,self.Cz,self.C4,self.T4,
                        self.CP5,self.CP1,self.CP2,self.CP6,self.P7,self.P3,self.Pz,self.P4,
                        self.P8,self.PO7,self.PO3,self.PO4,self.PO8,self.O1,self.Oz,self.O2
                        ]  # 32导名称
        self.channels_names = [
            'FP1', 'FP2', 'F7', 'F8', 'F3', 'F4', 'Fz', 'FC5',
            'FC1', 'FC2', 'FC6', 'T3', 'C3', 'Cz', 'C4', 'T4',
            'CP5', 'CP1', 'CP2', 'CP6', 'P7', 'P3', 'Pz', 'P4',
            'P8', 'PO7', 'PO3', 'PO4', 'PO8', 'O1', 'Oz', 'O2'
        ]
        # self.impedance_test(1)
        # self.trans.num_signal.connect(self.impedance_test)





