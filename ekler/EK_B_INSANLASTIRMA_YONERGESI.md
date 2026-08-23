# Ek B. İnsanlaştırma Protokolü (`bote-academic v5` — FAZ 3)

G3 grubundaki 100 metnin tamamı, G2 eşlerinin **tek geçişli** olarak aşağıda
tanımlanan protokolden geçirilmesiyle üretilmiştir. Protokol 100 üretimin
tamamında sabit tutulmuş; yalnızca kaynak metin değişmiştir. Zincirleme veya
yinelemeli parafraz uygulanmamış; ±%10 sözcük bandının dışına çıkan çıktılar
aynı protokolle yeniden üretilmiştir.

## B.1. Uygulama künyesi

| Öğe | Değer |
|---|---|
| Araç | Claude — Claude Code (CLI); G2 üretimiyle aynı istemci |
| Model sürümü | `claude-opus-4-8` |
| Parametreler | İstemci varsayılanları; Claude Code örnekleme parametrelerini (temperature, top_p) kullanıcıya açmamakta olup bu değerler çalışma kapsamında değiştirilmemiştir |
| Sistem istemi | Skill tanımının kendisi (aşağıda B.2) dışında ayrıca sistem istemi kullanılmamıştır |
| Uygulama tarihi | 06.07.2026 |
| Geçiş sayısı | 1 (bant ihlalinde aynı protokolle yeniden üretim) |
| Protokol sürümü | `bote-academic v5` |
| Protokol kaynağı | https://github.com/cihanemres/bote-academic (`SKILL.md`, `references/ai-signatures.md`, `bote-academic-v5.zip`) |
| Alt bileşen | `humanizer` v2.8.2, commit `1b48564` (29.06.2026) — https://github.com/blader/humanizer; tam metin **Ek B-1** |

## B.2. Protokolün bileşenleri

İnsanlaştırma tek bir istem metni değil, **üç bileşenli bir yönerge
kümesidir**. `bote-academic v5` skill'inin FAZ 3 (Revizyon & Humanizer) adımı
şu çağrıyı yapmaktadır:

> **FAZ 3 — Revizyon & Humanizer**
> 1. `humanizer` skill'i + `references/ai-signatures.md` ile AI imzalarını temizle.
> 2. İntihal riski taşıyan parafrazları yeniden yaz.
> 3. **Revizyon raporu ver:** kaç AI-imza temizlendi, hangi bölümler hâlâ riskli, similarity tahmini.

Buna göre uygulanan üç bileşen:

1. **`bote-academic v5` skill tanımı** — çerçeveyi ve değişmez kuralları
   (halüsinasyon sıfır toleransı, atıf bütünlüğü, anlamı bozmama) dayatan üst
   katman. Tam metin: depodaki `SKILL.md`.
2. **`references/ai-signatures.md`** — temizlenecek YZ imzalarının işlemsel
   listesi. Tam metin aşağıda B.3'te verilmiştir.
