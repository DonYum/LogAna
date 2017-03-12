#!/usr/bin/env python
# -*- coding: utf-8 -*-

# TODO: 考虑ftp异常的处理方法，比如：
#   (<class 'ftplib.error_temp'>, error_temp('425 Failed to establish connection.',), <traceback object at 0x7f8a97608e88>)

import re
import os
import shutil
from ftplib import FTP
import sys
# from flask import current_app
# from . import celery
# from config import Config


# import re
# import os
# import sys
import gzip
# import shutil
import zipfile
import fnmatch
import chardet
import codecs


class FtpHelper(object):
    def __init__(self, url, dest_dir='./logcat_dl/'):
        # url style: r'ftp://uploadloguser:uploadloguser@whaley.cn@uploadlogftp.aginomoto.com \
        #    /000896AC1D8B0745/594c9e1b-9de7-4f7e-8ff9-18544f932f95/'
        need_redownload_flag = False

        if url == '':
            print("url cannot be empty!")
            return False

        if url[-1] == '/':
            url = url[0:-1]
        
        self.user = r'uploadloguser'
        self.pwd = r'uploadloguser@whaley.cn'
        # self.server_domain = r'@uploadlogftp.aginomoto.com'
        self.url = url
        
        # mk ftp dest dir.
        if not os.path.exists(dest_dir):
            print("making dst dir(" + dest_dir + ")...")
            os.mkdir(dest_dir)

        url_split = url.split('/')
        self.dest_dir = os.path.join(dest_dir, url_split[-1])
        
        # mk ftp dest dir.
        if need_redownload_flag and os.path.exists(self.dest_dir):
            print("dst dir(", self.dest_dir, ") exist. removing...")
            shutil.rmtree(self.dest_dir)
        # mk ftp dest dir.
        if not os.path.exists(self.dest_dir):
            print("making dst dir(" + self.dest_dir + ")...")
            os.mkdir(self.dest_dir)

        if os.path.exists(os.path.join(self.dest_dir, 'files')):
            print("This url has been download.")
            self.dl_finish = True
            return

        # get log dir from url.
        self.log_dir = '/' + url_split[-2] + '/' + url_split[-1]
        print(self.log_dir)
        # print("RJZ: " + Config.BASE_DIR)

        # mk dest_dir
        #self.dest_dir = os.path.join(dest_dir, url_split[-2])
        #print("making new dst dir(" + self.dest_dir + ")...")
        #os.mkdir(self.dest_dir)

        # result
        self.dl_finish = False

        # login ftp server.
        self.ftp = None
        self.ftp = self.login_ftp_server()

    def __del__(self):
        pass
        # if self.ftp:
        #     self.ftp.quit()

    @staticmethod
    def login_ftp_server():
        ftp = FTP('uploadlogftp.aginomoto.com')
        ftp.set_pasv(0)
        ftp.login(r'uploadloguser', r'uploadloguser@whaley.cn')
        print(ftp.getwelcome())
        print("Login ftp OK!")
        return ftp

    def dl_log(self, pattern):
        '''dl log according pattern.'''
        # trace_pat = re.compile(pattern, re.IGNORECASE)
        list_names = self.ftp.nlst(self.log_dir)
        for file_name in list_names:
            if re.match(pattern, os.path.split(file_name)[1]):
                print("download file: " + file_name)
                file_hand = open(os.path.join(self.dest_dir, os.path.split(file_name)[1]), 'wb').write
                self.ftp.retrbinary('RETR %s' % file_name, file_hand)

    def dl_tombstone(self):
        self.dl_log('tombstone*')

    def dl_logcat(self):
        self.dl_log('logcat.log*')

    def dl_trace_log(self):
        self.dl_log('traces.*')

    def dl_all_log(self):
        list_names = self.ftp.nlst(self.log_dir)
        print("Start to dl all logcat!")
        print(list_names)
        if not list_names:
            print("There is no file in url.")
        for file_name in list_names:
            print("download file: " + file_name)
            file_hand = open(os.path.join(self.dest_dir, os.path.split(file_name)[1]), 'wb').write
            self.ftp.retrbinary('RETR %s' % file_name, file_hand)

        f = open(os.path.join(self.dest_dir, 'files'), 'w')
        f.write('\n'.join(list_names))
        f.close()
        self.dl_finish = True
        print("Finish to dl all logcat!")



