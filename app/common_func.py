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

def convert_size(size_bytes):
   if (size_bytes == 0):
       return '0B'
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   # s = round(size_bytes/p, 2)
   s = math.ceil(size_bytes/p)
   return '%s %s' % (s, size_name[i])
   