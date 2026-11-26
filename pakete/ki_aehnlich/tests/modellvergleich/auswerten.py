"""Modellvergleich (registry #242), Schritt 3: Auswertung. Siehe LIESMICH.md."""
import json,sys,subprocess,numpy as np
S=json.load(open('satz.json')); N=len(S); typ=[d['typ'] for d in S]; mappe=[d['mappe'] for d in S]
alle=sorted(set(typ)); SCHWELLE=0.45; FUELL='finanzen:kontoauszug'
def paare(D): C=D@D.T; return C[np.triu_indices(N,1)]
ref=np.sort(paare(np.load('wasm-256.npz')['D']))
def faelle(D,abb,fuellN):
    C=abb(D@D.T); fv=[i for i in range(N) if typ[i]==FUELL]; out=[]
    for i in range(N):
        if fuellN and typ[i]==FUELL: continue
        best={}
        for k in range(fuellN):
            s=C[i,fv[k%len(fv)]]
            if s>=SCHWELLE: best[f'f{k}']=(s,FUELL)
        for j in range(i):
            s=C[i,j]
            if s>=SCHWELLE and (mappe[j] not in best or best[mappe[j]][0]<s): best[mappe[j]]=(s,typ[j])
        ae=sorted(best.values(),key=lambda x:-x[0])[:10]
        anz={}
        for j in range(i): anz.setdefault(typ[j],set()).add(mappe[j])
        if fuellN: anz.setdefault(FUELL,set()).update(f'f{k}' for k in range(fuellN))
        out.append({'soll':typ[i],'typen':[{'id':t,'name':t,'anzahl':len(anz.get(t,()))} for t in alle],'aehnliche':[{'typ':t,'aehnlichkeit':round(float(s),3)} for s,t in ae]})
    return out
def klass(f):
    json.dump(f,open('f.json','w')); return json.loads(subprocess.run(['node',__import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)),'modul.mjs'),'klass','f.json'],capture_output=True,text=True).stdout)
zeilen=[]
for name in sys.argv[1:]:
    z=np.load(f'{name}.npz'); D,Q=z['D'],z['Q']
    srt=np.sort(paare(D)); q=np.linspace(0,1,len(srt)); abb=lambda C:np.interp(np.interp(C,srt,q),np.linspace(0,1,len(ref)),ref)
    C=D@D.T; np.fill_diagonal(C,-9)
    nn=np.mean([typ[int(np.argmax(C[i,:i]))]==typ[i] for i in range(1,N)])
    mit=[i for i in range(N) if S[i]['titel'].strip()]; R=Q[mit]@D.T
    r5=np.mean([i in np.argsort(-R[k])[:5] for k,i in enumerate(mit)])
    a=klass(faelle(D,abb,0)); b=klass(faelle(D,abb,200))
    zeilen.append((name,nn,a['richtig']/a['geliefert'],a['geliefert'],b['richtig']/b['geliefert'],b['fuell'],r5))
    print(f"{name:11} 1-NN {nn:.1%} | Paket {a['richtig']/a['geliefert']:.1%} ({a['geliefert']}) | +200 {b['richtig']/b['geliefert']:.1%} fälschl. KA {b['fuell']} | Suche R@5 {r5:.1%}",flush=True)
