"""Söylesem Ayıp mı? — Reels kurgusu (stil rehberine göre).

Kullanım: python3 render.py <kaynak.mp4> <çıktı_klasörü> [--no-music] [--preview]
"""
import json, math, subprocess, sys, os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC = sys.argv[1]
OUT = sys.argv[2]
NO_MUSIC = "--no-music" in sys.argv
PREVIEW = "--preview" in sys.argv
HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT, exist_ok=True)

EPISODE = os.environ.get("EPISODE", "1")
W, H, FPS = 1080, 1920, 30
SW, SH = 720, 1280

# ---------------------------------------------------------------- palette / fonts
CREAM = (237, 228, 211)       # #EDE4D3
INK = (35, 26, 20)            # koyu kahve-siyah
SERIF = os.path.join(HERE, "fonts", "PlayfairDisplay.ttf")
SANS_MED = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
SANS_REG = "/usr/share/fonts/opentype/inter/Inter-Regular.otf"


def serif(size, wght=700):
    f = ImageFont.truetype(SERIF, size)
    try:
        f.set_variation_by_axes([wght])
    except Exception:
        pass
    return f


def sans(size, path=SANS_MED):
    return ImageFont.truetype(path, size)

# ---------------------------------------------------------------- timeline
# Kaynak süre 50.0 sn. Jenerik, açılış sorularından hemen sonra (kaynak 5.8 sn'deki kesmede) girer.
JEN_AT, JEN_LEN = 5.8, 1.5
SRC_END = 50.0
TAIL = 1.3                       # kapanışta yavaş zoom out + siyaha fade için
TOTAL = SRC_END + JEN_LEN + TAIL
NFRAMES = int(round(TOTAL * FPS))


def out2src(t):
    """Çıktı zamanı -> (tür, kaynak zamanı)."""
    if t < JEN_AT:
        return "src", t
    if t < JEN_AT + JEN_LEN:
        return "jen", None
    s = t - JEN_LEN
    return "src", min(s, SRC_END - 1.0 / FPS)


def src2out(s):
    return s if s < JEN_AT else s + JEN_LEN

# ---------------------------------------------------------------- framing (kaynak zamanına göre)
# (başlangıç, bitiş, zoom_baş, zoom_son)  — kademeler: geniş 1.00 / orta ~1.12 / yakın ~1.32
# Kademe değişimleri kaynağın kendi jump cut'larına denk getirildi.
ZOOM = [
    (0.00, 12.00, 1.00, 1.025),   # geniş — açılış soruları, gevşek anlatım
    (12.00, 15.97, 1.00, 1.13),   # "Ama ne zaman..." — genişten yavaş zoom in (orta)
    (15.97, 27.33, 1.00, 1.03),   # geniş — sorular + üçlemenin 1. satırı
    (27.33, 30.37, 1.10, 1.12),   # üçleme 2. satır — bir kademe yakın
    (30.37, 42.37, 1.20, 1.23),   # üçleme 3. satır ve en sert tespit
    (42.37, 48.10, 1.00, 1.02),   # soru — geniş
]
PUNCH_AT, PUNCH_LEN, CLOSE_Z = 48.10, 0.5, 1.32   # kapanış: tek hamlede yakın (tek punch-in)
ZOOM_OUT_AT = 49.70                                # kapanış cümlesi bitti -> yavaş zoom out


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def zoom_at(out_t):
    s = out_t - JEN_LEN if out_t >= JEN_AT + JEN_LEN else out_t
    for a, b, z0, z1 in ZOOM:
        if a <= s < b:
            return z0 + (z1 - z0) * (s - a) / (b - a)
    if s < PUNCH_AT + PUNCH_LEN:
        z0 = ZOOM[-1][3]
        return z0 + (CLOSE_Z - z0) * smooth((s - PUNCH_AT) / PUNCH_LEN)
    if s < ZOOM_OUT_AT:
        return CLOSE_Z
    end = SRC_END + TAIL
    return CLOSE_Z - 0.14 * smooth((s - ZOOM_OUT_AT) / (end - ZOOM_OUT_AT))


