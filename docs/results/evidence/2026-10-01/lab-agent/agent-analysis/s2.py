import re, itertools, random
from fractions import Fraction
exec(open('an/struct.py').read().split('TMAX')[0])
def run(r,k,q,b,TM):
    for t in range(1,TM+1):
        pad=[q]*(2*t+1);x=pad+list(b)+pad;y=x
        for _ in range(t): y=step(r,k,y)
        n=len(x)
        for d in range(n):
            if all(y[i]==x[(i+d)%n] for i in range(n)):
                return t,(d if d<=n//2 else d-n)
    return None
random.seed(1)
for name,(k,r) in W.items():
    got={}
    for q in range(k):
        if r[q*k*k+q*k+q]!=q: continue
        for L in range(1,9):
            cnt = (k**L) if k**L<=3000 else 3000
            it = itertools.product(range(k),repeat=L) if k**L<=3000 else (tuple(random.randrange(k) for _ in range(L)) for _ in range(3000))
            for b in it:
                if b[0]==q or b[-1]==q: continue
                res=run(r,k,q,b,14)
                if res and res[0]>1: got.setdefault((q,res[0],res[1]),b)
    print(name,got,flush=True)
