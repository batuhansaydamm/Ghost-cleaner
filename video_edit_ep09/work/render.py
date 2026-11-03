#!/usr/bin/env python3
"""Söylesem Ayıp mı? ep09 renderer — reads edit_plan.json, writes exports/.
Usage: python3 render.py <source.mp4> <outdir> [--preview]
"""
import json, subprocess, sys, os, math, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC, OUT = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
plan = json.load(open(os.path.join(HERE, "edit_plan.json")))
W, H, FPS = 1080, 1920, 30
SW, SH = 720, 1280
TC_AT, TC_LEN, HOLD = 5.8, 1.4, 0.8
SRC_DUR = 50.0
DUR = SRC_DUR + TC_LEN + HOLD
NF = int(round(DUR * FPS))

SERIF_B = "/usr/share/fonts/truetype/crosextra/Caladea-Bold.ttf"
SERIF_R = "/usr/share/fonts/truetype/crosextra/Caladea-Regular.ttf"
INK = (34, 28, 23)          # warm near-black
CREAM = (237, 228, 211)     # series cream

def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)

beats = [b for b in plan["beats"] if b["src_start"] is not None]

def beat_at(ts):
    for b in beats:
        if b["src_start"] <= ts < b["src_end"]:
            return b
    return beats[-1]

def camera(ts):
    """returns zoom, (cx, cy) anchor in source fraction"""
    b = beat_at(ts)
    s, e = b["src_start"], b["src_end"]
    c0, c1 = b["crop_scale"]
    ax, ay = b["anchor"]
    p = (ts - s) / (e - s)
    role = b["narrative_role"]
    z = c0 + (c1 - c0) * ease(p)
    if role == "CLIMAX":                       # single hard punch-in at 44.9
        z = c0 + (c1 - c0) * ease((ts - 44.9) / 0.3)
    if s == 33.70:                             # triple steps 108 -> 114 at 36.0
        z = 1.08 + 0.06 * ease((ts - 36.0) / 0.25)
    if s == 15.97 and 16.4 <= ts < 18.0:       # hands detail insert
        z, ax, ay = 2.6 + 0.08 * (ts - 16.4) / 1.6, 0.27, 0.84
    if s == 21.10 and 21.6 <= ts < 23.2:       # eye-line detail insert
        z, ax, ay = 1.9 + 0.05 * (ts - 21.6) / 1.6, 0.5, 0.37
    return z, ax, ay

def frame_inset(ts):
    if 30.37 <= ts < 33.70:
        return 0.04 * ease((ts - 30.37) / 3.33)
    if 33.70 <= ts < 38.93:
        return 0.04 + 0.05 * ease((ts - 33.70) / 5.23)
    return 0.0

def crop_resize(src_img, z, ax, ay):
    cw, ch = SW / z, SH / z
    x0 = min(max(ax * SW - cw / 2, 0), SW - cw)
    y0 = min(max(ay * SH - ch / 2, 0), SH - ch)
    return src_img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))

