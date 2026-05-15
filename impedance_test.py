import sys
from pathlib import Path

from PyQt5 import QtCore
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel, QWidget

from ui_impedance import Ui_Impedance


def resource_path(relative_path):
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return str(base_path / relative_path)


class ImpedanceWidget(QWidget, Ui_Impedance):
    def __init__(self, trans):
        super().__init__()
        self.setupUi(self)
        self.trans = trans
        self.channels = [
            self.FP1, self.FP2, self.F7, self.F8, self.F3, self.F4, self.Fz, self.FC5,
            self.FC1, self.FC2, self.FC6, self.T3, self.C3, self.Cz, self.C4, self.T4,
            self.CP5, self.CP1, self.CP2, self.CP6, self.P7, self.P3, self.Pz, self.P4,
            self.P8, self.PO7, self.PO3, self.PO4, self.PO8, self.O1, self.Oz, self.O2,
        ]
        self.channels_names = [
            'FP1', 'FP2', 'F7', 'F8', 'F3', 'F4', 'Fz', 'FC5',
            'FC1', 'FC2', 'FC6', 'T3', 'C3', 'Cz', 'C4', 'T4',
            'CP5', 'CP1', 'CP2', 'CP6', 'P7', 'P3', 'Pz', 'P4',
            'P8', 'PO7', 'PO3', 'PO4', 'PO8', 'O1', 'Oz', 'O2',
        ]
        self._setup_background()
        # self.impedance_test(1)
        # self.trans.num_signal.connect(self.impedance_test)

    def _setup_background(self):
        pixmap = QPixmap(resource_path("background2.jpg"))
        self.background_label = QLabel(self)
        self.background_label.setGeometry(QtCore.QRect(60, 40, 760, 806))
        self.background_label.setAlignment(QtCore.Qt.AlignCenter)
        self.background_label.setPixmap(
            pixmap.scaled(
                self.background_label.size(),
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation,
            )
        )
        self.background_label.lower()
        for channel in self.channels:
            channel.raise_()
