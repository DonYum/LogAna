#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
import sys
import gzip
import shutil
import zipfile
import fnmatch
import chardet
import codecs

# 解压缩并连接log，程序自动去`src_dir`取压缩过的log，然后串联起来。
# 这一步用在ftp dl之后，log filter之前。
class Unzip_JoinLog(object):
    def __init__(self, src_dir='./zip_log/', dst_dir='./logcat_join/'):
        self.debug = 1      # if 1: not del dl dir.
        
        self.src_dir = (src_dir, './')['' == src_dir]
        self.dst_dir = (dst_dir, './')['' == dst_dir]
        self.tmp_dir = os.path.join(self.dst_dir, 'tmp')
        
        # flag to seperate zip and gz file.
        self.is_zip_file = 0
        
        # mk ftp dest dir.
        if os.path.exists(self.dst_dir):
            print("dst dir(", self.dst_dir, ") exist. removing...")
            shutil.rmtree(self.dst_dir)
            
        print("making dst dir(", self.dst_dir, ", and", self.tmp_dir, ")...")
        os.mkdir(self.dst_dir)
        os.mkdir(self.tmp_dir)
            
        if not os.path.exists(self.src_dir):
            print("src dir (", self.src_dir, ") does not exist, exit!")
            os.exit()
            
        self.unzip_all()
        self.join_logcat()

    def __del__(self):
        pass
        # if self.debug:
            #shutil.rmtree(self.src_dir)

    def un_gzip_logcat(self, gz_file):
        """unzip to here"""
        g_file = gzip.GzipFile(os.path.join(self.src_dir, gz_file))
        f_name = gz_file.replace(".gz", "")
        f_name = os.path.join(self.tmp_dir, f_name)     # unzip to file f_name
        print(gz_file, ' -> ', f_name)
        
        #创建gzip对象
        open(f_name, "wb").write(g_file.read())
        #gzip对象用read()打开后，写入open()建立的文件中。
        g_file.close()

    def un_zip_logcat(self, zip_file):
        """ungz zip file"""
        zip_file = os.path.join(self.src_dir, zip_file)
        print('unzip -> ', zip_file)  #打印zip归档中目录
        fz = zipfile.ZipFile(zip_file, 'r')
        for file in fz.namelist():
            fz.extract(file, self.tmp_dir)

    # unzip zip here.
    def unzip_all(self):
        a = os.walk(self.src_dir)
        for path, dirs, files in a:
            for file in files:
                if file.endswith('.gz'):
                    self.un_gzip_logcat(file)
                # elif zipfile.is_zipfile(file):
                elif file.endswith('.zip'):
                    self.is_zip_file = 1
                    self.un_zip_logcat(file)
                elif file.startswith("logcat"):
                    # 如果不是gzip/zip，而且以logcat开头，就需要cp到tmp_dir。
                    # 用来针对zip格式的logcat上传方法。
                    print(file, "does not need unzip, just copy.")
                    shutil.copy2(os.path.join(self.src_dir, file), self.tmp_dir)
                else:
                    pass
        
    #   logcat的每一行编码方式不同，大部分是'ascii'和'utf-8'，
    # 少部分是'ISO-8859-2'和'windows-1252'，
    # 只有'windows-1252'在做处理的时候会出exception，比如“for line in file:”
    # 所以需要在这里做转换，防止后面出现exception。
    # 这个处理过程需要考虑处理速率，下面方法是最优方案。
    def convert_str(self, str_b):
        # 该函数效率比较高，同样的110M文件，处理速度约0.9s
        try:
            content = str(str_b, encoding = "UTF8") 
        except UnicodeDecodeError:
            result = chardet.detect(str_b)
            coding = result.get('encoding')
            print(result, " -> utf-8!" + result.get('confidence'))
            if coding and result.get('confidence')>0.7:
                str_b = str_b.decode(coding).encode('UTF8')
            else:
                print("Can not handle: ", str_b)
                str_b = None
        except:
            print("Can not handle: ", str_b)
        return str_b
        
    '''
    def convert_str(self, str_b): 
        # 该函数效率很低，主要是try耗时，110M文件需要11s+
        try:
            ret_s = str_b.decode('ascii').encode('UTF8')
        except UnicodeDecodeError:
            result = chardet.detect(str_b)
            coding = result.get('encoding')
            if coding and coding == 'windows-1252':
                ret_s = str_b.decode('windows-1252').encode('UTF8')
                print(result, " -> utf-8!")
            else:
               ret_s = str_b
        else:
           ret_s = str_b
           
        return ret_s
    '''
    
    def join_logcat(self, dst_file="logcat.log.all"):
        readsize = 1024
        last_file = ''    # 最新log，最后join
        max_idx = 0     # logcat文件个数
        dst_file = os.path.join(self.dst_dir, dst_file)
        with open(dst_file, 'wb') as output:
            # zip解压出来的文件和gz解压出来的logcat的join方法不同。
            if self.is_zip_file:
                print("Join zip logcat files.")
                for root, dirs, files in os.walk(self.tmp_dir):
                    for filename in fnmatch.filter(files, r'logcat*.log'):
                        if not filename == 'logcat.log':
                            last_file = filename
                            _idx = re.findall(r"\d+", filename)
                            if _idx:
                                max_idx = int(_idx[0])
                                print('find logcat: ', filename, ', idx=', max_idx)

                # zip方式压缩过的logcat会存在1个或两个文件，需要分开处理。
                if max_idx:
                    for i in range(0, 2):
                        if 0 == i:
                            tmp_file = 'logcat.log'
                        else:
                            tmp_file = last_file
                        tmp_file = os.path.join(self.tmp_dir, tmp_file)
                        print("Join file:", tmp_file)
                        if os.path.exists(tmp_file):
                            with open(tmp_file, 'rb') as fileobj:
                                for line in fileobj:
                                    line = self.convert_str(line)
                                    if line:
                                        output.write(line)
                        else:
                            print(tmp_file, " not found!")
                else:
                    print("only 1 logcat file, just copy to:", dst_file)
                    tmp_file = os.path.join(self.tmp_dir, 'logcat.log')
                    with open(tmp_file, 'rb') as fileobj:
                        for line in fileobj:
                            line = self.convert_str(line)
                            if line:
                                output.write(line)
                    # shutil.copyfile(os.path.join(self.tmp_dir, 'logcat.log'), dst_file)
            else:
                print("Join gz logcat files.")
                # root, dirs, files = os.walk(self.tmp_dir)
                parts = os.listdir(self.tmp_dir)
                # parts.sort()
                for filename in fnmatch.filter(parts, r'logcat.log*'):
                    if not filename == 'logcat.log':
                        _idx = re.findall(r"\d+", filename)
                        if _idx:
                            max_idx = max(int(_idx[0]), max_idx)
                            print('find logcat: ', filename, ' idx=', int(_idx[0]), "->", max_idx)
                            
                print("max idx is:", max_idx)
                # 按顺序合并logcat，后缀数字越大就越早。
                for i in range(max_idx, -1, -1):
                    # print(filename)
                    if 0 == i:
                        tmp_file = 'logcat.log'
                    else:
                        tmp_file = 'logcat.log.' + str(i)
                    tmp_file = os.path.join(self.tmp_dir, tmp_file)
                    print("Join file:", tmp_file)
                    if os.path.exists(tmp_file):
                        with open(tmp_file, 'rb') as fileobj:
                            for line in fileobj:
                                line = self.convert_str(line)
                                if line:
                                    output.write(line)
                    else:
                        print(tmp_file, " not found! Just ignore it.")
                        
    
if __name__ == '__main__':
    src_dir = './zip/'
    # src_dir = './logcat_dl/'
    dst_dir = './logcat_join/'
    d = Unzip_JoinLog(src_dir, dst_dir)

    sys.path.append(os.path.dirname(sys.path[0]))
    # try:
        # d.unzip_all()
        # d.join_logcat()
    # except:
        # print(sys.exc_info())
