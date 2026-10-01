import re, itertools, sympy, sys
txt=open('README.md').read()
W={}
for m in re.finditer(r'- `(w\d+)`: k=(\d), rule table \[(.*?)\]',txt):
    W[m.group(1)]=(int(m.group(2)),[int(x) for x in m.group(3).split(',')])
def step(r,k,x):
    n=len(x);return tuple(r[x[i]*k*k+x[(i+1)%n]*k+x[(i+2)%n]] for i in range(n))
def feat(x,k,w):
    n=len(x);v=[0]*(k**w)
    for i in range(n):
        c=0
        for j in range(w):c=c*k+x[(i+j)%n]
        v[c]+=1
    return v
W1={}
for name,(k,r) in W.items():
    maxn=7 if k==3 else 6
    for w in (1,2):
        rows=set()
        for n in range(1,maxn+1):
            for x in itertools.product(range(k),repeat=n):
                a=feat(x,k,w);b=feat(step(r,k,x),k,w)
                d=tuple(q-p for p,q in zip(a,b))
                if any(d):rows.add(d)
        M=sympy.Matrix(list(rows))
        ns=M.nullspace()
        # remove trivial: constants and gradients g(a)-g(b)
        triv=[]
        if w==1: triv=[[1]*k]
        else:
            triv=[[1]*(k*k)]
            for g in range(k):
                v=[0]*(k*k)
                for a in range(k):
                    for b in range(k):
                        c=a*k+b
                        v[c]+=(a==g)-(b==g)
                triv.append(v)
        if w==2:
            for f1 in W1.get(name,[]):
                triv.append([f1[a] for a in range(k) for b in range(k)])
        T=sympy.Matrix(triv)
        base=T.rank()
        res=[]
        cur=T
        for v in ns:
            t=cur.col_join(v.T)
            if t.rank()>cur.rank():cur=t;res.append(v)
        out=[]
        for v in res:
            from math import lcm
            den=lcm(*[int(q.q) for q in v]);out.append([int(q*den) for q in v])
        if w==1: W1[name]=out
        print(name,w,'nullity',len(ns),'nontrivial',len(res),out,flush=True)
