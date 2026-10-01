import json, itertools, sys
from fractions import Fraction
rules={int(w):r for w,r in json.load(open('an/rules.json')).items()}
ks=[4,4,3,3,4,3,4,3,4,4,4,3,4,4,4,3]
TMAX=16
def find(wd,maxlen):
    k=ks[wd]; r=rules[wd]; found={}
    for q in range(k):
        if r[q*k*k+q*k+q]!=q: continue
        for L in range(1,maxlen+1):
            for B in itertools.product(range(k),repeat=L):
                if B[0]==q or B[-1]==q: continue
                pad=TMAX+2
                x=[q]*pad+list(B)+[q]*pad; n=len(x)
                cur=x
                for t in range(1,TMAX+1):
                    cur=[r[cur[i]*k*k+cur[(i+1)%n]*k+cur[(i+2)%n]] for i in range(n)]
                    nz=[i for i in range(n) if cur[i]!=q]
                    if not nz: break
                    if nz[0]<=1 or nz[-1]>=n-2: break
                    if tuple(cur[nz[0]:nz[-1]+1])==B:
                        d=pad-nz[0]
                        found.setdefault((q,t,Fraction(d,t)),(B,t,d)); break
    return found
res={}
for wd in range(16):
    k=ks[wd]
    f=find(wd,7 if k==3 else 6)
    print(wd,{(q,t,str(v)):B for (q,t,v),(B,_,d) in f.items()},flush=True)
    res[wd]=[(q,B,t,d) for (q,t,v),(B,t,d) in f.items()]
json.dump(res,open('an/structs.json','w'))
