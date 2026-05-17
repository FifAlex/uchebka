def ssqrt(n: int):
    x = 1
    i = 0
    while(i != 6):
        x = 0.5*(x + n/x)
        i += 1
    return x
print(ssqrt(49))
