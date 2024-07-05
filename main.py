import typing
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QCheckBox
from PyQt5 import  uic
from PyQt5.QtCore import QThread
import sys

import yc_rcad as rd

from time import sleep

class main_window(QMainWindow) :
    def __init__(self) -> None:
        super().__init__()
        uic.loadUi('ui/main.ui', self)

        self.setWindowTitle('自動順柱繫筋小幫手 v2.2')

        self.pbtn_start = self.findChild(QPushButton, 'pbtn_start')
        self.pbtn_quit = self.findChild(QPushButton, 'pbtn_quit')
        self.cb_read_excel = self.findChild(QCheckBox, 'cb_read_excel')

        self.pbtn_start.clicked.connect(self.click_start)
        self.pbtn_quit.clicked.connect(self.close)
    
    def click_start(self) :
        
        self.main_program = Main(self.cb_read_excel.isChecked())
        self.main_program.started.connect(lambda: self.pbtn_start_change(True))
        self.main_program.finished.connect(lambda: self.pbtn_start_change(False))
        # sleep(2)

        self.main_program.start()

    def pbtn_start_change(self, isRunning) :
        if isRunning :
            self.pbtn_start.setText('Running...')
            self.pbtn_start.setEnabled(False)
        else :
            self.pbtn_start.setText('START !!')
            self.pbtn_start.setEnabled(True)

class Main(QThread) :
    def __init__(self, isReadExcel:bool) -> None:
        super().__init__()

        self.isReadExcel = isReadExcel
        print(f'Running {self.isReadExcel}')

    def run(self) :
        sleep(10)

    def read_rcad(self) :
        rcol = rd.rcol2019()
        new_msg_input('- 讀取柱配筋成功 (%s)' % rcol.rcol_filename)

        self.rcol = rcol

def new_msg_input(s) :
    #### Send to GUI and Print in console
    global isAddMsg
    
    global new_msg
    new_msg += (s + '\n')
    print(s)
    
    isAddMsg = True

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = main_window()
    window.show()
    app.exec_()