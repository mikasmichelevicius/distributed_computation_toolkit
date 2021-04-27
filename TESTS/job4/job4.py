import time

# Job example that contains a runtime error, where the
# string is indexed outside of its range. The program
# should return an error in stderr file.

strs = "EXECUTING JOB"

spaces = ""
for x in range(len(strs)):
    spaces += "  "
for x in range(len(strs)+1):
    time.sleep(1)
    print(spaces,strs[x])
    spaces = spaces[:-2]