CX, CY = 0.5, 0.38   # yüz merkezi (kaynak çekimlerde kişi ortada)


def crop_zoom(img, z):
    h, w = img.shape[:2]
    cw, ch = w / z, h / z
    x0 = min(max(CX * w - cw / 2, 0), w - cw)
    y0 = min(max(CY * h - ch / 2, 0), h - ch)
    M = np.float32([[W / cw, 0, -x0 * W / cw], [0, H / ch, -y0 * H / ch]])
    interp = cv2.INTER_LANCZOS4 if img.ndim == 3 else cv2.INTER_LINEAR
    return cv2.warpAffine(img, M, (W, H), flags=interp, borderMode=cv2.BORDER_REPLICATE)

# ---------------------------------------------------------------- subtitles (kaynak zamanı)
SUBS = [
    (0.43, 3.08, "Kendimizden ödün vermek bizi uyumlu biri yapar mı?"),
    (3.34, 5.73, "Peki kendimiz olmak ayıp mı?"),
    (5.90, 7.55, "Her ortama biraz uyum sağlıyoruz."),
    (7.92, 10.24, "Biraz daha sessiz, biraz daha ölçülü,"),
    (10.58, 11.85, "biraz daha kabul edilebilir."),
    (12.02, 13.75, "Ama ne zaman uyum sağlamayı bırakıp"),
    (14.09, 15.82, "kendimizi değiştirmeye başlıyoruz?"),
    (16.24, 18.53, "Gerçekten hoşumuza giden şeyleri mi seviyoruz?"),
    (18.57, 20.96, "Yoksa sevmemiz beklenen şeylere mi alışıyoruz?"),
    (21.12, 24.24, "Bir şey söylemeden önce kabul edilip edilmeyeceğine bakıyoruz."),
    (24.39, 26.98, "Daha eleştirilmeden kendimizi sansürlüyoruz."),
    (27.40, 30.10, "Kimse bize “değiş” demeden değişmeye başlıyoruz."),
    (30.43, 33.51, "Daha reddedilmeden kendimizden bir şeyler eksiltiyoruz."),
    (33.97, 35.75, "Ve belki de en kötüsü dışlanmak değil…"),
    # 36.30–38.63 "Kabul edilmek için dönüştüğümüz kişiye alışmak." -> EKRAN METNİ
    (39.08, 42.20, "Çünkü insan bir süre sonra rol yaptığını bile unutabilir."),
    (42.53, 44.43, "Kimsenin ne düşüneceğini umursamasaydık,"),
    (44.91, 46.29, "aynı hayatı mı seçerdik?"),
    (46.67, 47.88, "Cevap hayırsa,"),
    # 48.19–49.68 "Şu an yaşadığımız hayat kimin?" -> EKRAN METNİ
]
# alt yazının ekranda kalma süresini bir sonrakine kadar hafifçe uzat
_subs = []
for i, (a, b, t) in enumerate(SUBS):
    nxt = SUBS[i + 1][0] if i + 1 < len(SUBS) else b + 1
    _subs.append((a, min(b + 0.25, nxt - 0.04), t))
SUBS = _subs

# ekran metni (kaynak zamanı): görünür olduğu aralık (fade dahil)
SCREEN = [
    (36.12, 38.93, ["KABUL EDİLMEK İÇİN", "DÖNÜŞTÜĞÜMÜZ", "KİŞİYE ALIŞMAK"]),
    (48.05, SRC_END + 0.9, ["ŞU AN YAŞADIĞIMIZ", "HAYAT KİMİN?"]),
]
FADE = 0.3


