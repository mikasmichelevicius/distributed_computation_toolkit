import time

strs = "EXECUTING JOB1"

spaces = "  "
for x in range(len(strs)):
    time.sleep(0.5)
    print(spaces,strs[x])
    spaces += "  "
