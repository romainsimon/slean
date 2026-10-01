import json, itertools, sympy as sp
rules={int(w):r for w,r in json.load(open('an/rules.json')).items()}
ks=[4,4,3,3,4,3,4,3,4,4,4,3,4,4,4,3]
def idx(t,k):
    v=0
    for x in t: v=v*k+x
    return v
def laws(w,k,r):
    nf=k**w; nh=k**(w+1)
    rows=[]
    for t in itertools.product(range(k),repeat=w+2):
        row=[0]*(nf+nh)
        # new window i: rule applied at positions 0..w-1 -> cells t[j..j+2]
        nw=[r[idx(t[j:j+3],k)] for j in range(w)]
        row[idx(nw,k)]+=1
        row[idx(t[:w],k)]-=1
        row[nf+idx(t[1:],k)]-=1
        row[nf+idx(t[:-1],k)]+=1
        rows.append(row)
    M=sp.Matrix(rows)
    ns=M.nullspace()
    return [list(v[:nf]) for v in ns],nf
out={}
for wd in range(16):
    k=ks[wd]; r=rules[wd]
    res={}
    for w in (1,2):
        ns,nf=laws(w,k,r)
        sub=sp.Matrix([v for v in ns]) if ns else sp.zeros(0,nf)
        rk=sub.rank() if ns else 0
        res[w]=(rk,ns)
    # trivial dim: w=1:1 ; w=2:k
    print(wd,k,'dim w1',res[1][0],'(nontriv',res[1][0]-1,') dim w2',res[2][0],'(nontriv',res[2][0]-k,')')
    out[wd]={w:[[str(x) for x in v] for v in res[w][1]] for w in (1,2)}
json.dump(out,open('an/laws.json','w'))
