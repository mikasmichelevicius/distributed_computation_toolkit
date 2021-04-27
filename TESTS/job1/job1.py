import time

# Job example that prints the string diagonally and calls
# time.sleep() function to use some time. The system 
# should return a successfully executed job, containing
# stdout file with printed string. 

strs = "EXECUTING JOB"

spaces = ""
for x in range(len(strs)):
    spaces += "  "
for x in range(len(strs)):
    time.sleep(1)
    print(spaces,strs[x])
    spaces = spaces[:-2]
