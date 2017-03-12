#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
import sys
import shutil
import fnmatch
import chardet
# from .models import *


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
    def __init__(self, src_file='./logcat_join/logcat.log.all', kw_list=["CMD_AUTO", "EVENT-DIS", "NetUti"]):
        self.debug = 1      # if 1: not del dl dir.
        self.src_file = src_file
        self.kw_reg_dict = {}

        self.regex_str = self.struct_regex(0)
        # if not self.kw_list:
            
        # return self.process_file(src_file)
        

    def __del__(self):
        pass
        
    def struct_regex(self, match_flag):
        strs = []

        # kwywords = Keyword.query.order_by(Keyword.timestamp.desc())
        kwywords = None
        if kwywords:
            for kw in kwywords:
                strs.append(kw.kw_regex)
                self.kw_reg_dict[kw.kw_regex] = kw.description
        if not strs:
            strs = ["CMD_AUTO", "EVENT-DIS", "NetUti"]
        
        if match_flag:
            regex_str = ".*" + "|.*".join(strs)
            # regex_str = "((.*" + ")|(.*".join(strs) + "))"
        else: 
            regex_str = "((" + ")|(".join(strs) + "))"
        # return re.compile(regex_str)
        print("reg_str: ", regex_str)
        return regex_str
        
    def process_content(self, content):
        print(content)
        regex_str = self.regex_str

        # regex_str = "^(.*\s+.*)\s+([0-9]+)\s+([0-9]+)\s+([A-Z])\s+(.*)$"
        pat = re.compile(regex_str)
        res = pat.search(content)
        
        if res and res.groups()[0]:
            print("res_l is:", res.groups()[0])
            desc = res.groups()[0]
            print("desc is:", )
            res_l = list(res.groups())[1:]
            res_s = res.group(0)
            print("res_s is:", res_s)
            res_idx = res_l.index(res_s)
            # print("res_idx is:", res_idx)
            str_to = '<span class="text-danger" style="background: #DA81F5;">' + res_s + '</span>'
            pat = re.compile(res_s)
            dst_str = pat.sub(str_to, content)      # 替换
            print("dst_str is:", dst_str)
            return (desc, dst_str)
        else:
            """ 匹配失败 """
            print("search fail!")
            return (None, content)
            
        
    def process_line(self, src_str):
        """
        grep keywords
        01-29 21:46:22.173  1984  2692 E WifiStateMachine: CMD_AUTO_CONNECT sup state ScanState my state DisconnectedState nid=0 roam=3
        res is: ('01-29 21:46:22.173 ', '1984', '2692', 'E', 'WifiStateMachine: CMD_AUTO_CONNECT sup state ScanState my state DisconnectedState nid=0 roam=3')
        """
        
        print(src_str)
        # regex_str = self.struct_regex(0)
        regex_str = "^(.*\s+.*)\s+([0-9]+)\s+([0-9]+)\s+([A-Z])\s+(.*)$"
        pat = re.compile(regex_str)
        res = pat.match(src_str)
        if res:
            """ logcat格式处理 """
            time, pid, uid, tag, content = res.groups()
            print("res_l is:", res.groups())
            
            (desc, content) = self.process_content(content)
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
        
        regex_str1 = self.struct_regex(1)
        
        with open(file, 'r') as f:
            # resul = list()
            for line in f:
                # 使用search会降低匹配速度，所以这里借用match做了一个trick。
                # 速度可以提高4倍（5.6s->1.1s）
                pat = re.compile(regex_str1)    # re预编译，提高匹配速度。
                res = pat.match(line)
                # res = pat.search(line)
                
                # 匹配到之后做专门处理
                if res:
                    res_str = self.process_line(line)
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
    BASEDIR = "/data1/renjz/log_analyze/flaky_bk/flasky/log_dir/b549afc6-cef7-463a-993a-32d46d39043f"
    src_file = os.path.join(BASEDIR, 'log_join/logcat.log.all')
    dst_dir = './logcat_join/'
    d = processLogcat(src_file)
    d.process_file()
    # try:
        # d.unzip_all()
        # d.join_logcat()
    # except:
        # print(sys.exc_info())