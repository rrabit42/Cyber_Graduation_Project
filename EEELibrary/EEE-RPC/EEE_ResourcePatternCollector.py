# date and time
# memory | committed bytes in use
# memory | available MBytes
# process total | processor time
# process total | private bytes
# process total | working set
# processor information total | processor time
# processor information total | processor utility

import time
import psutil
import csv

def RPC(filename):
    
    f = open(filename,'w',newline='')
    wr = csv.writer(f)
    wr.writerow(['time', 'memory | committed bytes in use', 'memory | available MBytes', 'process total | processor time', 'process total | private bytes', 'process total | working set', 'processor information total | processor time', 'processor information total | processor utility'])

    while 1:

        proc_util = psutil.cpu_percent(15)
        now = time.localtime()
        date_and_time = str(now.tm_year) + " " + str(now.tm_mon) + " " + str(now.tm_mday) + " " + str(now.tm_hour) + " " + str(now.tm_min) + " " + str(now.tm_sec)
        mem = psutil.virtual_memory()

        wr.writerow([
            date_and_time,                                          # date and time
            mem.percent,                                            # memory | committed bytes in use
            mem.available,                                          # memory | available MBytes
            psutil.cpu_times().user + psutil.cpu_times().system,    # process total | processor time
            mem.total,                                              # process total | private bytes
            mem.used,                                               # process total | working set
            psutil.cpu_times().user,                                # processor information total | processor time
            proc_util                                               # processor information total | processor utility
        ])
