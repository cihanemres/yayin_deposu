# Ek A. G2 Üretim İstemleri (Sabit Şablonlar)

G2 grubundaki 100 metnin tamamı, aşağıdaki **iki sabit şablondan** biriyle
üretilmiştir. Şablonlar 100 üretimin tamamında birebir aynı kalmış; yalnızca
`{BAŞLIK}` alanı, eşleşen G1 metninin yayımlanmış başlığıyla doldurulmuştur.
Şablon dışında hiçbir sistem istemi, örnek (few-shot) veya takip iletisi
kullanılmamış; her metin tek bir çağrıda üretilmiştir.

Şablonların korpus dosyasındaki 100 kayıtla birebir uyumu programatik olarak
doğrulanmıştır: başlık alanı çıkarıldığında yalnızca iki ayrı şablon metni
kalmaktadır (TUR için 50 kayıt, ENG için 50 kayıt).

---

## A.1. Türkçe şablon (TUR; G2_YZ_01 – G2_YZ_50)

```
Aşağıdaki başlıkla Türkçe bir akademik araştırma makalesi özeti yaz. 180-220
kelime olsun. Amaç, yöntem, bulgular ve sonuç unsurlarını içersin. Akademik,
nesnel ve formel bir dille yaz. Yalnızca özet metnini ver; başlık, etiket veya
açıklama ekleme. Başlık: {BAŞLIK}
```

## A.2. İngilizce şablon (ENG; G2_YZ_51 – G2_YZ_100)

```
Write an academic research article abstract in English for the following
title. It should be 180-220 words and include the purpose, method, findings,
and conclusion. Use formal, objective academic language. Provide only the
abstract text without any title, labels, or explanations.
Title: {BAŞLIK}
```

---

## A.3. Model ataması

| Aralık | Dil | Model |
|---|---|---|
| G2_YZ_01 – G2_YZ_15 | TUR | Claude |
| G2_YZ_16 – G2_YZ_30 | TUR | Gemini |
| G2_YZ_31 – G2_YZ_40 | TUR | Claude |
| G2_YZ_41 – G2_YZ_50 | TUR | Gemini |
| G2_YZ_51 – G2_YZ_75 | ENG | Claude |
| G2_YZ_76 – G2_YZ_100 | ENG | Gemini |

Toplam: Claude 50 metin, Gemini 50 metin.

**Model sürümleri ve üretim parametreleri**

| Model | Erişim | Sürüm | Parametreler |
|---|---|---|---|
| Claude | Claude Code (CLI) | `claude-opus-4-8` (istemci oturum kayıtlarından belirlendi; bkz. ana metin §3.2) | İstemci varsayılanları; örnekleme parametreleri kullanıcıya açılmamaktadır |
| Gemini | Doğrudan API | `gemini-2.5-flash` (sürüm 001) | `temperature = 0,7`, `max_output_tokens = 4096`, `thinkingBudget = 0` |

Her iki modelde de **sistem istemi kullanılmamıştır**; yukarıdaki şablonlar
doğrudan kullanıcı iletisi olarak verilmiştir.

**Üretim tarihi:** 06.07.2026

## A.4. Başlık listesi

Girdi olarak kullanılan 100 başlığın tamamı, eşleştikleri G1 metinlerinin DOI
bilgileriyle birlikte yayımlanan veri setinde (`G2_YZ_Korpus` sayfası,
`Kaynak_Başlık` sütunu) verilmektedir.
