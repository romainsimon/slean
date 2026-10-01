import json,itertools,sympy as sp
rules={int(k):v for k,v in json.load(open('an/rules.json')).items()}
ks={w:(4 if len(t)==64 else 3) for w,t in rules.items()}
def rows(w,k,t,wd,Lmax):
    S=set()
    for L in range(1,Lmax+1):
        for x in itertools.product(range(k),repeat=L):
            y=[t[x[i]*k*k+x[(i+1)%L]*k+x[(i+2)%L]] for i in range(L)]
            r=[0]*(k**wd)
            for i in range(L):
                a=0
                for j in range(wd):a=a*k+y[(i+j)%L]
                r[a]+=1
                a=0
                for j in range(wd):a=a*k+x[(i+j)%L]
                r[a]-=1
            S.add(tuple(r))
    return S
res={}
for w in range(16):
    k=ks[w];t=rules[w];out={}
    for wd in (1,2):
        Lmax=7 if k==3 else 6
        M=sp.Matrix(list(rows(w,k,t,wd,Lmax)))
        ns=M.nullspace()
        out[wd]=[[int(v) for v in (n*sp.ilcm(*[e.q for e in n])) ] for n in ns]
    # trivial space for wd=2
    triv=[[1]*(k*k)]
    for g in range(k):
        v=[0]*(k*k)
        for a in range(k):
            for b in range(k):
                v[a*k+b]=(1 if b==g else 0)-(1 if a==g else 0)
        triv.append(v)
    T=sp.Matrix(triv)
    # w1 laws embedded
    e1=[[f[b] if False else f[a] for a in range(k) for b in range(k)] for f in out[1]]
    base=triv+e1
    r0=sp.Matrix(triv).rank()
    r1=sp.Matrix(base).rank()
    r2=sp.Matrix(out[2]).rank() if out[2] else 0
    res[w]=dict(w1=out[1],w2=out[2],triv_rank=r0,w1nontriv=r1-r0,w2total=r2)
    print(w,k,'w1 dim',len(out[1]),'w1 nontriv',r1-r0,'w2 dim',r2,'w2 nontriv',r2-r0)
json.dump(res,open('an/laws.json','w'))
