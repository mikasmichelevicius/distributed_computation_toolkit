import time

strs = "EXECUTING JOB2"

spaces = ""
for x in range(len(strs)):
    spaces += "  "
for x in range(len(strs)):
    time.sleep(0.5)
    print(spaces,strs[x])
    spaces = spaces[:-2]
