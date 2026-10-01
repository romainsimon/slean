import json, sympy as sp
L=json.load(open('an/laws.json'))
ks=[4,4,3,3,4,3,4,3,4,4,4,3,4,4,4,3]
sub={}
def clear(v):
    v=[sp.Rational(x) for x in v]
    d=sp.ilcm(*[x.q for x in v]); v=[int(x*d) for x in v]
    g=sp.igcd(*v) or 1
    return [x//g for x in v]
for wd in range(16):
    k=ks[wd]; claims=[]
    triv1=[[1]*k]
    ns1=[[sp.Rational(x) for x in v] for v in L[str(wd)]['1']]
    cur=sp.Matrix(triv1)
    for v in ns1:
        m=sp.Matrix.vstack(cur,sp.Matrix([v]))
        if m.rank()>cur.rank():
            cur=m; claims.append((1,clear(v)))
    # w=2 trivial: const, u(b)-u(a)
    triv=[[1]*(k*k)]
    for u in range(k-1):
        f=[0]*(k*k)
        for a in range(k):
            for b in range(k):
                f[a*k+b]=(b==u)-(a==u)
        triv.append(f)
    cur=sp.Matrix(triv)
    for (w,f) in claims:
        e=[f[a] for a in range(k) for b in range(k)]
        cur=sp.Matrix.vstack(cur,sp.Matrix([e]))
    assert cur.rank()==k+len([1 for c in claims])
    for v in L[str(wd)]['2']:
        v=[sp.Rational(x) for x in v]
        m=sp.Matrix.vstack(cur,sp.Matrix([v]))
        if m.rank()>cur.rank():
            cur=m; claims.append((2,clear(v)))
    sub[wd]=claims
    print(wd,claims)
json.dump(sub,open('an/claims.json','w'))
