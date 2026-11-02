# Söylesem Ayıp mı? — Reels kurgusu

`render.py`, ham çekimi "Söylesem Ayıp mı? — Reels Stil Rehberi"ne göre kurgular:

- 1080×1920, 30 fps; krem/bej palet, sıcak ve düşük kontrastlı renk, yükseltilmiş siyahlar, ince grain
- İlk kare kapak (üst şerit + serif büyük harf başlık, en altta "AYIP MI?"); `kapak.jpg` olarak da kaydedilir
- Açılış sorularından sonra 1,5 sn jenerik ("Söylesem Ayıp mı?" / "Bir şey söyleyeceğim."); müzik burada başlar
- Kadraj kademeleri: geniş / orta / yakın, kaynağın jump cut'larına hizalı; üçlemede her satırda bir kademe yaklaşma; kapanışta tek punch-in, ardından yavaş zoom out ve siyaha fade
- Sans altyazı (Inter Medium), cümle cümle, en fazla 2 × 32 karakter, alt güvenli alanın üstünde
- İki ekran metni (Playfair Display, büyük harf, genişliğin %78'i, 0,3 sn fade, gövde maskeli): "Kabul edilmek için dönüştüğümüz kişiye alışmak" ve "Şu an yaşadığımız hayat kimin?"; bunlar görünürken altyazı gizlenir
- Ses: gürültü azaltma + -14 LUFS; minimal synth pad konuşmanın ~20 dB altında, kapanış cümlesinden önce tamamen kesilir. Ses efekti yok

```bash
pip install opencv-python-headless pillow numpy soundfile "rembg[cpu]"
EPISODE=1 python3 render.py kaynak.mp4 cikti/            # müzikli
EPISODE=1 python3 render.py kaynak.mp4 cikti/ --no-music # müziksiz (kendi müziğini eklemek için)
```

Altyazı zamanlamaları ve kadraj planı bu bölümün kaydına göre elle ayarlandı (`SUBS`, `ZOOM`, `SCREEN`). Font: Playfair Display (SIL OFL).
