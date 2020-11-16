import time

strs = "EXECUTING JOB1"

for x in range(len(strs)):
    time.sleep(0.5)
    print(strs[x])