# 解压缩并连接log，程序自动去`src_dir`取压缩过的log，然后串联起来。
# 这一步用在ftp dl之后，log filter之前。
# src_dir ---unzip---> tmp ---join---> dst_dir
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
            print("dst dir(" + self.dst_dir + ") exist. removing...")
            shutil.rmtree(self.dst_dir)
            
        print("making dst dir:", self.dst_dir, self.tmp_dir)
        os.mkdir(self.dst_dir)
        os.mkdir(self.tmp_dir)
            
        if not os.path.exists(self.src_dir):
            print("src dir (" + self.src_dir + ") does not exist, exit!")
            os.exit()
            
        self.join_finish = False
        if os.path.exists(os.path.join(self.dst_dir, 'files')):
            print("This url has been download.")
            self.dl_finish = True
            return

        # self.unzip_all()
        # self.join_logcat()


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
        print('RJZ: src_dir=' + self.src_dir)
        for path, dirs, files in os.walk(self.src_dir):
            # print('RJZ: path=' + path)
            for file in files:
                file_path = os.path.join(path, file)
                if file.startswith('log'):
                    if not os.path.getsize(file_path)==0:
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
                    else:
                        print('RJZ: file=' + file + ", size is 0!!!")
            break

    # clear tmp dir.
    def clr_tmp_dir(self):
        tmp_dir = os.path.join(self.tmp_dir, 'files')
        if os.path.exists(tmp_dir):
            print("removing tmp dir: " + tmp_dir)
            shutil.rmtree(tmp_dir)
        
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
            print("------------------------------------------------> Try to convert str:")
            print(result, " -> utf-8!")
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
                    break

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

        f = open(os.path.join(self.dst_dir, 'files'), 'w')
        f.write(dst_file + ' write finished.')
        f.close()


if __name__ == '__main__':
    dest_dir = "/data1/renjz/log_analyze/flaky_bk/flasky/log_dir"
    # url = r'ftp://uploadloguser:uploadloguser@whaley.cn@uploadlogftp.aginomoto.com/000896AC1D8B0745/594c9e1b-9de7-4f7e-8ff9-18544f932f95/'
    # url = r'ftp://uploadloguser:uploadloguser@whaley.cn@uploadlogftp.aginomoto.com/00080BF1D329836E/6f2eeb1a-f38f-40ad-89a7-5e60e9365c09/'
    # url = r'ftp://uploadloguser:uploadloguser@whaley.cn@uploadlogftp.aginomoto.com/003814920901319e/865aa8c9-0c7c-41f4-a267-2d3b80438ba1/'
    # url = r'ftp://uploadloguser:uploadloguser@whaley.cn@uploadlogftp.aginomoto.com/001832c1c604e18e/e3b6378c-5be3-463a-8bf2-24871a7c25aa/'
    # url = r'ftp://uploadloguser:uploadloguser@whaley.cn@uploadlogftp.aginomoto.com/00089FE26F34007A/89a98231-f93d-45e9-bfa6-f9eb5cd02e30/'
    # url = r'ftp://uploadloguser:uploadloguser@whaley.cn@uploadlogftp.aginomoto.com/00089FBAD94B007D/7ab0ed2d-ad4c-4360-a062-b6132ec550d2/'
    # url = r'ftp://uploadloguser:uploadloguser@whaley.cn@uploadlogftp.aginomoto.com/000881EF5EFB0763/2bae682b-1aef-46db-b8ba-051e4191baf4/'
    # url = r'ftp://uploadloguser:uploadloguser@whaley.cn@uploadlogftp.aginomoto.com/003a2251491da19e/514fcbdd-ec3b-4afe-87d1-f8b11a17adc8/'
    # url = r'ftp://uploadloguser:uploadloguser@whaley.cn@uploadlogftp.aginomoto.com/003a34c18418365e/4fa8d629-580c-47e5-aa20-dce91b0a6266/'
    # url = r'ftp://uploadloguser:uploadloguser@whaley.cn@uploadlogftp.aginomoto.com/00089F74ECFA041D/c2ae5882-c0bc-4146-a82a-fffc4f0b6092/'
    # url = r'ftp://uploadloguser:uploadloguser@whaley.cn@uploadlogftp.aginomoto.com/003814920901319e/97b8655e-0ff1-48b8-a9e0-b1e5f99bd7b1/'
    # url = r'ftp://uploadloguser:uploadloguser@whaley.cn@uploadlogftp.aginomoto.com/003c10c10005319e/9fe50aae-caec-4349-8ad5-ebadebb489de/'
    # url = r'ftp://uploadloguser:uploadloguser%40whaley.cn@uploadlogftp.aginomoto.com/000877FC902E07E9/b549afc6-cef7-463a-993a-32d46d39043f'
    url = r'ftp://uploadloguser:uploadloguser@whaley.cn@uploadlogftp.aginomoto.com/003c10c10005319e/15ee29f1-2358-4ef4-8a08-53afc60c61ad'

    cnt = 0
    ftp = FtpHelper(url=url, dest_dir=dest_dir)
    try:
        while not ftp.dl_finish and cnt < 10:
            ftp.dl_all_log()
        if not ftp.dl_finish:
            print("not finish!!!")
        else:
            d = Unzip_JoinLog(src_dir=ftp.dest_dir, dst_dir=os.path.join(ftp.dest_dir, 'log_join'))
            d.unzip_all()
            d.join_logcat()
            d.clr_tmp_dir()
    except:
        print(sys.exc_info())