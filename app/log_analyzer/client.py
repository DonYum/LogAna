from tasks import ftp_dl
import time
result = ftp_dl.delay("ftp://uploadloguser:uploadloguser@whaley.cn@uploadlogftp.aginomoto.com/00089FBAD94B007D/7ab0ed2d-ad4c-4360-a062-b6132ec550d2/")

while not result.ready():
    print("not ready yet")
    time.sleep(1)

    print(result.get())
