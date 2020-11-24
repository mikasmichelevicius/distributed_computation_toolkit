import time

strs = "EXECUTING JOB2"

spaces = ""
for x in range(len(strs)):
    spaces += "  "
for x in range(len(strs)):
    time.sleep(1)
    print(spaces,strs[x])
    spaces = spaces[:-2]
