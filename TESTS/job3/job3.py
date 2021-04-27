
# Job example that calculates the Pi number with 100000
# digits and returns the generated number within stdout file
# upon completion.

def make_pi(digits):
    q, r, t, k, m, x = 1, 0, 1, 1, 3, 3
    for j in range(digits):
        if 4 * q + r - t < m * t:
            yield m
            q, r, t, k, m, x = 10*q, 10*(r-m*t), t, k, (10*(3*q+r))//t - 10*m, x
        else:
            q, r, t, k, m, x = q*k, (2*q+r)*x, t*x, k+1, (q*(7*k+2)+r*x)//(t*x), x+2


my_array = []

digits = 100000

for i in make_pi(digits):
    my_array.append(str(i))

my_array = my_array[:1] + ['.'] + my_array[1:]
big_string = "".join(my_array)
print("Pi with ",digits," decimal digits:\n %s" % big_string)
