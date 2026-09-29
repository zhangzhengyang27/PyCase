print('test')

a=3
b=1
if(a>b):
    print('a>b')
elif(a==b):
    print('a=b')
else:
    print('a<b')

for i in range(0,5):
    print(i)

c=range(0,6)
for a in c:
    print(a)

a=False
b=False
c=True
if(a or b):
    print('true')
else:
    print('false')
    
a='ab'
b='abcd'
if(a in b):
    print('a in b')

def add(a,b):
    return a+b,a,b
c,a,b=add(5,6)
print(c,a,b)

import numpy as np
data=np.linspace(3,10,8)
print(data)
print(data[-1])

a='9'
print(type(a))
b=np.float(a)
print(b,type(b),b+3)

a=['9','10']
b=np.array(a,dtype=int)
print(a,b,b[0])