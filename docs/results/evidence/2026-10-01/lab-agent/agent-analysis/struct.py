import re, itertools
txt=open('README.md').read()
W={}
for m in re.finditer(r'- `(w\d+)`: k=(\d), rule table \[(.*?)\]',txt):
    W[m.group(1)]=(int(m.group(2)),[int(x) for x in m.group(3).split(',')])
def step(r,k,x):
    n=len(x);return [r[x[i]*k*k+x[(i+1)%n]*k+x[(i+2)%n]] for i in range(n)]
TMAX=10
for name,(k,r) in W.items():
    found={}
    for q in range(k):
        if r[q*k*k+q*k+q]!=q: continue
        for L in range(1,6 if k==3 else 5):
            for b in itertools.product(range(k),repeat=L):
                if b[0]==q or b[-1]==q: continue
                for t in range(1,TMAX+1):
                    pad=[q]*(2*t+1)
                    x=pad+list(b)+pad
                    y=x
                    for _ in range(t): y=step(r,k,y)
                    n=len(x);ok=None
                    for d in range(n):
                        if all(y[i]==x[(i+d)%n] for i in range(n)): ok=d;break
                    if ok is not None:
                        d=ok if ok<=n//2 else ok-n
                        # reduce: minimal period for this block
                        key=(q,t,d)
                        # velocity as fraction
                        from fractions import Fraction
                        v=Fraction(d,t)
                        found.setdefault((q,v,t),(b,t,d));break
    print(name,sorted((q,str(v),t,val[2],list(val[0])) for (q,v,t),val in found.items()),flush=True)
