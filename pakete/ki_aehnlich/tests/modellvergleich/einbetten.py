"""Modellvergleich (registry #242), Schritt 2: Vektoren je Modell. Siehe LIESMICH.md."""
import json,sys,time,numpy as np
from tokenizers import Tokenizer
from safetensors.numpy import load_file
S=json.load(open('satz.json'))
def statisch(ordner,dim=None):
    tok=Tokenizer.from_file(f'{ordner}/tokenizer.json'); E=list(load_file(f'{ordner}/model.safetensors').values())[0].astype(np.float32)
    if dim: E=E[:,:dim]
    def f(t):
        ids=tok.encode(t,add_special_tokens=False).ids
        v=E[ids].mean(0) if ids else np.zeros(E.shape[1],np.float32); return v/(np.linalg.norm(v) or 1)
    return f
def e5():
    import onnxruntime as ort
    tok=Tokenizer.from_file('hf/e5/tokenizer.json'); tok.enable_truncation(512)
    s=ort.InferenceSession('hf/e5/model.onnx',providers=['CPUExecutionProvider']); namen=[i.name for i in s.get_inputs()]
    def f(t):
        e=tok.encode(t); ids=np.array([e.ids]); m=np.array([e.attention_mask]); feed={'input_ids':ids,'attention_mask':m}
        if 'token_type_ids' in namen: feed['token_type_ids']=np.zeros_like(ids)
        h=s.run(None,feed)[0][0]; v=(h*m[0][:,None]).sum(0)/m.sum(); return v/np.linalg.norm(v)
    return f
modelle={'mrl-256':lambda:statisch('hf/mrl',256),'mrl-512':lambda:statisch('hf/mrl',512),'mrl-1024':lambda:statisch('hf/mrl',1024),'potion-256':lambda:statisch('hf/potion'),'e5-small':e5}
for name in sys.argv[1:]:
    f=modelle[name](); vor='passage: ' if name=='e5-small' else ''; fq='query: ' if name=='e5-small' else ''
    t0=time.time(); D=np.stack([f(vor+d['text']) for d in S]); ms=(time.time()-t0)*1000/len(S)
    Q=np.stack([f(fq+d['titel']) for d in S])
    np.savez(f'{name}.npz',D=D,Q=Q); print(name,D.shape,f'{ms:.1f} ms/Dok (Python)')