# ---------- typography ----------
_fc = {}
def font(path, size):
    k = (path, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(path, size)
    return _fc[k]

def tracked_line(draw, xy, text, f, fill, tracking, align_w=None, anchor="l"):
    widths = [f.getlength(c) for c in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x, y = xy
    if anchor == "c":
        x -= total / 2
    elif anchor == "r":
        x -= total
    for c, w in zip(text, widths):
        draw.text((x, y), c, font=f, fill=fill)
        x += w + tracking
    return total

def text_layer(lines, size, pos, anchor="l", tracking=4, leading=1.08, path=SERIF_B):
    lay = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(lay)
    f = font(path, size)
    x, y = pos
    for ln in lines:
        tracked_line(d, (x, y), ln, f, 255, tracking, anchor=anchor)
        y += size * leading
    return lay

# editorial text events in OUTPUT time
def o(t): return t if t < TC_AT else t + TC_LEN
EV = [
    # (start, end, lines, size, pos, anchor, masked)
    (o(5.95), o(7.62), ["SESSİZ"], 120, (90, 210), "l", False),
    (o(7.75), o(8.86), ["ÖLÇÜLÜ"], 120, (90, 1500), "l", False, CREAM),
    (o(9.05), o(11.95), ["KABUL", "EDİLEBİLİR"], 112, (70, 1440), "l", False, CREAM),
    (o(24.60), o(27.28), ["KİMSE “DEĞİŞ”", "DEMEDİ."], 84, (70, 150), "l", True),
    (o(27.95), o(30.32), ["AMA", "DEĞİŞTİK."], 118, (540, 165), "c", False),
    (o(39.15), o(42.30), ["KABUL EDİLMEK İÇİN", "DÖNÜŞTÜĞÜN KİŞİYE", "ALIŞMAK"], 74, (540, 1400), "c", False, CREAM),
    (o(47.05), DUR + 1, ["ŞU AN YAŞADIĞIMIZ", "HAYAT KİMİN?"], 84, (540, 190), "c", False),
]
_tl = {}
def ev_layer(i):
    if i not in _tl:
        s, e, lines, size, pos, anc, m = EV[i][:7]
        _tl[i] = text_layer(lines, size, pos, anc)
    return _tl[i]

def apply_text(img, t):
    for i, ev in enumerate(EV):
        s, e, lines, size, pos, anc, masked = ev[:7]
        col = ev[7] if len(ev) > 7 else INK
        if not (s <= t < e):
            continue
        a = ease((t - s) / 0.35) * (1 - ease((t - (e - 0.3)) / 0.3))
        drift = int(round(4 * (1 - ease((t - s) / 0.8))))  # 4px micro vertical drift
        lay = ev_layer(i)
        if drift:
            lay = lay.transform(lay.size, Image.AFFINE, (1, 0, 0, 0, 1, -drift))
        alpha = np.asarray(lay, dtype=np.float32) / 255.0 * a
        if masked:  # text passes behind subject: dark hair/shirt occlude
            lum = np.asarray(img.convert("L"), dtype=np.float32) / 255.0
            occ = np.clip((lum - 0.30) / 0.12, 0, 1)
            occ = np.asarray(Image.fromarray((occ * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.5)), dtype=np.float32) / 255
            alpha *= occ
        arr = np.asarray(img, dtype=np.float32)
        ink = np.array(col, dtype=np.float32)
        arr = arr * (1 - alpha[..., None]) + ink * alpha[..., None]
        img = Image.fromarray(arr.astype(np.uint8))
    return img

# ---------- title card ----------
def title_card(p):
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    s = 1.0 + 0.02 * p
    f1 = font(SERIF_B, int(150 * s))
    tracked_line(d, (540, 760), "SÖYLESEM", f1, INK, 6, anchor="c")
    tracked_line(d, (540, 760 + 165 * s), "AYIP MI?", f1, INK, 6, anchor="c")
    d.line([(470, 1150), (610, 1150)], fill=INK, width=3)
    tracked_line(d, (540, 1185), "BÖLÜM 9", font(SERIF_R, 40), INK, 10, anchor="c")
    return img

# ---------- video ----------
def render_video():
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-f", "rawvideo", "-pix_fmt", "rgb24", "-r", str(FPS), "-"],
                           stdout=subprocess.PIPE)
    vf = ("eq=contrast=0.96:saturation=0.94:brightness=0.005,"
          "colorbalance=rs=0.015:bs=-0.02:rm=0.02:bm=-0.025:rh=0.01:bh=-0.015,"
          "curves=all='0/0.02 0.5/0.5 1/0.97',noise=alls=3:allf=t,"
          f"fade=t=out:st={DUR-0.6:.2f}:d=0.6,format=yuv420p")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-profile:v", "high",
                            os.path.join(OUT, "_video.mp4")], stdin=subprocess.PIPE)
    fsz = SW * SH * 3
    src_frames_read = 0
    cur_src = None
    hist = []           # rendered (pre-text) frames for ghost reflection
    last_out = None
    for n in range(NF):
        t = n / FPS
        if TC_AT <= t < TC_AT + TC_LEN:
            img = title_card((t - TC_AT) / TC_LEN)
            k = (t - TC_AT)
            if k < 0.2 and last_out is not None:   # 0.2s dissolve in
                img = Image.blend(last_out, img, k / 0.2)
            enc.stdin.write(img.tobytes()); continue
        ts = t if t < TC_AT else t - TC_LEN
        hold = ts >= SRC_DUR - 1 / FPS
        need = min(int(round(ts * FPS)), int(SRC_DUR * FPS) - 1)
        while src_frames_read <= need:
            buf = dec.stdout.read(fsz)
            if len(buf) < fsz: break
            cur_src = Image.frombytes("RGB", (SW, SH), buf); src_frames_read += 1
        z, ax, ay = camera(min(ts, SRC_DUR - 0.01))
        img = crop_resize(cur_src, z, ax, ay)
        hist.append(img); hist = hist[-8:]
        # delayed reflection (climax)
        if 45.0 <= ts < 46.2 and len(hist) > 6:
            g = (min(ts - 45.0, 46.2 - ts) / 0.3)
            ghost = hist[-7].transform((W, H), Image.AFFINE, (1, 0, -46, 0, 1, 0), resample=Image.BICUBIC)
            img = Image.blend(img, ghost, 0.16 * min(g, 1))
        # frame narrowing
        f = frame_inset(ts)
        if f > 0:
            inner = img
            img = Image.new("RGB", (W, H), CREAM)
            ix, iy = int(W * f), int(H * f)
            img.paste(inner.crop((ix, iy, W - ix, H - iy)), (ix, iy))
        img = apply_text(img, t)
        last_out = img
        enc.stdin.write(img.tobytes())
    enc.stdin.close(); enc.wait(); dec.kill()

