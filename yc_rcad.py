#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

PROGRAM      : YC_RCAD
DESPRIPITION : 定義 RCAD 物件 及 函數

AUTHOR       : YUCHEN LIN
CREATE DATE  : 2020.11.25
UPDATE DATE  : 2023.07.22
VERSION      : v2.0
UPDATE       :
    1. Compactible with RCAD 2019, 2020
    2. Improve the functions of BEAM tmp file for reading and writing
    3. Add the function of revising column tie
    4. Fix the output new tmp of column

"""    

# Create RCAD object
class rcad :
    def __init__(self, version = None) :
        None
        
# Create RCAD_BEAM object
class rbeam2016(rcad) :
    #####
    def __init__(self, rbeam_filename = 'tmp-Beam-Rebar.txt', \
                 version = 'RCAD2016') :
        
        self.rbeam_filename = rbeam_filename
        self.version = version
        # CHECK if file does exist
        try :
            self.rbeam_datas = self.read_beam_data()
        except :
            print('No ' + self.rbeam_filename + ' to read !')
        
        # EXTRACT tmp file
        self.rbeam_blocks = self.extract_beam_rebar()
        
        # EXTRACT to database
        self.rbeam_db = self.read_blocks()

    #####    
    def read_beam_data(self) :
        with open(self.rbeam_filename, 'r') as f :
            return f.readlines()

    #####    
    def extract_beam_rebar(self) :
        block_list = []
        s = self.rbeam_datas
        
        for i in range(len(s)) :
            if i == 0 : # 1st LINE
                temp = []
                temp.append(s[i])
                
            elif i == len(s)-1 : # The LAST LINE
                block_list.append(temp)
                
            elif 'F.NO' in s[i] : # The beginning of next block
                block_list.append(temp)
                
                temp = []
                temp.append(s[i])
                
            else : # During the same block
                temp.append(s[i])
        
        return block_list

    #####    
    def read_blocks(self) :
        blocks = self.rbeam_blocks
        
        
        db = []
        
        for i in range(len(blocks)) :
            block = blocks[i]
            
            '''
            db dict
            count -> int : 連續跨梁數
            beam_story -> str : 此梁樓層
            beam_name -> list[str] : 各梁梁名
            section -> list[(b,h)] : 各梁尺寸
            rebar -> dict{POS : (#,[(left,mid,right)])} : 各梁配筋
            web -> list[(#, num)] : 各梁腰筋
            stirrup -> list[((#L,numL),(#M,numM,(#R,numR)))] : 各梁肋筋
            '''
            db.append({
                'count' : self.count_beam(block),
                'beam_story' : self.find_beam_stroy(block),
                'beam_name' : self.find_beam_name(block), 
                'section' : self.find_section(block), 
                'rebar' : self.find_rebar(block), 
                'web' : self.find_web(block), 
                'stirrup' : self.find_stirrup(block) 
                })
        
        return db
     
    #####
    def count_beam(self, block) :
        count = len(block[0].split())-2
        
        return count
    
    #####
    def beam_story(self,block) :
        story = block[0].split()[1]
        
        return story
    
    #####
    def find_beam_name(self,block) :
        s = block[0].split()
        
        name = []
        
        for i in range(2,len(s)) :
                name.append(s[i].split('"')[1])
        
        return name
    
    #####
    def find_section(self,block) :
        s = block[0].split()
        d = []
        
        for i in range(2,len(s)) :
            temp = s[i].split('(')[-1].split(')')[0].split('*')
            
            d.append([float(temp[0]),float(temp[1])])
        
        return d
    
    #####
    def find_rebar(self,block) :
        rebar = {}
        
        for i in range(len(block)) :
            if 'TOP' in block[i] :
                break
        
        # TOP1 ZONE
        temp = block[i].split()
        del temp[0]
        
        rebar_size = temp[0]
        del temp[0]
        
        rebar_nums = []
        for j in range(0,len(temp),3) :
            rebar_nums.append([int(temp[j]), int(temp[j+1]),int(temp[j+2])])
            
        rebar['TOP1'] = [rebar_size, rebar_nums]
        
        i += 1
        
        # TOP2 ZONE
        temp = block[i].split()
        del temp[0]
        
        rebar_size = temp[0]
        del temp[0]
        
        rebar_nums = []
        for j in range(0,len(temp),3) :
            rebar_nums.append([int(temp[j]), int(temp[j+1]),int(temp[j+2])])
            
        rebar['TOP2'] = [rebar_size, rebar_nums]
        
        i += 2
        
        # BOT2 ZONE
        temp = block[i].split()
        del temp[0]
        
        rebar_size = temp[0]
        del temp[0]
        
        rebar_nums = []
        for j in range(0,len(temp),3) :
            rebar_nums.append([int(temp[j]), int(temp[j+1]),int(temp[j+2])])
            
        rebar['BOT2'] = [rebar_size, rebar_nums]
        
        i += 1
        
        # BOT1 ZONE
        temp = block[i].split()
        del temp[0]
        
        rebar_size = temp[0]
        del temp[0]
        
        rebar_nums = []
        for j in range(0,len(temp),3) :
            rebar_nums.append([int(temp[j]), int(temp[j+1]),int(temp[j+2])])
            
        rebar['BOT1'] = [rebar_size, rebar_nums]
        
        
        return rebar

    #####    
    def find_web(self,block) :
        for i in range(len(block)) :
            if 'WEB' in block[i] :
                s = block[i].split()
                break
        
        d = []
        
        for i in range(1,len(s)) :
            temp = s[i].split('#')
            
            d.append(['#'+temp[1], int(temp[0])])
        
        return d
            

    #####    
    def find_stirrup(self,block) :
        for i in range(len(block)) :
            if 'STIR' in block[i] :
                break

        temp = block[i].split()
        del temp[0]
        
        rebar_nums = []
        for j in range(0,len(temp),3) :
            rebar_num = []
            
            temp2 = temp[j:j+3]
            
            for k in range(len(temp2)) :
                rebar_num.append(\
                    [temp2[k].split('@')[0],\
                     float(temp2[k].split('@')[1])])
            
            rebar_nums.append(rebar_num)
        
        return rebar_nums
    
    ####
    def update_rbeam(self) :
        db = self.rbeam_db
        block = self.rbeam_blocks
        
        for j in range(len(block)) :
            jblock = block[j]
            
            for i in range(len(db)) :
                idb = db[i]
                
                if idb['beam_name'][0] in jblock[0].split('"') :
                    count = idb['count']
                    break
            
            # Modify rebar data
            top1 = jblock[1].split()
            top2 = jblock[2].split()
            bot2 = jblock[4].split()
            bot1 = jblock[5].split()
            
            k = 2
            for kk in range(count) :
                for kkk in range(3) :
                    top1[k] = str(idb['rebar']['TOP1'][1][kk][kkk])
                    top2[k] = str(idb['rebar']['TOP2'][1][kk][kkk])
                    bot2[k] = str(idb['rebar']['BOT2'][1][kk][kkk])
                    bot1[k] = str(idb['rebar']['BOT1'][1][kk][kkk])
                    
                    k += 1
            
            block[j][1] = ' '.join(top1)
            block[j][2] = ' '.join(top2)
            block[j][4] = ' '.join(bot2)
            block[j][5] = ' '.join(bot1)
        
            # Modify stirrup
            stir = jblock[7].split()
            
            k = 1
            for kk in range(count) :
                for kkk in range(3) :
                    temp = idb['stirrup'][kk][kkk]
                    temp[1] = str(int(temp[1]))
                    stir[k] = '@'.join(temp)
                    
                    k += 1
            
            block[j][7] = ' '.join(stir)
            
            # Modify web
            web = jblock[8].split()
            
            k = 1
            for kk in range(count) :
                temp = idb['web'][kk]
                temp = str(temp[1]) + temp[0]
                
                web[k] = temp
                
                k += 1
            
            block[j][8] = ' '.join(web)
            
        self.rbeam_blocks = block
    
    ####
    def output_rbeam(self, filename = None) :
        self.update_rbeam()
        
        block = self.blocks
        
        if filename == None :
            filename = 'new_' + self.rbeam_filename
        
        with open(filename, 'w') as f :
            for i in range(len(block)) :
                for j in range(len(block[0])) :
                    temp = block[i][j]
                    
                    if temp[-1] == '\n' :
                        f.write(block[i][j])
                    else :
                        f.write(block[i][j]+'\n')
    
    ####
    # def rbeam2sercb_rebar(self) :
        
        
    #     pass

    
# Create RCAD_COL object
class rcol2016(rcad) :
    #####
    def __init__(self, rcol_filename = 'tmp-Col-Rebar.txt', version = 'RCAD2016') :
        super().__init__(version = version)
        
        self.rcol_filename = rcol_filename
        try :
            self.rcol_datas = self.read_col_data()
        except :
            print('No ' + self.rcol_filename + ' to read !')
        
        self.rcol_blocks = self.extract_col_rebar()
        
        self.rcol_db = self.read_blocks()

    #####    
    def read_col_data(self) :
        with open(self.rcol_filename, 'r', encoding = 'Big5') as f :
            return f.readlines()

    #####    
    def extract_col_rebar(self) :
        block_list = []
        s = self.rcol_datas
        
        isStart = False
        
        for i in range(len(s)) :
            if (not isStart) and ('RCAD_ASCO COLUMN-LINE' in s[i]) :
                isStart = True
                
                temp = []
                # temp.append(s[i])
                
            elif i == len(s)-1 :
                temp.append(s[i])
                block_list.append(temp)
                
            elif (isStart) and ('RCAD_ASCO COLUMN-LINE' in s[i]) :
                block_list.append(temp)
                
                temp = []
                # temp.append(s[i])
                
            elif isStart :
                temp.append(s[i])
        
        return block_list

    #####    
    def read_blocks(self) :
        blocks = self.rcol_blocks
        
        db = []
        
        for i in range(len(blocks)) :
            block = blocks[i]
            
            for j in range(int(block[1])) :
                jblock  = block[j*5+2:j*5+7]
                
                db.append({
                    'col_name' : self.find_col_name(jblock,block[0]), # str
                    'section' : self.find_section(jblock), # (b,h)
                    'rebar' : self.find_rebar(jblock), # ((numx,numy),rebararray)
                    'tie' : self.find_tie(jblock), # (#, (numx,numy)
                    'stirrup' : self.find_stirrup(jblock), # list[((#D,numD),(#M,numM,(#U,numU)))]
                    'As' : self.find_As(jblock),
                    'story' : self.find_story(jblock),
                    'sect_name' : block[0]
                    })
        
        return db
    
    #####
    def find_story(self,block) :
        s = block[0].split()
        
        return s[0]
    
    #####
    def find_col_name(self,block,col_name) :
        s = block[0].split()
        
        col_name = col_name.split('"')[1]
        
        return s[0]+col_name
    
    #####
    def find_section(self,block) :
        s = block[1].split()
        
        b = int(float(s[0]))
        h = int(float(s[1]))
                
        return (b,h)
    
    #####
    def find_rebar(self,block) :
        x_rebar_data = block[2].split()
        y_rebar_data = block[3].split()
        
        x_rebar = x_rebar_data[2:]
        y_rebar = y_rebar_data[2:]
        
        num_x_rebar = 0
        for temp in x_rebar :
            for n in range(len(temp)) :
                if temp[n] == '#' :
                    num_x_rebar += 1
        
        num_y_rebar = 0
        for temp in y_rebar :
            for n in range(len(temp)) :
                if temp[n] == '#' :
                    num_y_rebar += 1
        
        rebar = [(num_x_rebar, num_y_rebar), [x_rebar, y_rebar]]
        
        return rebar

    #####    
    def find_tie(self,block) :
        x_rebar_data = block[2].split()[2:]
        y_rebar_data = block[3].split()[2:]
        
        num_x_tie = 0
        num_y_tie = 0
        
        for temp in x_rebar_data :
            if temp[0] == '1' :
                num_x_tie += 1
        
        for temp in y_rebar_data :
            if temp[0] == '1' :
                num_y_tie += 1
        
        return (num_x_tie, num_y_tie) 

    #####    
    def find_stirrup(self,block) :
        stirrup_data = block[4].split()
        
        stir = []
        nums = []
        
        for i in range(3) :
            stirNO = stirrup_data[i].split('@')[0]
            spacing = int(stirrup_data[i].split('@')[1].split(',')[0])
            
            if i == 1 :
                num = stirrup_data[i].split('@')[1].split(',')[1]
            else :
                num = ''
            
            stir.append((stirNO, spacing))
            nums.append(num)
        
        stir.append(nums)
        
        return stir
    
    #####
    def find_As(self, block) :
        return float(block[1].split()[2])
    
    ####
    def update_rcol(self) :
        db = self.rcol_db
        block = self.rcol_blocks
        
        for j in range(len(block)) :
            jblock = block[j]
            
            num_story = int(jblock[1])
            
            for jj in range(num_story) :
                jjblock = jblock[jj*5+2: jj*5+7]
                
                for idb in db :
                    if (idb['sect_name'] in jblock[0]) and \
                        (idb['story'] in jjblock[0].split()[0]) :
                            break
                
                # Modify main rebar
                rebars = idb['rebar']
                tie = idb['tie']
                
                for k in range(2) :
                    num_rebar = rebars[0][k]
                    num_tie = tie[k]
                    rebar = rebars[1][k]
                    
                    block[j][jj*5+4+k] = \
                        '  ' + str(num_rebar) + '  ' + str(num_tie) +\
                        '  ' + '  '.join(rebar) + '\n'
                
                # Modify stirrup
                stirrup = idb['stirrup']
                s = '  '
                for k in range(3) :
                    temp = stirrup[k]
                    
                    s += temp[0] + '@' + str(temp[1])
                    
                    if k == 1 :
                        s += ',%d' % int(stirrup[3][1])
                    
                    s += '   '
                    
                s += '\n'
                block[j][jj*5+6] = s
                
            
        self.rcol_blocks = block
    
    ####
    def output_rcol(self, filename = None) :
        
        self.update_rcol()
        
        block = self.rcol_blocks
        datas = self.rcol_datas
        
        if filename == None :
            filename = self.rcol_filename + '_new' 
        
        for iblock in block :
            for j in range(len(datas)) :
                if '$RCAD_ASCO COLUMN-LINE' in datas[j] :
                    if iblock[0] in datas[j+1] :
                        for i in range(len(iblock)) :
                            datas[(j+1+i)] = iblock[i]
        
        self.rcol_datas = datas
        
        with open(filename, 'w') as f :
            for temp in datas :
                f.write(temp)

#### RCAD 2019 ####
## BEAM ##
class rbeam2019(rbeam2016) :
    #### initialize ####
    def __init__(self, 
                 rbeam_filename = 'tmp-Beam-Rebar.txt', 
                 rbeam_logname = 'Beam-Log.txt', 
                 version = 'RCAD2019') :
        self.version = version
        self.rbeam_filename = rbeam_filename
        self.rbeam_logname = rbeam_logname
        
        self.POS = ['TOP1', 'TOP2', 'TOP3', 'BOT1', 'BOT2', 'BOT3']
        
        # CHECK if file does exist
        try :
            self.rbeam_datas = self.read_beam_data() # rbeam2016 function
        except :
            print('No ' + self.rbeam_filename + ' to read !')
        
        # Get Stories data
        self.stories = self.get_all_stories()
        
        # EXTRACT tmp file
        self.rbeam_blocks = self.extract_beam_rebar() # rbeam2016 function
        
        # EXTRACT to database
        self.rbeam_db = self.read_blocks() 
    
    #### Built @ V2.0
    def get_all_stories(self) :
        with open(self.rbeam_logname, 'r', encoding='Big5') as f:
            s = f.readlines()
            
        for i in range(len(s)) :
            line = s[i]
            
            if '各樓層設計狀況' in line :
                idx = i+3
                
                break
        
        stories = []
        
        for i in range(idx, len(s)) :
            line = s[i]
            
            if '------' in line :
                break
            else :
                stories.append(line.split()[0])
        
        return stories.reverse()
        
    
    #####    
    def read_blocks(self) :
        blocks = self.rbeam_blocks
        
        
        db = []
        
        for i in range(len(blocks)) :
            block = blocks[i]
            
            '''
            db dict
            count -> int : 連續跨梁數
            beam_story -> str : 此梁樓層
            beam_name -> list[str] : 各梁梁名
            section -> list[(b,h)] : 各梁尺寸
            rebar -> dict{POS : (#,[(left,mid,right)])} : 各梁配筋
            web -> list[(#, num)] : 各梁腰筋
            stirrup -> list[((#L,numL),(#M,numM,(#R,numR)))] : 各梁肋筋
            nth-block -> int : tmp檔中第n個區塊
            '''
            db.append({
                'count' : self.count_beam(block), # update to 2019
                'beam_story' : self.find_beam_story(block), # update to 2019
                'beam_name' : self.find_beam_name(block), # update to 2019
                'section' : self.find_section(block), # update to 2019
                'rebar' : self.find_rebar(block), # update to 2019
                'rebar2' : self.find_rebar2(block), # add @ V2.0
                'web' : self.find_web(block), # modify @ V2.0
                'stirrup' : self.find_stirrup(block), # rbeam2016 function
                'nth-block' : i # Add @ V2.0
                })
        
        return db
     
    #####
    def count_beam(self, block) : # update to 2019
        count = int(len(block[0].split('('))-1)
        
        return count # int
    
    #####
    def find_beam_story(self,block) : # update to 2019
        s = block[0].split('"')[1]
        
        story = ["",""]
        
        #### Merge Story Part ####
        if '~' in s :
            story[0] = s.split('~')[0]
            
            temp = s.split('~')[1]
            
            for i in range(len(temp)) :
                if temp[i] == "F" :
                    story[1] = temp[0:(i+1)]
                    break
        
        #### Single Story Part ####
        else :
            for i in range(len(s)) :
                if s[i] == "F" :
                    story = [s[0:(i+1)], s[0:(i+1)]]
                    break
        
        return story
    
    #####
    def find_beam_name(self,block) : # update to 2019
        s = block[0].split('"')
        
        name = []
        
        for i in range(1,len(s), 2) :
                temp = s[i].split('~')[-1]
                
                for j in range(len(temp)) :
                    if temp[j] == 'F' :
                        name.append(temp[(j+1):(len(temp))])
        
        return name
    
    #####
    def find_section(self,block) :  # update to 2019
        s = block[0].split('(')
        d = []
        
        for i in range(1,len(s)) :
            temp = s[i].split(')')[0].split('*')
            width = temp[0]
            height = temp[1]
            
            d.append([float(width),float(height)])
        
        return d
    
    #####
    def find_rebar(self,block) : # update to 2019
        rebar = {}
        
        ### TOP1 ZONE        
        for i in range(len(block)) :
            if 'TOP1' in block[i] :
                break

        temp = block[i].split()
        del temp[0]
        
        rebar_size = temp[0]
        del temp[0]
        
        rebar_nums = []
        for j in range(0,len(temp),4) :
            rebar_nums.append([int(temp[j]), int(temp[j+1]),int(temp[j+2])])
            
        rebar['TOP1'] = [rebar_size, rebar_nums]

        ### TOP2 ZONE        
        for i in range(len(block)) :
            if 'TOP2' in block[i] :
                break
            
        temp = block[i].split()
        del temp[0]
        
        rebar_size = temp[0]
        del temp[0]
        
        rebar_nums = []
        for j in range(0,len(temp),4) :
            rebar_nums.append([int(temp[j]), int(temp[j+1]),int(temp[j+2])])
            
        rebar['TOP2'] = [rebar_size, rebar_nums]
        
        
        ### BOT2 ZONE
        for i in range(len(block)) :
            if 'BOT2' in block[i] :
                break
            
        temp = block[i].split()
        del temp[0]
        
        rebar_size = temp[0]
        del temp[0]
        
        rebar_nums = []
        for j in range(0,len(temp),4) :
            rebar_nums.append([int(temp[j]), int(temp[j+1]),int(temp[j+2])])
            
        rebar['BOT2'] = [rebar_size, rebar_nums]
        
        # BOT1 ZONE
        for i in range(len(block)) :
            if 'BOT1' in block[i] :
                break
            
        temp = block[i].split()
        del temp[0]
        
        rebar_size = temp[0]
        del temp[0]
        
        rebar_nums = []
        for j in range(0,len(temp),4) :
            rebar_nums.append([int(temp[j]), int(temp[j+1]),int(temp[j+2])])
            
        rebar['BOT1'] = [rebar_size, rebar_nums]
        
        
        return rebar
    
    #####
    def find_rebar2(self,block) : # update to 2019
        rebar = {}
        
        POS = self.POS
        
        for pos in POS :
            for i in range(len(block)) :
                if pos in block[i] :
                    isExist = True
                    break
                elif i == len(block)-1 :
                    isExist = False
            
            if isExist :
                temp = block[i].split()
                rebar_nums = []
                
                for j in range(1,len(temp), 4) :
                    rebar_nums.append([temp[j], int(temp[j+1]), int(temp[j+2]), int(temp[j+3])])
            else :
                rebar_nums = []
                TOP1 = rebar['TOP1']
                rebar_nums = [['#3', 0, 0, 0]] * len(TOP1) # default
            
            rebar[pos] = rebar_nums
        
        return rebar

    #####    
    def find_web(self,block) : # Modify @ V2.0
        for i in range(len(block)) :
            if 'WEB ' in block[i] :
                s = block[i].split()
                break
        
        d = []
        
        for i in range(1,len(s)) :
            temp = s[i].split('#')
            
            d.append([int(temp[0]), '#'+temp[1]])
        
        return d
            
    
    ####
    def update_rbeam(self) : # update to 2019
        dbs = self.rbeam_db
        blocks = self.rbeam_blocks
        
        for j in range(len(blocks)) :
            block = blocks[j]
            
            for db in dbs :
                if db['nth-block'] == j :
                    break
            
            # Modify rebar data
            POS = self.POS
            rebar = db['rebar2']
            
            for pos in POS :
                rebar_pos = rebar[pos]
                
                for k in range(len(block)):
                    if pos in block[k] :
                        temp = '%s' % pos
                        
                        for kk in range(len(rebar_pos)) :
                            temp += '\t%s\t%d\t%d\t%d' % tuple(rebar_pos[kk])
                        
                        block[k] = temp + '\n'
                        
                        break
        
            # Modify stirrup
            stir = db['stirrup']
            for k in range(len(block)):
                if 'STIR ' in block[k] :
                    temp = '%s' % 'STIR'
                    
                    for kk in range(len(stir)) :
                        kkstir = stir[kk] 
                        
                        for kkk in range(3) :
                            temp += '\t%s@%d' % (kkstir[kkk][0],int(kkstir[kkk][1]))
                    
                    block[k] = temp + '\n'
                    
                    break
                    
            # Modify web
            web = db['web']
            
            for k in range(len(block)):
                if 'WEB ' in block[k] :
                    temp = '%s' % 'WEB '
                    
                    for kk in range(len(web)) :
                        temp += '\t%d%s' % tuple(web[kk])
                    
                    block[k] = temp + '\n'
                    
                    break
            
            blocks[j] = block
            
            
        self.rbeam_blocks = blocks
    
    ####
    def output_rbeam(self, filename = None) :
        self.update_rbeam()
        
        block = self.rbeam_blocks
        
        if filename == None :
            filename = self.rbeam_filename.replace('.txt', '_new.txt')
        
        with open(filename, 'w') as f :
            for i in range(len(block)) :
                for j in range(len(block[i])) :
                    temp = block[i][j]
                    
                    if temp[-1] == '\n' :
                        f.write(block[i][j])
                    else :
                        f.write(block[i][j]+'\n')

## COL ##
class rcol2019(rcol2016) :
    #####
    def __init__(self, rcol_filename = 'tmp-Col-Rebar.txt', version = 'RCAD2019') :
        super().__init__(version = version)
        
        self.rcol_filename = rcol_filename
        try :
            self.rcol_datas = self.read_col_data()
        except :
            print('No ' + self.rcol_filename + ' to read !')
        
        self.rcol_blocks = self.extract_col_rebar()
        
        self.rcol_db = self.read_blocks()

    #####    
    def read_col_data(self) :
        with open(self.rcol_filename, 'r', encoding = 'Big5') as f :
            return f.readlines()

    #####    
    def extract_col_rebar(self) :
        block_list = []
        s = self.rcol_datas
        
        isStart = False
        
        for i in range(len(s)) :
            if (not isStart) and ('RCAD_ASCO COLUMN-LINE' in s[i]) :
                isStart = True
                
                temp = []
                # temp.append(s[i])
                
            elif i == len(s)-1 :
                temp.append(s[i])
                block_list.append(temp)
                
            elif (isStart) and ('RCAD_ASCO COLUMN-LINE' in s[i]) :
                block_list.append(temp)
                
                temp = []
                # temp.append(s[i])
                
            elif isStart :
                temp.append(s[i])
        
        return block_list

    #####    
    def read_blocks(self) : ## update to 2019
        blocks = self.rcol_blocks
        
        db = []
        
        for i in range(len(blocks)) :
            block = blocks[i]
            
            for j in range(2, len(block), 5) :
                jblock  = block[j:(j+5)]
                
                '''
                db dict
                col_name -> str : 柱編號 5FC1
                section -> tuple : 柱尺寸 (100.0, 110.0)
                rebar -> list : 柱配筋 [[x支數,y支數],[x配筋,y配筋]]
                tie -> tuple : 柱繫筋數 [x繫筋數, y繫筋數]
                stirrup -> list : 柱箍筋間距 [(#D, spacingD),(#M, spacingM),(#U, spacingU)]
                As -> float : 柱筋需求
                story -> str : 樓層名 5F
                sect_name -> str : 斷面名 "C1"
                block_index -> tuple : block的索引值
                '''
                
                db.append({
                    'col_name' : self.find_col_name(jblock,block[0]), # using 2016 function
                    'section' : self.find_section(jblock), # using 2016 function
                    'rebar' : self.find_rebar(jblock), # using 2016 function
                    'tie' : self.find_tie(jblock), # using 2016 function
                    'stirrup' : self.find_stirrup(jblock), # update to 2019
                    'As' : self.find_As(jblock), # using 2016 function
                    'story' : self.find_story(jblock), # using 2016 function
                    'sect_name' : block[0],
                    'block_index' : (i, j) # add in 2019
                    })
        
        return db

    

    #####    
    def find_stirrup(self,block) :
        stirrup_data = block[4].split()
        
        stir = []
        nums = []
        
        for i in range(3) :
            stirNO = stirrup_data[i].split('@')[0]
            spacing = int(stirrup_data[i].split('@')[1].split(',')[0])
            
            stir.append((stirNO, spacing))

        return stir

    def update_rcol(self) : 
        #### UPDATE rcol_blocks from rcol_db
        
        db = self.rcol_db
        blocks = self.rcol_blocks
        
        for j in range(len(blocks)) :
            block = blocks[j]
            
            col_name = block[0].split('"')[1] # C1
            
            for k in range(2, len(block), 5) :
                if block[k].split()[1] != 'RECT' :
                    print('Skip "%s %s", due to the shape is not a rectangle!!\n' % (block[k].split()[0], col_name))
                    continue
                
                kstory = block[k].split()[0]
                
                story_colname = kstory + col_name
                
                for idb in db :
                    if idb['col_name'] == story_colname :
                        break
                
                # Modify rebar and tie
                block_rebar = block[(k+2):(k+4)]
                db_rebar = idb['rebar']
                db_sect = idb['section']
                for xy in range(2) :
                    block_rebar = block[k+2+xy].split()
                    
                    del block_rebar[2:]
                    
                    block_rebar = block_rebar + db_rebar[1][xy]
                    
                    block[k+2+xy] = ('%10s'*len(block_rebar) + '\n') % tuple(block_rebar)

                # Modify stirrup
                stir = idb['stirrup']
                block_stir = ' '*37
                for kk in range(3) :
                    istir = stir[kk]
                    block_stir += f'    {istir[0]}@{istir[1]}'

                    if kk == 1 :
                        block_stir += f',{max(db_sect)}'
                block[k+4] = block_stir    
            
            blocks[j] = block
                
            
        self.rcol_blocks = blocks
    
    def output_rcol(self, filename = 'tmp-Col-Rebar_new.txt') :
        #### OUTPUT tmp file and update rcol_datas
        
        self.update_rcol()
        
        block = self.rcol_blocks
        datas = self.rcol_datas
        
        col_rebar_start_line = '$RCAD_ASCO COLUMN-LINE'
        
        for start_row in range(len(datas)):
            if col_rebar_start_line in datas[start_row]:
                break
        
        del datas[start_row:]
        
        for iblock in block :
            datas = datas + \
                [col_rebar_start_line + '\n'] + iblock
        
        self.rcol_datas = datas
        
        with open(filename, 'w') as f :
            for temp in datas :
                f.write(temp)

#### METHOD ZONE
def modify_tie(rebar, new_tie_num) :
    current_tie_num = 0
    
    num_rebar = len(rebar)
    max_tie_num = num_rebar - 2
    
    if num_rebar % 2 == 0 :
        isOdd = False
        
    else :
        isOdd = True
    
    
    for irebar in rebar :
        if irebar[0] == '1' :
            current_tie_num += 1
    
    new_tie_num = min(max_tie_num, new_tie_num)
    
    # Create tie arange matrix
    if num_rebar == 2 :
        pass
    elif num_rebar == 3 :
        tie_mat = [[1]]
    else :
        if isOdd :
           half_tie_num = int((max_tie_num + 1) / 2)
           tie_mat_col = int((num_rebar + 1) / 2)
           
        else :
           half_tie_num = int(max_tie_num / 2)
           tie_mat_col = int(num_rebar / 2)
        
        
        temp = []
        for i in range(half_tie_num) :
            if i % 2 == 0 :
                temp.append(0)
            else :
                temp.append(1)
                
        half_tie_mat = [temp]
        for i in range(tie_mat_col - 1) :
            temp = [n for n in half_tie_mat[i]]
            del temp[-1]
            half_tie_mat.append([1] + temp)
        
        tie_mat = []
        for i in range(len(half_tie_mat)) :
            temp = half_tie_mat[i]
            
            temp2 = []
            for j in range(-2, -1*len(temp)-1, -1) :
                temp2.append(temp[j])
            
            tie_mat.append(temp + temp2)
        
    if not isOdd :
        for i in range(len(tie_mat)) :
            tie_mat[i].insert(int(max_tie_num/2), 1)
                
    ## Get the arange
    for new_tie_mat in tie_mat :
        if sum(new_tie_mat) == new_tie_num :
            break
    
    for i in range(1,len(rebar)-1) :
        irebar = rebar[i].split('#')
        irebar[0] = str(new_tie_mat[i-1])
        
        rebar[i] = '#'.join(irebar)
    
    return rebar
# rcol=rcol2016()
# rbeam = rbeam2016()
# rbeam = rbeam2019().output_rbeam()

#### TEST 
# rcol = rcol2019()
# rcol.output_rcol()


# db = rcol.rcol_db
# col = db[10]
# rebar = col['rebar'][1][0]

# print(rcol.modify_tie(rebar,3))

