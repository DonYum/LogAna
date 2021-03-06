import os
from config import Config
import math

def get_dir_from_url(url):
	if url == '':
		print("url cannot be empty!")
		return ''

	if url[-1] == '/':
		url = url[0:-1]

	return url.split('/')[-1]

def get_dst_dir_from_url(url):
	return os.path.join(Config.LOGCAT_DIR, get_dir_from_url(url))

def convert_size(num):
    for x in ['bytes','KB','MB','GB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')
    