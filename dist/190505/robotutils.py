import time

log_list= []
def oplogs(log):
    logs = "[%s]%s" %(time.strftime("%Y-%m-%d %H:%M:%S"),log)
    log_list.append(logs)
    print( logs)