def wrap(text, font, maxc=32):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if len(trial) <= maxc or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    lines.append(cur)
    if len(lines) == 2 and len(lines[1]) < 10:      # dengeli satır kırma
        allw = text.split()
        best = None
        for k in range(1, len(allw)):
            l1, l2 = " ".join(allw[:k]), " ".join(allw[k:])
            if len(l1) <= maxc and len(l2) <= maxc:
                d = abs(len(l1) - len(l2))
                if best is None or d < best[0]:
                    best = (d, [l1, l2])
        if best:
            lines = best[1]
    assert len(lines) <= 2, text
    return lines


SUB_FONT = sans(50)
SUB_BOTTOM = H - 250 - 190     # IG arayüzünün kapattığı alt ~250 px'in ve caption alanının üstü


def render_sub(text):
    lines = wrap(text, SUB_FONT)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lh = 66
    y = SUB_BOTTOM - lh * len(lines)
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds, d = ImageDraw.Draw(shadow), ImageDraw.Draw(layer)
    for i, ln in enumerate(lines):
        tw = d.textlength(ln, font=SUB_FONT)
        x = (W - tw) / 2
        ds.text((x, y + i * lh + 3), ln, font=SUB_FONT, fill=(0, 0, 0, 170))
        d.text((x, y + i * lh), ln, font=SUB_FONT, fill=(255, 255, 255, 255))
    shadow = shadow.filter(ImageFilter.GaussianBlur(4))
    return Image.alpha_composite(shadow, layer)


def fit_serif(lines, target_w, wght=700, max_size=200):
    size = max_size
    while size > 20:
        f = serif(size, wght)
        widest = max(f.getlength(l) for l in lines)
        if widest <= target_w:
            return f, size
        size -= 2
    return serif(size, wght), size


def render_screen_text(lines, top):
    f, size = fit_serif(lines, W * 0.78)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    lh = int(size * 0.98)           # sıkı satır aralığı
    for i, ln in enumerate(lines):
        tw = f.getlength(ln)
        d.text(((W - tw) / 2, top + i * lh), ln, font=f, fill=INK + (255,))
    return np.asarray(layer).astype(np.float32) / 255.0

# ---------------------------------------------------------------- color grade (ffmpeg, kaynak üzerinde)
GRADE = ("eq=contrast=0.90:saturation=0.86:gamma=1.02,"
         "colorbalance=rs=0.03:gs=0.01:bs=-0.04:rm=0.035:gm=0.01:bm=-0.035:rh=0.02:bh=-0.03,"
         "curves=all='0/0.055 0.5/0.51 1/0.965'")


