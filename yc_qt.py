#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

PROGRAM      : YC_QT
DESPRIPITION : 定義常用 pyqt5  物件 及 函數

AUTHOR       : YUCHEN LIN
CREATE DATE  : 2023.07.28
UPDATE DATE  : -
VERSION      : v1.0
UPDATE       :
    1. 

"""    

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys     

class process_windows(QWidget) :
    def __init__ (self, parent = None,
                  win_title = 'Process Windows') :
        
        super(process_windows, self).__init__(parent)
        
        self.setWindowTitle(win_title)
        # self.list_file = QListWidget()
        # self.input = QLineEdit(self)
        self.text_edit = QTextEdit()
        self.button_start = QPushButton('START !!')
        self.button_end = QPushButton('QUIT')
        
        self.layout = QGridLayout(self)
        # self.layout.addWidget(self.list_file, 0, 0, 1, 2)
        # self.layout.addWidget(self.input, 0, 0, 1, 2)
        
        self.layout.addWidget(self.text_edit, 0, 0, 1, 2)
        self.layout.addWidget(self.button_start, 1, 1)
        self.layout.addWidget(self.button_end, 1, 0)
        
        self.text_edit.setReadOnly(True)
        
        # self.button_start.clicked.connect(self.slotStart)
        # self.thread.signal_out.connect(self.slotAdd)

    # def slotAdd(self, s) :
    #     self.listFile.addItem(s)
        
    # def slotStart(self) :
    #     self.button_start.setEnabled(False)
    #     self.thread.start()
        
if __name__ == '__main__' :
    app = QApplication(sys.argv)
    
    win = process_windows()
    win.show()
    
    sys.exit(app.exec_())