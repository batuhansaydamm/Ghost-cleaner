import wave, numpy as np, json
w=wave.open('../src/audio16k.wav'); sr=w.getframerate()
x=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
hop=160; n=len(x)//hop
rms=np.sqrt((x[:n*hop].reshape(n,hop)**2).mean(1)); db=20*np.log10(rms+1e-6)
def snap(t,win=0.18):
    a=int((t-win)*100); b=int((t+win)*100)
    seg=db[a:b]; i=int(np.argmin(seg)); return round((a+i)/100,2), round(float(seg[i]),1)
EDL=[(132.70,137.25),(1.05,4.35),(4.85,6.75),(8.45,10.40),(13.80,16.05),(25.55,27.10),(30.85,33.50),(41.80,44.30),(45.85,47.20),(49.20,52.30),(84.35,87.20),(131.45,132.75),(137.25,139.70)]
for a,b in EDL:
    print((a,b), snap(a), snap(b))
