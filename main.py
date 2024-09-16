from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QCheckBox, QTextEdit, QMessageBox
from PyQt5 import  uic
from PyQt5.QtCore import QThread, pyqtSignal, QObject
from PyQt5.QtGui import QTextCursor

import sys, os, math

import pandas as pd
import numpy as np

import yc_rcad as rd

# from time import sleep


class MsgSignal(QObject):
    new_msg = pyqtSignal(str)

msg_signal = MsgSignal()

# thread = QThread()

class main_window(QMainWindow) :
    def __init__(self) -> None:
        super().__init__()

        # LOADING UI FILE
        uic.loadUi('ui/main.ui', self)
        self.setWindowTitle('自動順柱繫筋小幫手 v2.2')

        # DEFINE UI OBJECTS WHICH WILL BE USED
        self.pbtn_start = self.findChild(QPushButton, 'pbtn_start')
        self.pbtn_quit = self.findChild(QPushButton, 'pbtn_quit')
        self.cb_read_excel = self.findChild(QCheckBox, 'cb_read_excel')
        self.te_show_msg = self.findChild(QTextEdit, 'te_show_msg')

        # INITIALIZE MAIN PROGRAM
        self.main_program = Main(self.cb_read_excel.isChecked())

        # CONNECTION ZONE
        self.pbtn_start.clicked.connect(self.click_start)
        self.pbtn_quit.clicked.connect(self.close)
        self.main_program.started.connect(lambda: self.pbtn_start_change(True))
        self.main_program.finished.connect(lambda: self.pbtn_start_change(False))
        msg_signal.new_msg.connect(self.update_screen)
    
    def click_start(self) :
        self.main_program.set_is_read_excel(self.cb_read_excel.isChecked())
        self.main_program.start()

    def pbtn_start_change(self, isRunning) :
        if isRunning :
            self.pbtn_start.setText('Running...')
        else :
            self.pbtn_start.setText('START !!')
            QMessageBox.about(self,'自動順繫筋小幫手 完成!!!', '結束嘍!!!')

        self.pbtn_start.setEnabled(not(isRunning))

    def update_screen(self, msg) :
        # self.te_info.clear()
        self.te_show_msg.setPlainText(msg)
        self.te_show_msg.moveCursor(QTextCursor.End)
        # cur = self.te_show_msg.textCursor()
        # cur.movePosition(QTextCursor.End)


