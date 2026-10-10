# Ek F — Üretici Model (Claude / Gemini) Kırılımı

> **Kaynak dosya(lar):** `sonuclar/uretici_model_rapor.txt`  
> **Üretim tarihi:** 2026-10-10  
> Sayılar kaynak dosyalardan olduğu gibi aktarılmıştır; yeniden hesaplama veya yuvarlama yapılmamıştır.

Üretici model dağılımı: Claude = 50, Gemini = 50 (`URETICI MODEL DAGILIMI: {'Claude': 50, 'Gemini': 50}`). G3'te Claude = öz-parafraz, Gemini = çapraz-model. `*` = Fisher p < .05 (`analiz_uretici_model.py` içindeki işaretleme ölçütü).

## F.1 G2 (saf YZ) — YZ olarak yakalanma oranı

| Araç | Dil | Claude | Gemini | Fark | Fisher p |  |
|---|---|---|---|---|---|---|
| GPTZero | TUM | 50/50 = 1.00 | 50/50 = 1.00 | +0.00 | 1.000000 |  |
| GPTZero | TUR | 25/25 = 1.00 | 25/25 = 1.00 | +0.00 | 1.000000 |  |
| GPTZero | ENG | 25/25 = 1.00 | 25/25 = 1.00 | +0.00 | 1.000000 |  |
| ZeroGPT | TUM | 48/50 = 0.96 | 50/50 = 1.00 | -0.04 | 0.494949 |  |
| ZeroGPT | TUR | 25/25 = 1.00 | 25/25 = 1.00 | +0.00 | 1.000000 |  |
| ZeroGPT | ENG | 23/25 = 0.92 | 25/25 = 1.00 | -0.08 | 0.489796 |  |
| Copyleaks | TUM | 31/31 = 1.00 | 15/15 = 1.00 | +0.00 | 1.000000 |  |
| Copyleaks | TUR | 15/15 = 1.00 | 15/15 = 1.00 | +0.00 | 1.000000 |  |
| Sapling | TUM | 50/50 = 1.00 | 43/50 = 0.86 | +0.14 | 0.012480 | * |
| Sapling | TUR | 25/25 = 1.00 | 18/25 = 0.72 | +0.28 | 0.009625 | * |
| Sapling | ENG | 25/25 = 1.00 | 25/25 = 1.00 | +0.00 | 1.000000 |  |
| Originality_ai | TUM | 50/50 = 1.00 | 50/50 = 1.00 | +0.00 | 1.000000 |  |
| Originality_ai | TUR | 25/25 = 1.00 | 25/25 = 1.00 | +0.00 | 1.000000 |  |
| Originality_ai | ENG | 25/25 = 1.00 | 25/25 = 1.00 | +0.00 | 1.000000 |  |
| Pangram | TUM | 50/50 = 1.00 | 50/50 = 1.00 | +0.00 | 1.000000 |  |
| Pangram | TUR | 25/25 = 1.00 | 25/25 = 1.00 | +0.00 | 1.000000 |  |
| Pangram | ENG | 25/25 = 1.00 | 25/25 = 1.00 | +0.00 | 1.000000 |  |

## F.2 G3 (insanlaştırılmış) — YZ olarak yakalanma oranı

| Araç | Dil | Claude | Gemini | Fark | Fisher p |  |
|---|---|---|---|---|---|---|
| GPTZero | TUM | 48/50 = 0.96 | 49/50 = 0.98 | -0.02 | 1.000000 |  |
| GPTZero | TUR | 23/25 = 0.92 | 24/25 = 0.96 | -0.04 | 1.000000 |  |
| GPTZero | ENG | 25/25 = 1.00 | 25/25 = 1.00 | +0.00 | 1.000000 |  |
| ZeroGPT | TUM | 37/50 = 0.74 | 36/50 = 0.72 | +0.02 | 1.000000 |  |
| ZeroGPT | TUR | 23/25 = 0.92 | 22/25 = 0.88 | +0.04 | 1.000000 |  |
| ZeroGPT | ENG | 14/25 = 0.56 | 14/25 = 0.56 | +0.00 | 1.000000 |  |
| Sapling | TUM | 50/50 = 1.00 | 49/50 = 0.98 | +0.02 | 1.000000 |  |
| Sapling | TUR | 25/25 = 1.00 | 25/25 = 1.00 | +0.00 | 1.000000 |  |
| Sapling | ENG | 25/25 = 1.00 | 24/25 = 0.96 | +0.04 | 1.000000 |  |
| Originality_ai | TUM | 50/50 = 1.00 | 49/50 = 0.98 | +0.02 | 1.000000 |  |
| Originality_ai | TUR | 25/25 = 1.00 | 24/25 = 0.96 | +0.04 | 1.000000 |  |
| Originality_ai | ENG | 25/25 = 1.00 | 25/25 = 1.00 | +0.00 | 1.000000 |  |
| Pangram | TUM | 50/50 = 1.00 | 50/50 = 1.00 | +0.00 | 1.000000 |  |
| Pangram | TUR | 25/25 = 1.00 | 25/25 = 1.00 | +0.00 | 1.000000 |  |
| Pangram | ENG | 25/25 = 1.00 | 25/25 = 1.00 | +0.00 | 1.000000 |  |

## F.3 İnsanlaştırmanın etkisi, üretici modele göre (eşleşmiş)

b = G2'de yakalanıp G3'te kaçırılan çift sayısı; c = G2'de kaçırılıp G3'te yakalanan çift sayısı.

| Araç | Model | n | R_G2 | R_G3 | b | c | p (exact) |
|---|---|---|---|---|---|---|---|
| GPTZero | Claude | 50 | 1.0000 | 0.9600 | 2 | 0 | 0.500000 |
| GPTZero | Gemini | 50 | 1.0000 | 0.9800 | 1 | 0 | 1.000000 |
| ZeroGPT | Claude | 50 | 0.9600 | 0.7400 | 11 | 0 | 0.000977 |
| ZeroGPT | Gemini | 50 | 1.0000 | 0.7200 | 14 | 0 | 0.000122 |
| Sapling | Claude | 50 | 1.0000 | 1.0000 | 0 | 0 | 1.000000 |
| Sapling | Gemini | 50 | 0.8600 | 0.9800 | 1 | 7 | 0.070312 |
| Originality_ai | Claude | 50 | 1.0000 | 1.0000 | 0 | 0 | 1.000000 |
| Originality_ai | Gemini | 50 | 1.0000 | 0.9800 | 1 | 0 | 1.000000 |
| Pangram | Claude | 50 | 1.0000 | 1.0000 | 0 | 0 | 1.000000 |
| Pangram | Gemini | 50 | 1.0000 | 1.0000 | 0 | 0 | 1.000000 |

**Not:** Copyleaks G3 ölçümleri derlemin güncel sürümünden önceki metinlere ait olduğu için raporlanmamıştır.
