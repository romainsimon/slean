import subprocess,json,sys
def db(k,n):
    a=[0]*k*n;s=[]
    def f(t,p):
        if t>n:
            if n%p==0:s.extend(a[1:p+1])
        else:
            a[t]=a[t-p];f(t+1,p)
            for j in range(a[t-p]+1,k):
                a[t]=j;f(t+1,t)
    f(1,1);return s
ks={0:4,1:4,2:3,3:4,4:3,5:3,6:4,7:4,8:4,9:3,10:4,11:4,12:4,13:3,14:3,15:4}
rules={}
for w,k in ks.items():
    s=db(k,3);N=len(s)
    out=subprocess.run(['./lab','experiment',f'w{w}',''.join(map(str,s)),'1'],capture_output=True,text=True).stdout.split()
    n=list(map(int,out[1]))
    t=[None]*k**3
    for i in range(N):
        c=s[i]*k*k+s[(i+1)%N]*k+s[(i+2)%N]
        t[c]=n[i]
    assert None not in t
    rules[w]=t
json.dump(rules,open('an/rules.json','w'))
print(rules)