class Main(QThread) :
    # INITIALIZE
    def __init__(self, isReadExcel:bool) -> None:
        self.msg = ''
        # self.is_new_msg = False

        super().__init__()

        self.isReadExcel = isReadExcel
        self.checkAixalForceControl = False

        # self.fid = open('log.txt', 'w')

    # MAIN PROCEDURE
    def run(self) :
        # START LOG EMPTY FILE
        with open('log.txt', 'w') as f :
            f.write('')

        # 1st Step : Read RCAD File
        self.read_rcad()
        # 2nd Step : Read Excel File
        self.read_excel()
        # 3rd Step : Check Tie Demand
        self.tie_demand_check()
        # 4th Step : Start Check the Rules
        self.adjust_tie()
        # 5th Step : Column in B1F Should Be All Tie
        self.adjust_B1F_col_tie()
        # 6th Step : Updating RCAD and Output
        self.add_msg('- 更新柱配筋 ...')
        self.rcol.rcol_db = self.dbs
        
        self.add_msg('- 輸出順繫筋的tmp檔 ...')
        self.rcol.output_rcol()

    # ADD MESSAGE TO SCREEN
    def add_msg(self, msg) :
        self.msg += msg + '\n'
        print(msg)

        msg_signal.new_msg.emit(self.msg)

        with open('log.txt', 'a') as f :
            f.write(msg + '\n')

    # SET SHOULD BE READ EXCEL OR NOT
    def set_is_read_excel(self, isReadExcel) :
        self.isReadExcel = isReadExcel

    # READING RCAD FILE
    def read_rcad(self) :
        rcol = rd.rcol2019()
        self.add_msg('- 讀取柱配筋成功 (%s)' % rcol.rcol_filename)

        self.rcol = rcol

        self.dbs = rcol.rcol_db
        self.blocks = rcol.rcol_blocks

    # READING EXCEL FILE
    def read_excel(self) :
        if self.isReadExcel :
            for tmp in os.listdir() :
                if 'RCAD柱調整' in tmp :
                    col_excel = tmp
                    break
                        
            try :
                self.add_msg('- 讀取柱excel中... (%s)' % col_excel)
                tie_demand, stir = self.read_tie_demand(os.path.join(os.getcwd(),col_excel))
                self.add_msg('- 讀取柱excel成功 (%s)' % col_excel)
            except :
                self.add_msg('- 讀取柱excel失敗!!! 請確認是否有放進資料夾 !!!')
                ErroMsgBox('讀取柱excel失敗!!! 請確認是否有放進資料夾 !!!')
         
                tie_demand = None
                stir = None
            
            try :
                isPuControl = self.read_checkPuControl(os.path.join(os.getcwd(),col_excel))
                self.checkAixalForceControl = True
            except :
                isPuControl = None

        else :
            self.add_msg('- 未讀取柱excel!!!')
            tie_demand = None
            stir = None
        
        self.tie_demand = tie_demand
        self.stir = stir
        self.isPuControl = isPuControl

    # READ TIE DEMAND
    def read_tie_demand(self, file) :
        df = pd.read_excel(file, sheet_name = 'RCA001', engine="openpyxl")

        tie_demand = {}
        stir = {}

        for row in range(len(df)) :
            if not np.isnan(df['nx'][row]) :
                tie_demand[df['Flr.Col.'][row]] = [int(df['nx'][row]), int(df['ny'][row])]
                stir[df['Flr.Col.'][row]] = [df['stir#'][row], int(df['spacing'][row])]
                
        return tie_demand, stir
    
    def read_checkPuControl(self, file) :
        df = pd.read_excel(file, sheet_name = 'RCA001', engine="openpyxl")

        isPuControl = {}

        for row in range(len(df)) :
            if not np.isnan(df['nx'][row]) :
                isPuControl[df['Flr.Col.'][row]] = df["Pu>0.3fc'Ag"][row]
                
        return isPuControl

    # CHECK TIE DEMAND
    def tie_demand_check(self) :
        dbs = self.dbs
        tie_demand = self.tie_demand
        stirs = self.stir

        if tie_demand == None :
            self.add_msg('\n- 未讀Excel，目前配置作為最小繫筋量 ...')
            return None

        else :
            self.add_msg('\n- 確認最小繫筋量 ...')
        
        for db in dbs :
            idb = db
            col_name = db['col_name']
            
            try :
                nxy = tie_demand[col_name]
                stir = stirs[col_name]
            except :
                self.add_msg('-- 最小繫筋讀取未成功 !!!! (%s)' % col_name)
                continue
            
            isTieFull = False
            if self.checkAixalForceControl :
                if self.isPuControl[col_name] == 'Yes' :
                    self.add_msg(f'--- 軸力控制滿箍 ({col_name})')
                    isTieFull = True
            
            ties = list(db['tie'])
            rebar = db['rebar'][1]
            
            dir = ['X', 'Y']
            
            for n in range(2) :
                tie_n = ties[n]
                
                if isTieFull :
                    nn = max(len(rebar[n])-2, nxy[n])
                else :
                    nn = nxy[n]
                
                # Tie Between per 2 rebar
                if tie_n < math.floor((len(rebar[n])-2)/2) :
                    ties[n] = math.floor((len(rebar[n])-2)/2)
                    
                    rebar[n] = rd.modify_tie(rebar[n], ties[n])
                    
                    self.add_msg(f'--- 隔根箍調整!!!!! {col_name}, {dir[n]}向)')
                
                # Tie number excceeds the number of rebar
                if nn > tie_n : 
                    ties[n] = nn
                    if nn > (len(rebar[n])-2) :
                        self.add_msg(f'------ 柱筋不夠排 請CHECK!!!!! {col_name}, {dir[n]}向)')
                    rebar[n] = rd.modify_tie(rebar[n], nn)

            db['tie'] = tuple(ties)
            db['rebar'][1] = rebar
            
            istir = (stir[0], stir[1])
            db_stir = []
            for i in range(3) :
                db_stir.append(istir)

            db['stirrup'] = db_stir

            dbs[dbs.index(idb)] = db    
            
        self.dbs = dbs

    def adjust_tie(self) :
        self.add_msg('\n- 開始順繫筋 ...')
        blocks = self.blocks
        dbs = self.dbs

        for ii in range(len(blocks)) :
            block = blocks[ii]
            col_name = block[0].split('"')[1]
            self.add_msg(f'\n--  順柱 {col_name} ')
            
            block1 = block[2:7]
            story1 = block1[0].split()[0]
            db1 = dbs[find_db_pos(dbs, story1+col_name)]

            db1 = self.least_1_tie(db1)
            
            for i in range(7, len(block), 5) :
                block2 = block[i:i+5]
                story2 = block2[0].split()[0]
                db2 = dbs[find_db_pos(dbs, story2+col_name)]
                
                tie1 = list(db1['tie'])
                tie2 = list(db2['tie'])
                
                stirNo1 = db1['stirrup'][0][0]
                stirNo2 = db2['stirrup'][0][0]

                width1, height1 = db1['section']
                width, height = db2['section']
                rebar1 = sum(db1['rebar'][0])
                rebar2 = sum(db2['rebar'][0])

                dir = ['X', 'Y']

                #### Check No. of tie of below story is not less than one of upper story
                if stirNo1 != stirNo2 :
                    self.add_msg(f'--- {db2["col_name"]} 箍筋號數不同，不順繫筋')
                elif f'{width1}x{height1}' != f'{width}x{height}' :
                    self.add_msg(f'--- {db2["col_name"]} 與上層斷面不同，不順繫筋')
                elif rebar1 > rebar2 :
                    self.add_msg(f'--- {db2["col_name"]} 比上層鋼筋支數少，不順繫筋')
                else :
                    for j in range(2) :
                        if tie2[j] < tie1[j] :
                            rebar = db2['rebar'][1][j]
                            
                            ## Check if tie is full, that it couldn't be changed.
                            tie2[j] = min(tie1[j], len(rebar) - 2)
                            
                            if tie2[j] == tie1[j] :
                                self.add_msg(f'--- {db2["col_name"]} 繫筋調整 ({dir[j]}向)')
                            else :
                                self.add_msg(f'--- {db2["col_name"]} 繫筋繫滿 ({dir[j]}向)')

                            db2['rebar'][1][j] = rd.modify_tie(rebar, tie2[j])
                
                #### Check the tie number is the same if the setion is square
                if width == height :
                    if tie2[0] != tie2[1] :
                        tie2 = [max(tie2)]*2
                        
                        rebar = db2['rebar'][1]
                        
                        db2['rebar'][1] = [
                            rd.modify_tie(rebar[0], tie2[0]),
                            rd.modify_tie(rebar[1], tie2[1])
                            ]
                
                #### Check if no tie when min. side >= 40cm
                db2 = self.least_1_tie(db2)

            
                db2['tie'] = tuple(tie2)
                
                block1 = block2
                story1 = story2
                db1 = db2
                
                dbs[find_db_pos(dbs, story2+col_name)] = db2
            
            self.dbs = dbs
        
        
    def adjust_B1F_col_tie(self) :
        dbs = self.dbs
        for i in range(len(dbs)) :
            db = dbs[i]
            col_name = db['col_name']
            
            if col_name[:3] == 'B1F' :
                direction = ['X', 'Y']
                rebar = db['rebar'][1]
                tie = list(db['tie'])
                col_name = db['col_name']
                for i in range(len(rebar)) :
                    irebar = rebar[i]
                    itie = tie[i]
                    
                    max_tie = len(irebar) - 2
                    
                    if itie < max_tie :
                        db['rebar'][1][i] = rd.modify_tie(irebar, max_tie)
                        tie[i] = max_tie
                        
                        self.add_msg(f'-- {col_name} 柱筋繫滿 ({direction[i]}向)')
                        
                db['tie'] = tuple(tie)

                self.dbs = dbs 
                
    def least_1_tie(self, db) :
        width, height = db['section']
        tie = list(db['tie'])

        if (min(width, height) >= 40.0) :
            for j in range(len(tie)) :
                rebar = db['rebar'][1][j]

                if len(rebar) == 2 :
                    rebar.append(rebar[1])
                    # irebar[1][0] = '1'
                    # db2['rebar'][1][j] = rebar
                    

                if tie[j] < 1 :
                    tie[j] = 1
                    db['rebar'][1][j] = rd.modify_tie(rebar, tie[j])
                    self.add_msg(f'--- {db["col_name"]} 柱寬超過40cm，繫筋至少1支調整')

        return db

class ErroMsgBox():
    def __init__(self, msg):

        msg_box = QMessageBox()
        msg_box.setText(msg)
        msg_box.setWindowTitle('重大錯誤')
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

        self.msg_box = msg_box

def find_db_pos(db, story_colname) :
    #### To find the position of one coluimn in database
    for idx in range(len(db)) :
        if db[idx]['col_name'] == story_colname :
            return idx
        
    return None


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = main_window()
    window.show()
    app.exec_()

    # Main(True).run()