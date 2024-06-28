#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

PROGRAM      : RCA001-AutoColTieAdjust
DESPRIPITION : 順柱繫筋

AUTHOR       : YUCHEN LIN
CREATE DATE  : 2024.01.04
UPDATE DATE  : 
VERSION      : v2.0
UPDATE       :
    1. Update to 113 RC code
    2. Fix the message dialoge updating criteria

"""    

import yc_rcad as rd
import copy
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import time
import numpy as np
import pandas as pd
import os, sys, math


global new_msg
global isEnd
new_msg = ''
isEnd = False
#isRun = False
isAddMsg = True

class show_process(QThread) :
    #### For pyQT5
    show_text = pyqtSignal(str)
    end_info = pyqtSignal()
    
    def run(self) :
        global new_msg
        global isEnd
        global isAddMsg
        
        while True :
            if not isEnd and isAddMsg :
                self.show_text.emit(new_msg)
                isAddMsg = False
                #time.sleep(1)
            elif isEnd :
                self.end_info.emit()
                isEnd = False
                #isRun = False
                #time.sleep(5)
            else : 
                pass

def new_msg_input(s) :
    #### Send to GUI and Print in console
    global isAddMsg
    
    global new_msg
    new_msg += (s + '\n')
    print(s)
    
    isAddMsg = True

def main() :
    global isEnd
    global isRun
    #### main code
    
    isRun = True
    
    rcol = rd.rcol2019()
    new_msg_input('- 讀取柱配筋成功 (%s)' % rcol.rcol_filename)
    
    msgBox = QMessageBox()
    thread0 = QThread()
    msgBox.setText('是否需要讀取柱excel？')
    msgBox.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
    thread0.run = msgBox
    thread0.start
    reply = msgBox.exec()
    
    if reply == QMessageBox.Yes :
        for tmp in os.listdir() :
            if 'RCAD柱調整' in tmp :
                col_excel = tmp
                break
                    
        try :
            new_msg_input('- 讀取柱excel中... (%s)' % col_excel)
            tie_demand, stir = read_tie_demand(os.path.join(os.getcwd(),col_excel))
            new_msg_input('- 讀取柱excel成功 (%s)' % col_excel)
        except :
            new_msg_input('- 讀取柱excel失敗!!! 請確認是否有放進資料夾 !!!')
            # msgBox = QMessageBox.about('重大錯誤!!!!', '讀取柱excel失敗!!! 請確認是否有放進資料夾 !!!')
            
            msgBox = QMessageBox()
            msgBox.setText('讀取柱excel失敗!!! 請確認是否有放進資料夾 !!!')
            msgBox.setWindowTitle('重大錯誤')
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
            
            tie_demand = None
            
    else :
        new_msg_input('- 未讀取柱excel!!!')
        tie_demand = None
    
    dbs = rcol.rcol_db
    blocks = rcol.rcol_blocks
    
    if tie_demand == None :
        pass
    else :
        new_msg_input('\n- 確認最小繫筋量 ...')
        dbs = tie_demand_check(dbs, tie_demand, stir)
    
    new_msg_input('\n- 開始順繫筋 ...')
    for i in range(len(blocks)) :
        block = blocks[i]
        new_msg_input('\n--  順柱 %s ' % block[0].split('"')[1])
        
        dbs = adjust_tie(dbs, block, tie_demand)
    
    new_msg_input('\n- B1F 柱筋繫滿 ...')
    for i in range(len(dbs)) :
        db = dbs[i]
        col_name = db['col_name']
        
        if col_name[:3] == 'B1F' :
            dbs[i] = adjust_B1F_col_tie(db)
            
    
    new_msg_input('- 更新柱配筋 ...')
    rcol.rcol_db = dbs
    
    new_msg_input('- 輸出順繫筋的tmp檔 ...')
    rcol.output_rcol()
    
    new_msg_input('- FINISHED !!!!!')
    
    isEnd = True
    

def read_tie_demand(file) :
    df = pd.read_excel(file, sheet_name = 'RCA001', engine="openpyxl")

    tie_demand = {}
    stir = {}
    
    for row in range(len(df)) :
        if not np.isnan(df['nx'][row]) :
            tie_demand[df['Flr.Col.'][row]] = [int(df['nx'][row]), int(df['ny'][row])]
            stir[df['Flr.Col.'][row]] = [df['#'][row], int(df['spacing'][row])]
            
    return tie_demand, stir

def find_db_pos(db, story_colname) :
    #### To find the position of one coluimn in database
    for idx in range(len(db)) :
        if db[idx]['col_name'] == story_colname :
            return idx
        
    return None

def tie_demand_check(dbs, tie_demand, stirs) :
    
    for db in dbs :
        idb = db
        col_name = db['col_name']
        
        try :
            nxy = tie_demand[col_name]
            stir = stirs[col_name]
        except :
            new_msg_input('-- 最小繫筋讀取未成功 !!!! (%s)' % col_name)
            continue
        
        ties = list(db['tie'])
        rebar = db['rebar'][1]
        
        dir = ['X', 'Y']
        
        for n in range(2) :
            tie_n = ties[n]
            nn = nxy[n]
            
            # Tie Between per 2 rebar
            if tie_n < math.floor((len(rebar[n])-2)/2) :
                ties[n] = math.floor((len(rebar[n])-2)/2)
                
                rebar[n] = rd.modify_tie(rebar[n], ties[n])
                
                new_msg_input(f'--- 隔根箍調整!!!!! {col_name}, {dir[n]}向)')
            
            # Tie number excceeds the number of rebar
            if nn > tie_n : 
                ties[n] = nn
                if nn > (len(rebar[n])-2) :
                    new_msg_input(f'------ 柱筋不夠排 請CHECK!!!!! {col_name}, {dir[n]}向)')
                rebar[n] = rd.modify_tie(rebar[n], nn)

        db['tie'] = tuple(ties)
        db['rebar'][1] = rebar
        
        istir = (stir[0], stir[1])
        db_stir = []
        for i in range(3) :
            db_stir.append(istir)

        db['stirrup'] = db_stir

        dbs[dbs.index(idb)] = db    
        
    return dbs

def adjust_tie(dbs, block, tie_demand) :
    #### To adjust the tie following the rule
    
    col_name = block[0].split('"')[1]
    
    block1 = block[2:7]
    story1 = block1[0].split()[0]
    db1 = dbs[find_db_pos(dbs, story1+col_name)]
    
    for i in range(7, len(block), 5) :
        block2 = block[i:i+5]
        story2 = block2[0].split()[0]
        db2 = dbs[find_db_pos(dbs, story2+col_name)]
        
        tie1 = list(db1['tie'])
        tie2 = list(db2['tie'])
        
        stirNo1 = db1['stirrup'][0][0]
        stirNo2 = db2['stirrup'][0][0]
        
        dir = ['X', 'Y']

        #### Check No. of tie of below story is not less than one of upper story
        if stirNo1 == stirNo2 :
            for j in range(2) :
                if tie2[j] < tie1[j] :
                    rebar = db2['rebar'][1][j]
                    
                    ## Check if tie is full, that it couldn't be changed.
                    tie2[j] = min(tie1[j], len(rebar) - 2)
                    
                    if tie2[j] == tie1[j] :
                        new_msg_input(f'--- {db2["col_name"]} 繫筋調整 ({dir[j]}向)')
                    else :
                        new_msg_input(f'--- {db2["col_name"]} 繫筋繫滿 ({dir[j]}向)')

                    db2['rebar'][1][j] = rd.modify_tie(rebar, tie2[j])
        else :
            new_msg_input(f'--- {db2["col_name"]} 箍筋號數不同，不順繫筋')
        
        #### Check the tie number is the same if the setion is square
        width, height = db2['section']
        if width == height :
            if tie2[0] != tie2[1] :
                tie2 = [max(tie2)]*2
                
                rebar = db2['rebar'][1]
                
                db2['rebar'][1] = [
                    rd.modify_tie(rebar[0], tie2[0]),
                    rd.modify_tie(rebar[1], tie2[1])
                    ]
        
    	#### Check if no tie when min. side >= 40cm
        if (min(width, height) >= 40.0) :
            for j in range(len(tie2)) :
                rebar = db2['rebar'][1][j]
                irebar = rebar[j]
                if len(irebar) == 2 :
                    irebar.append(irebar[1])
                    irebar[1][0] = '1'
                    db2['rebar'][1] = ' '.join(irebar)
                    

                if tie2[j] < 1 :
                    tie2[j] = 1
                    db2['rebar'][1][j] = rd.modify_tie(rebar, tie2[j])
                    new_msg_input(f'--- {db2["col_name"]} 柱寬超過40cm，繫筋至少1支調整')

    
        db2['tie'] = tuple(tie2)
        
        block1 = block2
        story1 = story2
        db1 = db2
        
        dbs[find_db_pos(dbs, story2+col_name)] = db2
    
    return dbs

def adjust_B1F_col_tie(db) :
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
            
            new_msg_input(f'-- {col_name} 柱筋繫滿 ({direction[i]}向)')
            
    db['tie'] = tuple(tie)

    return db

if __name__ == '__main__' :
    
    app = QApplication(sys.argv)
    
    main()