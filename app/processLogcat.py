#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
import sys
import shutil
import fnmatch
import chardet
from .models import *


BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

def format2(fg=None, bg=None, bright=False, bold=False, dim=False, reset=False):
    # manually derived from http://en.wikipedia.org/wiki/ANSI_escape_code#Codes
    codes = []
    if reset: codes.append("0")
    else:
        if not fg is None: codes.append("3%d" % (fg))
        if not bg is None:
            if not bright: codes.append("4%d" % (bg))
            else: codes.append("10%d" % (bg))
        if bold: codes.append("1")
        elif dim: codes.append("2")
        else: codes.append("22")
    return "\033[%sm" % (";".join(codes))

def format(fg=None, bg=None, bright=False, bold=False, dim=False, reset=False):
    # manually derived from http://en.wikipedia.org/wiki/ANSI_escape_code#Codes
    codes = []
    if reset: codes.append("0")
    else:
        if not fg is None: codes.append("3%d" % (fg))
        if not bg is None:
            if not bright: codes.append("4%d" % (bg))
            else: codes.append("10%d" % (bg))
        if bold: codes.append("1")
        elif dim: codes.append("2")
        else: codes.append("22")
    return "\033[%sm" % (";".join(codes))

class processLogcat(object):
    def __init__(self, src_file='./logcat_join/logcat.log.all', kw_res=None):
        self.debug = 1      # if 1: not del dl dir.
        self.src_file = src_file
        if not kw_res:
            return False
        self.kw_res = kw_res
        self.RSSI_array = [[], []]
        self.ping_array = [[], []]

        self.regex_str = self.struct_regex(0)
            
        # return self.process_file(src_file)

    def __del__(self):
        pass
        
    def struct_regex(self, match_flag):
        strs = [row.kw_regex for row in self.kw_res]
        
        if match_flag:
            regex_str = ".*" + "|.*".join(strs)
            # regex_str = "((.*" + ")|(.*".join(strs) + "))"
        else: 
            regex_str = "((" + ")|(".join(strs) + "))"
        # return re.compile(regex_str)
        print("reg_str: ", regex_str)
        return regex_str

    def get_RSSI_array(self):
        return self.RSSI_array

    def get_ping_array(self):
        return self.ping_array
        
    def process_content(self, time, content):
        print("src_str=" + content)

        # Get RSSI value here!
        # RSSI_reg_str = "WifiConfigStore.*RSSI=(-[0-9]*)"
        pat1 = re.compile("(WifiConfigStore.*RSSI=(-[0-9]*)|ConnectivitySer.*data=([0-9]*)ms)")
        res = pat1.search(content)
        
        if res and res.groups()[0]:
            print("RSSI|ping res is:", res.groups())
            if res.groups()[1]:
                self.RSSI_array[0].append(time)
                self.RSSI_array[1].append(int(res.groups()[1]))
            elif res.groups()[2]:
                self.ping_array[0].append(time)
                self.ping_array[1].append(int(res.groups()[2]))

        # Parse normal keywords!
        pat = re.compile(self.regex_str)
        res = pat.search(content)
        
        if res and res.groups()[0]:
            print("res_g is:", res.groups())
            dst_reg_arr = list(res.groups())[1:]
            dst_reg_idx = 0
            for dst_reg in dst_reg_arr:
                if not dst_reg==None:
                    break
                dst_reg_idx += 1
            # print("dst_reg_idx="+str(dst_reg_idx))
            print("description="+str(self.kw_res[dst_reg_idx].description))

            desc = self.kw_res[dst_reg_idx].description

            res_l = list(res.groups())[1:]
            res_s = res.group(0)
            print("res_s is:"+res_s+".")
            print("content is:"+content+".")
            # res_idx = res_l.index(res_s)
            # print("res_idx is:", res_idx)
            str_to = '<span class="text-danger" style="background: #DA81F5;">' + res_s + '</span>'
            pat = re.compile(res_s)
            dst_str = pat.sub(str_to, content)      # 替换
            print("dst_str is:", dst_str)
            return (desc, dst_str)
        else:
            """ 匹配失败 """
            # print("search fail!")

            return (None, None)
            
        
    def process_line(self, src_str):
        """
        grep keywords
        01-29 21:46:22.173  1984  2692 E WifiStateMachine: CMD_AUTO_CONNECT sup state ScanState my state DisconnectedState nid=0 roam=3
        res is: ('01-29 21:46:22.173 ', '1984', '2692', 'E', 'WifiStateMachine: CMD_AUTO_CONNECT sup state ScanState my state DisconnectedState nid=0 roam=3')
        """
        
        # print("src_str="+src_str)
        # regex_str = self.struct_regex(0)
        regex_str = "^(.*\s+.*)\s+([0-9]+)\s+([0-9]+)\s+([A-Z])\s+(.*)$"
        pat = re.compile(regex_str)
        res = pat.match(src_str)
        if res:
            """ logcat格式处理 """
            time, pid, uid, tag, content = res.groups()
            # print("res_l is:", res.groups())
            
            (desc, content) = self.process_content(time, content)
            if not desc:
                return None

            res_str = {'time':time, 'pid':pid, 'uid':uid, 'tag':tag, 'desc':desc, 'cont':content}
        else:
            """ 非logcat格式处理 """
            print("no match!")
            res_str = {'time':None, 'pid':None, 'uid':None, 'tag':None, 'desc':None, 'cont':src_str}

        return res_str
            
        
    def grep_logcat(self):
        pass
        
    def get_basic_info(self):
        pass
        
      
    def process_file(self):
        file = self.src_file
        print("process file:", file)
        results = []
        
        kw_reg = self.struct_regex(1)
        ping_reg = ".*ConnectivitySer.*data=[0-9]*|"
        RSSI_reg = ".*WifiConfigStore.*RSSI=-[0-9]*|"
        regex_str = ping_reg + RSSI_reg + kw_reg
        print("regex_str=" + regex_str)
        
        with open(file, 'r') as f:
            # resul = list()
            for line in f:
                # 使用search会降低匹配速度，所以这里借用match做了一个trick。
                # 速度可以提高4倍（5.6s->1.1s）
                pat = re.compile(regex_str)    # re预编译，提高匹配速度。
                res = pat.match(line)
                # res = pat.search(line)
                
                # 匹配到之后做专门处理
                if res:
                    res_str = self.process_line(line)
                    if res_str:
                        results.append(res_str)
        return results
                    

        """
    def process_file(self, file):
        print("process file:", file)
        with open(file, 'rb') as f:
            resul = list()
            for line in f:
                #   logcat的每一行编码方式不同，大部分是'ascii'和'utf-8'，
                # 少部分是'ISO-8859-2'和'windows-1252'，
                # 只有'windows-1252'在做处理的时候会出exception，
                # 所以需要在这里做exception处理。
                #   使用这种方式可以免去在join过程中去做，在join过程做编码转换速度太慢。
                try:
                    new_content = str(line, encoding = "UTF8") 
                except UnicodeDecodeError:
                    result = chardet.detect(line)
                    coding = result.get('encoding')
                    print(result, " -> utf-8!")
                    if coding and coding == 'windows-1252':
                        new_content = line.decode('windows-1252').encode('UTF8')
                    else:
                       new_content = line
                    new_content = str(new_content, encoding = "UTF8") 
                else:
                    new_content = line
                    new_content = str(new_content, encoding = "UTF8")
                    
                new_content = new_content.strip()
                if not len(new_content):
                    continue
                new_content = self.process_string(new_content)
                resul.append(new_content)
            # print(result)

            """
            
if __name__ == '__main__':
    src_file='./logcat_join/logcat.log.all'
    dst_dir = './logcat_join/'
    d = processLogcat(src_file, dst_dir)
    # try:
        # d.unzip_all()
        # d.join_logcat()
    # except:
        # print(sys.exc_info())