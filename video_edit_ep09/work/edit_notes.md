# Söylesem Ayıp mı? — Bölüm 9 · Edit Notları (v01)

**Kaynak:** `source/A_cam.mp4` (720×1280, 30 fps, 50.0 sn; kaynakta 15 jump-cut var)
**Çıktı:** `exports/ep09_v01_final_1080x1920.mp4` (1080×1920, 30 fps, H.264 CRF16, AAC 48 kHz, −14 LUFS, 52.2 sn)

## Önemli kısıt: transkript yok
Ortamın ağ politikası konuşma tanıma modelinin indirilmesini engelledi (HuggingFace erişimi 403). Bu yüzden:
- Beat'ler ses enerjisi (nefes/duraklama) ve kaynaktaki sahne kesimleriyle zamanlandı.
- Editoryal metinler, playbook §17'deki "Bölüm 9 – Kendimiz olmak ayıp mı?" haritasından alındı. Kaynaktaki kesim yapısı bu haritayla örtüşüyor: 5.8 / 7.67 / 8.9 sn'deki üç kesim "sessiz / ölçülü / kabul edilebilir" üçlemesine, sondaki geniş plan da final sorusuna denk geliyor.
- **Altyazı (captions.srt) üretilmedi.** Transkript (veya .srt) gelince altyazı katmanı eklenip metin zamanlamaları kelime düzeyinde ayarlanacak.

## Yaratıcı strateji
| Final zaman | Beat | Karar | Neden |
|---|---|---|---|
| 0:00–3:23 | HOOK | Orta plan, %3 micro push, metin yok | Soru yüz temasıyla yeterli |
| 3:23–5:80 | HOOK ("Peki… ayıp mı?") | Sola reframe, sabit | İmza soru; jeneriğe nefes |
| 5:80–7:20 | JENERİK | Krem zemin, serif "SÖYLESEM / AYIP MI?", 0.2 sn dissolve | Seri kimliği; müzik + yumuşak "air" geçiş burada girer |
| 7:20–13:40 | TRIPLE | 100→106→112 crop basamakları; SESSİZ (üst sol, koyu) / ÖLÇÜLÜ, KABUL EDİLEBİLİR (alt, krem) | Gerilim kademeli; kelimeler farklı negative-space alanlarında |
| 13:40–17:37 | QUESTION | Daha geniş kadraj, off-axis | Sorular nefes alır |
| 17:37–19:40 | EXAMPLE | **Eller detay insert'i** (2.6×), 1.6 sn | Göz yeni bilgi alır; ses devam eder |
| 20:03–22:50 | OBSERVATION | %4 yavaş push-in | Gözlem |
| 23:00–24:60 | EXAMPLE | **Göz hattı detay insert'i** (1.9×) | Tereddüt hissi |
| 25:83–28:73 | CONTRAST | Üst-sol serif "KİMSE “DEĞİŞ” DEMEDİ.", saçın arkasından geçen luma maskesi | Dönüş = kompozisyon değişimi |
| 28:73–31:77 | CONTRAST | Daha sıkı kadraj, "AMA DEĞİŞTİK." | Karşı-cümle sertleşir |
| 31:77–40:33 | TRIPLE (sansür) | **Kadraj daralması**: krem çerçeve %0→%9 içeri kapanır, crop 104→108→114 | "Kendimizden eksiltmek" metaforu |
| 40:33–43:77 | EMOTIONAL TURN | Çerçeve bir anda açılır, müzik −1.5 dB, 3 satır krem metin (alt üçte bir) | Rahatlama ama acı tespit |
| 43:77–48:00 | CLIMAX | **Bölümün tek punch-in'i** 106→120 (0.3 sn), müzik −2 dB, gecikmeli yansıma ("ghost"; %16 opak, 6 kare) | "Rol yaptığını unutmak" fikri; iki versiyon |
| 48:00–52:20 | FINAL QUESTION | Geniş plan, 110→100 yavaş pull-out, "ŞU AN YAŞADIĞIMIZ HAYAT KİMİN?" kalır, müzik −12 dB, 0.8 sn hold, siyaha fade | Cevap verilmez, alan açılır |

## Ritim kontrolü (playbook §6 hedefleri)
- Kadraj/crop değişimi: ~16 (hedef 8–14; kaynaktaki jump-cut'larla birlikte)
- Editoryal metin: 5 an (+ jenerik) (hedef 3–6)
- B-roll/insert: 2 (eller, göz). Harici arşiv verilmedi; aynı çekimden detay planlar kullanıldı.
- Masking/compositing: 3 (metin-arkası maske, çerçeve daralması, gecikmeli yansıma)
- Sert punch-in: 1
- Müzik düşüşü: climax öncesi ve finalde

## Renk ve ses
- Renk: warm-neutral; kontrast 0.96, saturasyon 0.94, highlight'lar hafif korunuyor, ince ve tutarlı grain. Cilde smoothing uygulanmadı.
- Ses: 80 Hz high-pass, hafif FFT gürültü azaltma, hafif presence EQ ve 2.5:1 kompresyon; −14 LUFS'e normalize edildi.
- Müzik: minimal ambient pad, render sırasında üretildi (Dmaj7 / Bm7 / Cmaj7); konuşmanın ~18 dB altında. Gerçek bir müzik dosyası verilirse onunla değiştirilmeli.

## Self-critique (2. geçiş) ve yapılan düzeltmeler
- "KABUL EDİLEBİLİR" ve "KABUL EDİLMEK İÇİN…" saça çarpıyordu → alt üçte bire, koyu tişört üzerine krem renkle taşındı.
- "KİMSE DEĞİŞ DEMEDİ" maske yüzünden kesiliyordu → 2 satıra indirildi, başın üstüne alındı. Maske artık yalnızca saç kenarında devreye giriyor.
- Eller insert'inde ağız yarım görünüyordu → crop aşağı ve sola kaydırıldı, süre 1.6 sn'ye indi.
- Bilinen sınır: kaynak 720p olduğu için 2× üzeri detay crop'lar hafif yumuşak. 4K kaynak verilirse insert'ler belirgin şekilde netleşir.

## Açık işler
1. Transkript → captions.srt ve metin zamanlamalarını kelimeye göre ayarlamak.
2. Jenerik asset'i (`brand/title_card.mov`) varsa üretilen jenerik kartı yerine onu koymak.
3. Arşiv B-roll (story taslağı, ayna/kıyafet) gelirse 17:37 ve 23:00'daki insert'leri onunla değiştirmek.
