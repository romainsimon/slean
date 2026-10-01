import json,itertools
from fractions import Fraction
rules={int(k):v for k,v in json.load(open('an/rules.json')).items()}
def step(x,t,k):
    n=len(x);return [t[x[i]*k*k+x[(i+1)%n]*k+x[(i+2)%n]] for i in range(n)]
def find(w,q,blk,T):
    k=4 if len(rules[w])==64 else 3;t=rules[w]
    x=[q]*(2*T+1)+list(blk)+[q]*(2*T+1)
    x0=x[:]
    for s in range(1,T+1):
        x=step(x,t,k)
        n=len(x)
        for d in range(-s-1,s+2):
            if all(x[i]==x0[(i+d)%n] for i in range(n)):return s,d
    return None
T=20;found={}
for w in range(16):
    k=4 if len(rules[w])==64 else 3
    for q in range(k):
        if rules[w][q*k*k+q*k+q]!=q:continue
        for L in range(1,6 if k==4 else 7):
            for blk in itertools.product(range(k),repeat=L):
                if blk[0]==q or blk[-1]==q:continue
                r=find(w,q,blk,T)
                if r:
                    key=(w,q,r[0],Fraction(r[1],r[0]))
                    if key not in found:found[key]=(blk,r)
for key,(blk,r) in sorted(found.items()):print(key[0],'bg',key[1],'t',r[0],'d',r[1],'v',key[3],''.join(map(str,blk)))
json.dump([[k[0],k[1],list(b),r[0],r[1]] for k,(b,r) in found.items()],open('an/structs.json','w'))
