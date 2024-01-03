#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

PROGRAM      : RCA001_QT
DESPRIPITION : RCA001的GUI

AUTHOR       : YUCHEN LIN
CREATE DATE  : 2023.07.29
UPDATE DATE  : -
VERSION      : v1.0
UPDATE       :
    1. 

"""   

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys 

import yc_qt as ycqt
import RCA001_RCAD_adjust_col_tie as rca001

class main_window(ycqt.process_windows) :
    def __init__ (self, parent = None,
                  win_title = '自動順柱繫筋小幫手') :
        
        super(main_window, self).__init__(parent)
        
        self.setWindowTitle(win_title)
        self.thread = rca001.show_process() ## assign
    
        self.button_start.clicked.connect(self.slotStart)
        self.button_end.clicked.connect(self.close)
        
        self.initUI()

    def slotAdd(self, s) :
        self.text_edit.clear()
        self.text_edit.setPlainText(s)
        self.text_edit.moveCursor(QTextCursor.End)
        
    def slotStart(self) :        
        rca001.main()
    
    def initUI(self) :
        self.backend = rca001.show_process()
        self.backend.show_text.connect(self.slotAdd)
        self.backend.end_info.connect(self.show_end_msg)
        
        self.backend.start()
        
    def show_end_msg(self) :
        self.backend.end_info.disconnect(self.show_end_msg)
        QMessageBox.about(self,'自動順繫筋小幫手 完成!!!', '結束嘍!!!')
    
if __name__ == '__main__' :
    app = QApplication(sys.argv)
    
    win = main_window()
    win.show()
    
    sys.exit(app.exec_())