def read_src_frames():
    cmd = ["ffmpeg", "-v", "error", "-i", SRC, "-vf", GRADE, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    n = SW * SH * 3
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        yield np.frombuffer(b, np.uint8).reshape(SH, SW, 3)

# ---------------------------------------------------------------- person mask (ekran metni maskelemesi)
_seg = None


def person_mask(frame):
    global _seg
    from rembg import new_session, remove
    if _seg is None:
        _seg = new_session("u2net_human_seg")
    m = np.asarray(remove(Image.fromarray(frame), session=_seg, only_mask=True)).astype(np.float32) / 255.0
    # tavandaki beyaz küre lambayı maskeden çıkar (parlak + doygunluğu düşük + üst bölge)
    hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
    lamp = (hsv[..., 2] > 200) & (hsv[..., 1] < 40)
    lamp[int(SH * 0.40):] = False
    lamp = cv2.dilate(lamp.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
    m[lamp] = 0
    m = cv2.GaussianBlur(m, (0, 0), 1.2)
    return m

# ---------------------------------------------------------------- cover + jenerik
def strip_box(img, text):
    f = sans(34)
    d = ImageDraw.Draw(img, "RGBA")
    tw = d.textlength(text, font=f)
    bx, by, pad = (W - tw) / 2, 150, 18
    d.rounded_rectangle([bx - pad * 1.6, by - pad, bx + tw + pad * 1.6, by + 34 + pad + 6],
                        radius=8, fill=(255, 255, 255, 90))
    d.text((bx, by), text, font=f, fill=INK + (230,))


def make_cover(photo_rgb):
    """Kapak: krem zemin, üst şerit, serif büyük harf başlık (AYIP MI? son satırda), altında fotoğraf."""
    cover = Image.new("RGB", (W, H), CREAM)
    # fotoğraf: alt bölüm, üst kenarı kreme yumuşakça karışır
    ph = Image.fromarray(photo_rgb).convert("RGB")
    pw, phh = W, int(W * ph.height / ph.width)
    ph = ph.resize((pw, phh), Image.LANCZOS)
    top = 300                      # baş, başlığın altında kalsın
    crop = ph.crop((0, 0, pw, H - top))
    alpha = np.ones((crop.height, crop.width), np.float32)
    g = 360
    alpha[:g] = np.linspace(0, 1, g)[:, None] ** 1.6
    cover.paste(crop, (0, top), Image.fromarray((alpha * 255).astype(np.uint8)))
    strip_box(cover, f"Söylesem Ayıp mı?  —  Bölüm {EPISODE}")
    lines = ["KENDİMİZ", "OLMAK", "AYIP MI?"]
    f, size = fit_serif(lines, W * 0.80, wght=800, max_size=230)
    d = ImageDraw.Draw(cover)
    lh = int(size * 0.96)
    y = 270
    for i, ln in enumerate(lines):
        tw = f.getlength(ln)
        d.text(((W - tw) / 2, y + i * lh), ln, font=f, fill=INK)
    return np.asarray(cover)


def make_jenerik():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    f = serif(112, 700)
    t = "Söylesem Ayıp mı?"
    tw = f.getlength(t)
    d.text(((W - tw) / 2, H / 2 - 110), t, font=f, fill=INK)
    f2 = sans(40, SANS_REG)
    t2 = "Bir şey söyleyeceğim."
    tw2 = f2.getlength(t2)
    d.text(((W - tw2) / 2, H / 2 + 60), t2, font=f2, fill=(95, 82, 70))
    return np.asarray(img)

# ---------------------------------------------------------------- audio
def build_audio(path_wav):
    sr = 48000
    # konuşma: temizle + normalize
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-vn", "-ac", "1", "-ar", str(sr),
                    "-af", "highpass=f=75,afftdn=nr=8:nf=-45,loudnorm=I=-14:TP=-1.5:LRA=9",
                    os.path.join(OUT, "_speech.wav")], check=True)
    import soundfile as sf
    sp, _ = sf.read(os.path.join(OUT, "_speech.wav"), dtype="float32")
    sp = sp[: int(SRC_END * sr)]
    a = int(JEN_AT * sr)
    total = int(TOTAL * sr)
    speech = np.zeros(total, np.float32)
    speech[:a] = sp[:a]
    b = a + int(JEN_LEN * sr)
    seg = sp[a:]
    speech[b:b + len(seg)] = seg[: total - b]
    # kesme noktalarında tık olmasın
    for p in (a, b):
        n = 240
        speech[p - n:p] *= np.linspace(1, 0, n)
        speech[p:p + n] *= np.linspace(0, 1, n)

    music = np.zeros(total, np.float32)
    if not NO_MUSIC:
        music = synth_pad(total, sr)
        t = np.arange(total) / sr
        env = np.zeros(total, np.float32)
        jen0, jen1 = JEN_AT, JEN_AT + JEN_LEN
        close0 = src2out(46.60)            # "Cevap hayırsa" — müzik kısılmaya başlar
        lvl_jen = 10 ** (-25 / 20)         # jenerikte tek başına
        lvl_bed = 10 ** (-39 / 20)         # konuşmanın ~20 dB altında
        env = np.where(t < jen0, 0, env)
        m1 = (t >= jen0) & (t < jen1 + 0.3)
        env[m1] = lvl_jen * np.clip((t[m1] - jen0) / 0.25, 0, 1)
        m2 = (t >= jen1 + 0.3) & (t < jen1 + 1.0)
        env[m2] = lvl_jen + (lvl_bed - lvl_jen) * ((t[m2] - jen1 - 0.3) / 0.7)
        m3 = (t >= jen1 + 1.0) & (t < close0)
        env[m3] = lvl_bed
        m4 = (t >= close0) & (t < close0 + 1.2)
        env[m4] = lvl_bed * (1 - (t[m4] - close0) / 1.2)
        rms = np.sqrt(np.mean(music ** 2)) + 1e-9
        music = music / rms * env
    mix = speech + music
    mix = np.clip(mix, -0.98, 0.98)
    sf.write(path_wav, np.stack([mix, mix], 1), sr)


