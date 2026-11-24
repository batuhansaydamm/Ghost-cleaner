import subprocess, json
SRC='../src/raw.mp4'
G="eq=contrast=1.07:saturation=1.10:gamma=0.97,curves=master='0/0.035 0.25/0.21 0.5/0.49 0.78/0.80 1/0.96':red='0/0.01 0.5/0.51 1/0.99':blue='0/0.05 0.5/0.48 1/0.93',colorbalance=rs=-0.04:bs=0.05:rh=0.03:bh=-0.03,hue=s=1.04"
# id, in, out, zoom, speed
EDL=[("hook",132.92,137.30,1.06,1),("intro",1.07,4.51,1.0,1),("tee1",4.69,6.71,1.10,1),("tee2",8.58,10.56,1.0,1),
     ("tee3",13.68,16.15,1.18,1),("cap1",25.41,27.08,1.0,1),("cap2",30.95,33.66,1.12,1),("jkt1",41.97,44.29,1.0,1),
     ("jkt2",49.09,52.46,1.06,1),("ramp",63.20,73.20,1.0,4),("tones",84.38,87.26,1.10,1),("collab",131.40,132.90,1.0,1),("end",137.30,139.87,1.15,1)]
segs=[];t=0
for i,(n,a,b,z,sp) in enumerate(EDL):
    d=(b-a)/sp; out=f"s{i:02d}.mp4"
    crop=f"crop=iw/{z}:ih/{z}:(iw-iw/{z})/2:min(ih-ih/{z}\\,max(0\\,ih*0.55-ih/{z}/2)),scale=1080:1920:flags=lanczos," if z!=1 else ""
    if sp==1:
        vf=f"{crop}{G},fps=30,format=yuv420p"
        af=f"afade=t=in:d=0.015,afade=t=out:st={d-0.03:.3f}:d=0.03"
        cmd=['ffmpeg','-v','error','-y','-ss',str(a),'-t',f"{b-a:.3f}",'-i',SRC,'-vf',vf,'-af',af,'-ar','48000','-ac','2']
    else:
        vf=f"setpts=(PTS-STARTPTS)/{sp},tmix=frames=3,{crop}{G},fps=30,format=yuv420p"
        cmd=['ffmpeg','-v','error','-y','-ss',str(a),'-t',f"{b-a:.3f}",'-i',SRC,'-f','lavfi','-t',f"{d:.3f}",'-i','anullsrc=r=48000:cl=stereo','-map','0:v','-map','1:a','-vf',vf]
    cmd+=['-c:v','libx264','-crf','14','-preset','medium','-c:a','pcm_s16le','-shortest',out.replace('.mp4','.mov')]
    import os
    if not os.path.exists(out.replace(".mp4",".mov")): subprocess.run(cmd,check=True)
    segs.append(dict(id=n,src_in=a,src_out=b,start=round(t,3),dur=round(d,3),zoom=z,speed=sp)); t+=d
open('list.txt','w').write(''.join(f"file 's{i:02d}.mov'\n" for i in range(len(EDL))))
subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i','list.txt','-c:v','libx264','-crf','15','-preset','medium','-r','30','-c:a','pcm_s16le','base_raw.mov'],check=True)
json.dump(segs,open('segs.json','w'),indent=1); print(round(t,3))
for s in segs: print(s)
