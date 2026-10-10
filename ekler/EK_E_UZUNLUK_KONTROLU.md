# Ek E — Uzunluk Kontrolü (G2 → G3)

> **Kaynak dosya(lar):** `sonuclar/uzunluk_rapor.txt`, `sonuclar/yontem_rapor.txt` (Bölüm 0b)  
> **Üretim tarihi:** 2026-10-10  
> Sayılar kaynak dosyalardan olduğu gibi aktarılmıştır; yeniden hesaplama veya yuvarlama yapılmamıştır.

`yontem_rapor.txt`, `analiz_yontem.py` betiğinin konsol çıktısıdır; aynı çalıştırmanın JSON özeti `sonuclar/yontem_istatistik.json` dosyasındadır.

## E.1 Eşleşmiş kelime sayıları (`yontem_rapor.txt`, Bölüm 0b)

| Grup | n | Ortalama | Min | Maks |
|---|---|---|---|---|
| G1 | 100 | 195.42 | 134 | 335 |
| G2 | 100 | 186.90 | 137 | 272 |
| G3 | 100 | 175.09 | 126 | 244 |

- Eşleşmiş çift: 100
- G3/G2 uzunluk oranı: ort = 0.9380, min = 0.8936, maks = 1.0153
- ±%10 bandında: 95/100 (95.0%)
- ±%20 bandında: 100/100 (100.0%)
- Eşleşmiş t-testi: t(99) = -20.2138, p = 6.453e-37 (p < .001)
- Wilcoxon: W = 5.0, p = 9.337e-18 (p < .001)

## E.2 Etki büyüklüğü (`uzunluk_rapor.txt`, Bölüm 1)

- n çift: 100
- Ortalama fark: -11.8100 sözcük (SS = 5.8425)
- Eşleşmiş t(99): -20.2138, p = 6.453e-37 (p < .001)
- Cohen's dz: -2.0214
- G3/G2 oran ort: 0.9380 (SS = 0.0279)

Not: dz büyük çıkabilir; çünkü farkın değişkenliği çok küçüktür (protokol her çifti dar bir banda zorluyor). Büyük dz burada "büyük fark" değil, "çok tutarlı küçük fark" anlamına gelir.

## E.3 Eşdeğerlik sınaması — TOST (`uzunluk_rapor.txt`, Bölüm 2)

H0: fark ±%10 bandının dışında. Ölçek: G3/G2 uzunluk oranı. Eşdeğerlik sınırı: [0.90, 1.10].

| Ölçüt | Değer |
|---|---|
| Ortalama oran | 0.9380 (%90 GA: [0.9334, 0.9426]) |
| H01 (μ ≤ 0.90) | t(99) = 13.6028, p = 1.083e-24 (p < .001) |
| H02 (μ ≥ 1.10) | t(99) = -57.9856, p = 1.583e-78 (p < .001) |
| TOST kararı | p = 1.083e-24 (p < .001) → eşdeğerlik kanıtlandı |

## E.4 Bant içi alt örneklem — McNemar (`uzunluk_rapor.txt`, Bölüm 3)

±%10 bandına uymayan 5 çift atılmış, kalan 95 çift üzerinde McNemar yinelenmiştir. Atılan çift no'ları: [1, 32, 50, 62, 92].

| Araç | Kapsam | n | R_G2 | R_G3 | b | c | p (exact) |
|---|---|---|---|---|---|---|---|
| GPTZero | TUM | 100 | 1.0000 | 0.9700 | 3 | 0 | 0.250000 |
| GPTZero | BANT | 95 | 1.0000 | 0.9684 | 3 | 0 | 0.250000 |
| ZeroGPT | TUM | 100 | 0.9800 | 0.7300 | 25 | 0 | 0.000000 |
| ZeroGPT | BANT | 95 | 0.9789 | 0.7368 | 23 | 0 | 0.000000 |
| Sapling | TUM | 100 | 0.9300 | 0.9900 | 1 | 7 | 0.070312 |
| Sapling | BANT | 95 | 0.9368 | 0.9895 | 1 | 6 | 0.125000 |
| Originality_ai | TUM | 100 | 1.0000 | 0.9900 | 1 | 0 | 1.000000 |
| Originality_ai | BANT | 95 | 1.0000 | 0.9895 | 1 | 0 | 1.000000 |
| Pangram | TUM | 100 | 1.0000 | 1.0000 | 0 | 0 | 1.000000 |
| Pangram | BANT | 95 | 1.0000 | 1.0000 | 0 | 0 | 1.000000 |

**Not:** Copyleaks G3 ölçümleri derlemin güncel sürümünden önceki metinlere ait olduğu için raporlanmamıştır.

## E.5 G3 içinde skor ile kelime sayısı ilişkisi — Spearman ρ (`uzunluk_rapor.txt`, Bölüm 4)

"Metin kısaldığı için kaçırıldı" savı doğruysa ρ pozitif ve anlamlı olmalıdır (uzun metin → yüksek YZ skoru).

| Araç | Dil | n | ρ | p |
|---|---|---|---|---|
| GPTZero | TUM | 100 | 0.4207 | 0.000013 |
| GPTZero | TUR | 50 | -0.0206 | 0.887237 |
| GPTZero | ENG | 50 | 0.1339 | 0.353878 |
| ZeroGPT | TUM | 100 | -0.3874 | 0.000068 |
| ZeroGPT | TUR | 50 | -0.1606 | 0.265196 |
| ZeroGPT | ENG | 50 | -0.2441 | 0.087582 |
| Sapling | TUM | 100 | 0.1923 | 0.055229 |
| Sapling | TUR | 50 | -0.6901 | 0.000000 |
| Sapling | ENG | 50 | 0.0125 | 0.931300 |
| Originality_ai | TUM | 100 | 0.3457 | 0.000427 |
| Originality_ai | TUR | 50 | -0.3337 | 0.017857 |
| Originality_ai | ENG | 50 | -0.1249 | 0.387340 |
| Pangram | TUM | 100 | — (skor sabit) | |
| Pangram | TUR | 50 | — (skor sabit) | |
| Pangram | ENG | 50 | — (skor sabit) | |

**Not:** Copyleaks G3 ölçümleri derlemin güncel sürümünden önceki metinlere ait olduğu için raporlanmamıştır.

## E.6 Kaçırılan çiftler (b hücresi) ile diğerleri — Mann–Whitney (`uzunluk_rapor.txt`, Bölüm 5)

Uzunluk karıştırıcısı geçerliyse, G3'te kaçırılan çiftlerin kısalma miktarı diğerlerinden büyük olmalıdır.

| Araç | Kaçırılan n | Diğer n | Kaçırılanlarda G3/G2 oran ort | Diğerlerinde G3/G2 oran ort | Mann–Whitney U | p | Sonuç |
|---|---|---|---|---|---|---|---|
| GPTZero | 3 | 97 | 0.9579 | 0.9374 | 195.0 | 0.322101 | fark yok |
| ZeroGPT | 25 | 75 | 0.9369 | 0.9384 | 873.0 | 0.610413 | fark yok |
| Sapling | 1 | — | — | — | — | — | sınama için yetersiz |
| Originality_ai | 1 | — | — | — | — | — | sınama için yetersiz |
| Pangram | 0 | — | — | — | — | — | sınama için yetersiz |

**Not:** Copyleaks G3 ölçümleri derlemin güncel sürümünden önceki metinlere ait olduğu için raporlanmamıştır.