def synth_pad(n, sr):
    """Minimal, düşük tempolu yumuşak synth pad (Am – Fmaj7 – C – G), her akor 4 sn."""
    t = np.arange(n) / sr
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    chords = [[45, 57, 60, 64], [41, 57, 60, 64], [48, 55, 60, 64], [43, 55, 59, 62]]
    out = np.zeros(n, np.float32)
    dur = 4.0
    k = 0
    start = 0.0
    while start < n / sr:
        ch = chords[k % 4]
        s0, s1 = int(start * sr), min(n, int((start + dur + 2.0) * sr))
        tt = t[s0:s1] - start
        env = np.minimum(1, tt / 1.6) * np.clip((dur + 2.0 - tt) / 2.0, 0, 1)
        sig = np.zeros(s1 - s0)
        for i, m in enumerate(ch):
            f = hz(m)
            amp = 0.6 if i == 0 else 0.35
            for det in (-0.004, 0, 0.0045):
                sig += amp * np.sin(2 * np.pi * f * (1 + det) * tt + i)
            sig += amp * 0.12 * np.sin(2 * np.pi * 2 * f * tt)
        out[s0:s1] += (sig * env).astype(np.float32)
        start += dur
        k += 1
    # yumuşat: basit alçak geçiren + yavaş tremolo
    out = np.convolve(out, np.ones(24) / 24, mode="same").astype(np.float32)
    out *= (1 + 0.06 * np.sin(2 * np.pi * 0.15 * t)).astype(np.float32)
    # basit yankı
    rev = out.copy()
    for d_ms, g in ((83, 0.35), (127, 0.28), (191, 0.22), (263, 0.16)):
        d = int(sr * d_ms / 1000)
        rev[d:] += g * out[:-d]
    return rev

