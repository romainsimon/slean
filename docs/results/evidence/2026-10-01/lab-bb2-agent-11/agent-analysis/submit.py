import json,sympy as sp,subprocess
res=json.load(open('an/laws.json'));rules=json.load(open('an/rules.json'))
for w in range(16):
    r=res[str(w)];k=4 if len(rules[str(w)])==64 else 3
    triv=[[1]*(k*k)]
    for g in range(k):
        triv.append([(1 if b==g else 0)-(1 if a==g else 0) for a in range(k) for b in range(k)])
    span=list(triv)
    def emb(f):return [f[a] for a in range(k) for b in range(k)]
    for wd,cands in((1,r['w1']),(2,r['w2'])):
        for f in cands:
            v=emb(f) if wd==1 else f
            if sp.Matrix(span+[v]).rank()>sp.Matrix(span).rank():
                span.append(v)
                out=subprocess.run(['./lab','propose',json.dumps({"kind":"conservation","world":f"w{w}","w":wd,"f":f})],capture_output=True,text=True).stdout
                print(w,wd,f,out.strip())