# ---------- audio ----------
SR = 48000
def read_wav(p):
    w = wave.open(p); a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return a.reshape(-1, w.getnchannels())

def write_wav(p, a):
    a = np.clip(a, -1, 1); w = wave.open(p, "wb"); w.setnchannels(a.shape[1]); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((a * 32767).astype(np.int16).tobytes()); w.close()

def render_audio():
    tmp = os.path.join(OUT, "_src.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-vn", "-ac", "2", "-ar", str(SR), tmp], check=True)
    a = read_wav(tmp)
    cut = int(TC_AT * SR); fd = int(0.012 * SR)
    pre, post = a[:cut].copy(), a[cut:].copy()
    pre[-fd:] *= np.linspace(1, 0, fd)[:, None]; post[:fd] *= np.linspace(0, 1, fd)[:, None]
    dia = np.concatenate([pre, np.zeros((int(TC_LEN * SR), 2), np.float32), post, np.zeros((int(HOLD * SR) + SR, 2), np.float32)])
    dia = dia[:int(DUR * SR)]
    write_wav(os.path.join(OUT, "_dialog_raw.wav"), dia)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(OUT, "_dialog_raw.wav"), "-af",
                    "highpass=f=80,afftdn=nr=8:nf=-42,equalizer=f=3500:t=q:w=1.2:g=1.5,acompressor=threshold=-24dB:ratio=2.5:attack=8:release=120,loudnorm=I=-15:TP=-1.5:LRA=9",
                    "-ar", str(SR), os.path.join(OUT, "_dialog.wav")], check=True)
    # minimal ambient pad (generated)
    n = int(DUR * SR); t = np.arange(n) / SR
    chords = [[146.83, 220.0, 277.18, 369.99], [123.47, 185.0, 220.0, 293.66], [130.81, 196.0, 246.94, 329.63], [146.83, 220.0, 277.18, 369.99]]
    pad = np.zeros(n, np.float32)
    seg = 9.0
    for ci in range(int(DUR // seg) + 2):
        ch = chords[ci % len(chords)]
        st = TC_AT + ci * seg - 2.0
        env = np.clip((t - st) / 3.0, 0, 1) * np.clip((st + seg + 4.0 - t) / 3.0, 0, 1)
        env = env ** 1.5
        for k, fq in enumerate(ch):
            ph = np.random.rand() * 6.28
            lfo = 0.75 + 0.25 * np.sin(2 * np.pi * (0.07 + 0.03 * k) * t + ph)
            v = np.sin(2 * np.pi * fq * t + ph) + np.sin(2 * np.pi * fq * 1.003 * t) * 0.6 + 0.12 * np.sin(4 * np.pi * fq * t)
            pad += (env * lfo * v * (0.9 ** k)).astype(np.float32)
    # soft air transition into title card
    rng = np.random.default_rng(1)
    noise = rng.standard_normal(n).astype(np.float32)
    k = np.ones(400) / 400; noise = np.convolve(noise, k, "same") * 18
    air_env = np.clip((t - (TC_AT - 0.7)) / 0.7, 0, 1) * np.clip((TC_AT + 0.5 - t) / 0.5, 0, 1)
    pad_env = np.clip((t - TC_AT) / 0.8, 0, 1)
    # automation (dB)
    db = np.zeros(n)
    db += np.where(t > o(38.93), -1.5, 0)
    db += np.where(t > o(42.37), -2.0, 0)
    db += -12 * np.clip((t - o(46.6)) / 1.5, 0, 1)
    gain = 10 ** (db / 20)
    m = pad * pad_env * gain
    m = m / (np.sqrt(np.mean((pad * pad_env) ** 2) + 1e-9)) * 10 ** (-33 / 20)
    m += noise * air_env * 10 ** (-38 / 20) / (np.sqrt(np.mean(noise ** 2)) + 1e-9)
    # fade end
    m *= np.clip((DUR - t) / 0.6, 0, 1)
    music = np.stack([m, np.roll(m, 240)], 1)
    d = read_wav(os.path.join(OUT, "_dialog.wav"))[:n]
    if len(d) < n: d = np.concatenate([d, np.zeros((n - len(d), 2), np.float32)])
    d *= np.clip((DUR - t) / 0.6, 0, 1)[:, None]
    write_wav(os.path.join(OUT, "_mix.wav"), d + music)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    render_audio()
    render_video()
    final = os.path.join(OUT, "ep09_v01_final_1080x1920.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(OUT, "_video.mp4"), "-i", os.path.join(OUT, "_mix.wav"),
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-af", "alimiter=limit=0.89",
                    "-movflags", "+faststart", "-shortest", final], check=True)
    for f in ["_src.wav", "_dialog_raw.wav", "_dialog.wav", "_mix.wav", "_video.mp4"]:
        os.remove(os.path.join(OUT, f))
    print("done", final)