# ---------------------------------------------------------------- main render
def main():
    sub_cache = {}
    screen_layers = [(a, b, render_screen_text(lines, top=130 if len(lines) == 3 else 230))
                     for a, b, lines in SCREEN]
    cover = None
    jen = make_jenerik()
    Image.fromarray(jen).save(os.path.join(OUT, "jenerik.png"))

    wav = os.path.join(OUT, "_mix.wav")
    build_audio(wav)

    name = "soylesem_ayip_mi_reels" + ("_muziksiz" if NO_MUSIC else "") + ".mp4"
    outp = os.path.join(OUT, name)
    enc = subprocess.Popen([
        "ffmpeg", "-v", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", wav,
        "-vf", "noise=c0s=4:c0f=t,format=yuv420p",      # sabit, çok ince grain
        "-c:v", "libx264", "-preset", "veryfast" if PREVIEW else "slow", "-crf", "18",
        "-profile:v", "high", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", outp],
        stdin=subprocess.PIPE)

    frames = read_src_frames()
    cur_idx, cur = -1, None
    last_src = None
    mask_cache = {}
    for i in range(NFRAMES):
        t = i / FPS
        kind, s = out2src(t)
        if kind == "src":
            want = min(int(round(s * FPS)), int(SRC_END * FPS) - 1)
            while cur_idx < want:
                try:
                    cur = next(frames)
                    cur_idx += 1
                except StopIteration:
                    break
            z = zoom_at(t)
            img = crop_zoom(cur, z)
            img = cv2.addWeighted(img, 1.35, cv2.GaussianBlur(img, (0, 0), 1.4), -0.35, 0)  # hafif netlik
            s_eff = t - JEN_LEN if t >= JEN_AT + JEN_LEN else t   # kuyruğu da kaynak saatinde say
            frame = img.astype(np.float32) / 255.0

            # ekran metni (maskeli)
            screen_on = False
            for a, b, layer in screen_layers:
                if a <= s_eff < b:
                    screen_on = True
                    alpha = min(1, (s_eff - a) / FADE, (b - s_eff) / FADE)
                    if cur_idx not in mask_cache:
                        mask_cache.clear()
                        mask_cache[cur_idx] = person_mask(cur)
                    m = crop_zoom(mask_cache[cur_idx], z)
                    la = layer[..., 3] * (1 - m) * alpha
                    frame = frame * (1 - la[..., None]) + layer[..., :3] * la[..., None]

            # altyazı (ekran metni varken gizli)
            if not screen_on:
                for a, b, text in SUBS:
                    if a <= s_eff < b:
                        if text not in sub_cache:
                            sub_cache[text] = np.asarray(render_sub(text)).astype(np.float32) / 255.0
                        L = sub_cache[text]
                        fa = min(1, (s_eff - a) / 0.08, (b - s_eff) / 0.08)
                        la = L[..., 3:] * fa
                        frame = frame * (1 - la) + L[..., :3] * la
                        break

            # kapak: ilk kare(ler) — sonra temiz geçiş
            if t < 0.65:
                if cover is None:
                    cover = make_cover(cv2.resize(cur_cover, (SW, SH))).astype(np.float32) / 255.0
                k = 1.0 if t < 0.35 else 1 - smooth((t - 0.35) / 0.3)
                frame = frame * (1 - k) + cover * k

            # kapanış: siyaha fade
            fb0 = src2out(49.85)
            if t > fb0:
                frame *= 1 - smooth((t - fb0) / (TOTAL - fb0 - 0.05))
            out = (np.clip(frame, 0, 1) * 255).astype(np.uint8)
            last_src = out
        else:
            # jenerik — 0.2 sn yumuşak geçiş giriş/çıkış
            u = t - JEN_AT
            k = min(1, u / 0.2, (JEN_LEN - u) / 0.2)
            base = last_src.astype(np.float32) if last_src is not None else jen.astype(np.float32)
            out = (jen.astype(np.float32) * k + base * (1 - k)).astype(np.uint8) if u < 0.2 else jen
        enc.stdin.write(np.ascontiguousarray(out).tobytes())
        if i % 150 == 0:
            print(f"{i}/{NFRAMES}", flush=True)
    enc.stdin.close()
    enc.wait()
    Image.fromarray((cover * 255).astype(np.uint8)).save(os.path.join(OUT, "kapak.jpg"), quality=95)
    write_srt(os.path.join(OUT, "altyazi.srt"))
    for f in ("_speech.wav", "_mix.wav"):
        os.remove(os.path.join(OUT, f))
    print("OK", outp)


def write_srt(path):
    def ts(x):
        ms = int(round(x * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, text) in enumerate(SUBS, 1):
            f.write(f"{i}\n{ts(src2out(a))} --> {ts(src2out(b))}\n" + "\n".join(wrap(text, SUB_FONT)) + "\n\n")


# kapak fotoğrafı: 3.2 sn — orta plan, kameraya bakıyor
def grab(t):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", SRC, "-frames:v", "1", "-vf", GRADE,
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.uint8).reshape(SH, SW, 3)


cur_cover = grab(3.2)

if __name__ == "__main__":
    main()