3. **`humanizer` skill'i** — genel amaçlı yeniden-yazım katmanı; üçüncü
   tarafça geliştirilmiş, kamuya açık ve MIT lisanslı bir bileşendir
   (https://github.com/blader/humanizer). Wikipedia'nın "Signs of AI writing"
   sayfasındaki (WikiProject AI Cleanup) 35 örüntüyü işlemsel kurallara
   dönüştürür ve metni bu kurallara göre yeniden yazar; yeniden yazımda
   kapsam korunur (kaynak metin kaç paragrafsa çıktı da o kadardır),
   olgusal içerik ve anlam değiştirilmez. Sürüm 2.8.2, commit `1b48564`
   (29.06.2026). **Tam metin Ek B-1'de** birebir verilmiştir; sürüm
   sabitlemesinin gerekçesi ve belirsizlik aralığı da orada tartışılmıştır.
4. **Çalışmaya özgü uzunluk kısıtı** — yukarıdaki üç bileşene ek olarak, bu
   çalışma için çıktının kaynak G2 eşinin ±%10 sözcük bandında kalması
   koşulu dayatılmıştır. ⟦DOLDUR: bu kısıtı iletirken kullandığınız
   ifadeyi buraya yazın.⟧

## B.3. `references/ai-signatures.md` (tam metin)

> Aşağıdaki metin, protokolün uygulandığı sürümden (v5) birebir alınmıştır.

```markdown
# AI-Tespit İmzaları ve Turnitin Uyumluluğu

Bu dosya Turnitin/AI-detektör flag'lerini azaltmaya yönelik akademik-Türkçe
odaklı kontrol listesidir. Genel yeniden-yazım için `humanizer` skill'ini
kullan; bu dosya onu **tamamlar**, tekrar etmez: akademik metne özgü imzalar +
Türkçe-İngilizce çift dil tuzakları + revizyon raporu formatı.

## ÖNEMLİ: Amaç dürüstlük, kaçırma değil

Hedef, **gerçekten insan tarafından düşünülmüş, doğal akademik metin**
üretmektir; detektörü "kandırmak" değil. Uydurma kaynak, sahte parafraz veya
anlamı bozan kelime oyunu KESİNLİKLE yapılmaz. Metin doğallaşırken bilimsel
doğruluk ve atıf bütünlüğü korunur. Son editör kontrolü kullanıcıdadır.

## A) Yüksek-riskli AI imzaları (akademik metinde en sık flag)

1. **Üçleme saplantısı (rule of three):** "hızlı, etkili ve sürdürülebilir"
   gibi sürekli 3'lü sıralama. Akademik Türkçede de aynı risk. → 2'li veya
   4'lü varyasyon, bazen tek güçlü sıfat.
2. **Boş geçiş kalıpları:** "Bu bağlamda", "Bu doğrultuda", "Sonuç olarak
   ifade etmek gerekirse", "Günümüzde giderek artan". → Doğrudan iddiaya geç;
   geçişi argümanın kendisi taşısın.
3. **Şişirilmiş önem cümleleri:** "Bu çalışma alanyazına önemli katkılar
   sunmaktadır" (kanıtsız). → Somut katkıyı söyle: "Bu çalışma, X ölçeğini
   Türk örnekleminde ilk kez doğrulamaktadır."
4. **Yüzeysel -arak/-erek analizi:** "...inceleyerek, ...vurgulayarak,
   ...göstererek" zinciri. → Bağımsız cümlelere böl, gerçek nedensellik kur.
5. **Belirsiz atıf:** "Araştırmalar göstermektedir ki", "Uzmanlara göre",
   "Literatürde sıkça belirtildiği üzere" (kaynaksız). → Gerçek atıf koy
   `(Yazar, Yıl)` veya `[KAYNAK GEREKLİ]` etiketle.
6. **Aşırı em-dash / noktalı virgül dengesi:** İngilizce abstract'ta em-dash
   bombardımanı klasik AI imzası. → Türkçe metinde uzun çizgiyi sınırla;
   cümleyi böl.
7. **Olumsuz paralellik:** "Sadece X değil, aynı zamanda Y" kalıbının aşırı
   tekrarı. → Seyrekleştir.
8. **AI sözcük dağarcığı (TR):** "kritik öneme sahip", "hayati",
   "dönüştürücü", "sorunsuz", "kapsamlı bir şekilde", "titizlikle", "zengin
   bir goblen" türevleri. → Sade akademik karşılık.

## B) Çift dil (TR→EN abstract) tuzakları

- Türkçe metni İngilizceye çevirirken AI, cümleleri **fazla simetrik ve uzun**
  kurar → detektör en çok abstract'ı flag'ler.
- Çeviride birebir kalıp tekrarı (her cümle "This study..."/"The results..."
  ile başlar) → cümle başlarını çeşitlendir.
- Türkçe deyim/bağlacın İngilizce kalıp karşılığı ("in this context", "it is
  worth noting") → kaldır.

## C) İntihal (similarity) ayrı risktir

AI-tespitten farklıdır. Kontrol:
- Birebir kopya yok; alıntı ise tırnak + sayfa `(Yazar, Yıl, s. X)`.
- Gerçek parafraz: **cümle yapısı + kelime tamamen değişmiş**, sadece eş
  anlamlı değiştirme değil.
- Kendi-intihali (önceki kendi yayınından kopya) da flag olur — belirt.
- Yöntem bölümünde standart kalıplar (ölçek tanımı vb.) kaçınılmaz benzerlik
  üretir; bunu revizyon raporunda not et.

## D) Revizyon raporu formatı (her humanize çıktısında)

─── AI-RİSK & İNTİHAL RAPORU ───
Temizlenen AI imzaları:
- [imza türü]: kaç yer, örnek (önce → sonra)

Hâlâ riskli bölümler:
- [bölüm]: neden (örn. yöntem kalıbı kaçınılmaz)

Tahmini similarity riski: [düşük / orta / yüksek] — gerekçe
Tahmini AI-tespit riski: [düşük / orta / yüksek] — hangi bölümler

ÖNERİ: Kullanıcı son kontrolü [Turnitin/iThenticate] ile yapmalı; otomatik
araç kesin değil.

## E) Akademik bütünlük sınırı

- Parafraz yaparken **kaynak hâlâ atıflanmalı** — yeniden yazmak atıf
  gerekliliğini kaldırmaz.
- Anlamı korumak için bilimsel terimi değiştirme (örn. "geçerlik" yerine eş
  anlamlı arama yapma).
- Detektör skorunu düşürmek için cümleye anlamsız varyasyon ekleme — bu hem
  kaliteyi düşürür hem etik dışıdır.
```

## B.4. Protokolün dayattığı kısıtlar

Ana metinde (§3.2) özetlenen dört kısıt, yukarıdaki bileşenlerin ve korpus
dosyasındaki `Islem_Notu` alanının birleşiminden gelmektedir:

1. **YZ imzalarının temizlenmesi** — B.3'teki A ve B maddeleri
   (kalıplaşmış geçişler, üçleme, tekdüze cümle başları, aşırı em-dash).
2. **İçerik ve veri sadakati** — B.3'teki C ve E maddeleri; hiçbir sayısal
   bulgu, yöntem adı veya sav düşürülmez, bilimsel terim değiştirilmez.
3. **Uzunluk bandı** — çıktı, kaynak G2 eşinin ±%10 sözcük bandında kalır
   (çalışmaya özgü ek kısıt, bkz. B.2 madde 4).
4. **Kısaltma yasağı** — dönüşüm, kısaltma yoluyla değil yeniden ifade
   yoluyla yapılır; kaynak içerik tam olarak taşınır.

`Islem_Notu` alanı iki biçimde kayıtlıdır (her biri 50 metin): 4. maddenin
açıkça yazıldığı sürüm ve yazılmadığı sürüm. Her iki alt kümede de aynı
protokol kullanılmıştır; ⟦DOLDUR: iki not biçimi arasında uygulama farkı varsa
burada belirtin, yoksa "yalnızca not metni farklıdır, uygulama aynıdır"
yazın⟧.

**Sürüm etiketi düzeltmesi.** Korpus dosyasının `Islem_Notu` alanı, 100 kaydın
tamamında protokolü "v2" olarak etiketliyordu; uygulanan sürüm ise
`bote-academic v5`'tir (depodaki `bote-academic-v5.zip` ile doğrulanmıştır).
Etiket 23.08.2026'da düzeltilmiştir (yedek:
`YZ_Tespit_Korpus_v9_YEDEK_20260823_protokol_etiketi.xlsx`). Düzeltme yalnızca
metin etiketini değiştirmiş, hiçbir metin veya ölçüm değerine dokunmamıştır.

## B.5. Doğrulama

Uzunluk kısıtının fiilen işlediği, ölçüm öncesinde korpus düzeyinde
doğrulanmıştır: 100 eşleşmiş çiftin 95'i ±%10 bandını sağlamış, ortalama
G3/G2 uzunluk oranı 0,9380 (SS = 0,0279) olarak gerçekleşmiş ve eşdeğerlik
sınamasıyla bandın içinde kaldığı gösterilmiştir (§3.2, madde 3).
