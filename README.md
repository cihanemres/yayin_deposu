# YZ Tespit Araçlarının Türkçe ve İngilizce Akademik Metinlerdeki Güvenilirliği

Bu depo, "YZ Tespit Araçlarının Türkçe ve İngilizce Akademik Metinlerdeki
Güvenilirliği" başlıklı çalışmanın **ölçüm boru hattını, ham verisini ve
istatistiksel analiz betiklerini** içerir. Makalede raporlanan her sayısal
değer, buradaki betiklerin ham veri üzerinde çalıştırılmasıyla yeniden
üretilebilir.

> **Makale sürümü:** `v1.0-paper` etiketi. Makaledeki değerleri yinelemek için
> `main` dalını değil bu etiketi kullanın.

## Çalışmanın özeti

Altı ticari YZ tespit aracı (GPTZero, ZeroGPT, Copyleaks, Sapling,
Originality.ai, Pangram), 300 akademik özetten oluşan dengeli bir derlem
üzerinde, tek bir ölçüm protokolüyle ve resmî API'leri üzerinden sınanmıştır.

| Grup | Gerçek etiket | n | İçerik |
|---|---|---|---|
| G1 | İnsan | 100 (50 TUR + 50 ENG) | 2018–2021 arası, DOI doğrulanmış açık erişimli makale özetleri |
| G2 | YZ | 100 (50 TUR + 50 ENG) | G1 başlıklarından sabit istemle üretilmiş özetler |
| G3 | YZ | 100 (50 TUR + 50 ENG) | G2'nin ±%10 uzunluk bandında insanlaştırılmış hâli |

Çerçeve olarak Sinyal Tespit Teorisi benimsenmiş; duyarlılık ($d'$) ile karar
ölçütü ($c$) ayrı ayrı kestirilmiştir.

## Dizin yapısı

```
run.py                     Ölçüm sürücüsü (--olc / --yaz / --dogrula / --kalibrasyon)
ilerleme.py                Canlı ilerleme paneli
metrikler.py               Temel metrik raporu
yzdetect/                  Boru hattı paketi
  corpus.py                Korpus yükleyici
  detectors.py             Altı araç için adaptör katmanı
  runner.py                Orkestratör (hız sınırı, üstel geri çekilme)
  writer.py                JSONL + Excel sonuç yazıcı
  config.py                Yapılandırma (anahtarlar .env'den okunur)
test_detectors.py          Adaptör sözleşmesi testleri

analiz_yontem.py           Ki-kare/Fisher, McNemar, Cochran Q
analiz_sdt.py              d', c, c', beta, AUC + eşik duyarlılık analizi
analiz_uzunluk.py          Cohen's dz, TOST eşdeğerlik, bant içi yineleme
analiz_uretici_model.py    Üretici model (Claude/Gemini) kırılımı

veri/
  HAM_OLCUMLER.csv         1624 ölçüm (metin × araç), düz tablo
  ham_api_yanitlari.jsonl  Ham API yanıtları (girdi metni içeren alanlar çıkarılmış)
  G2_G3_METINLER.csv       G2 ve G3 metinlerinin tam gövdeleri (200 metin)
  G1_KAYNAKCA_DOI.csv      G1'in 100 kaydı: dergi, başlık, DOI (gövde yok)

sonuclar/                  Analiz çıktıları (JSON özetler + konsol raporları)
ekler/                     Ek A (üretim istemleri), Ek B (insanlaştırma
                           protokolü), Ek B-1 (`humanizer` skill tam metni)
```

## G1 metinleri neden burada değil?

G1 özetlerinin telif hakları kaynak dergilerdedir; bu nedenle metin gövdeleri
çoğaltılmamış, bunun yerine `veri/G1_KAYNAKCA_DOI.csv` dosyasıyla 100 kaydın
tamamı DOI üzerinden izlenebilir kılınmıştır (100/100 DOI, 38 dergi).

Bu, analizlerin yeniden üretilebilirliğini **kısıtlamaz**: her (metin, araç)
ölçümünün normalize skoru ve ham API yanıtlarının metin içermeyen alanları bu depodadır, dolayısıyla tüm
istatistiksel çözümlemeler metinlere hiç erişmeden yinelenebilir. Metin
gövdesine yalnızca *yeni bir ölçüm* yapmak isteyen (örneğin başka bir dedektör
eklemek isteyen) bir araştırmacının ihtiyacı olur.

## Veri

`veri/ham_api_yanitlari.jsonl`, API ham yanıtlarının girdi metni içeren
alanları çıkarılmış hâlidir. G1 insan metinleri telif nedeniyle
paylaşılmamıştır; kaynakları `veri/G1_KAYNAKCA_DOI.csv` dosyasındaki DOI'lerle
erişilebilir. Analiz için birincil kaynak `veri/HAM_OLCUMLER.csv`'dir. Bir
metin–araç çifti için birden çok kayıt varsa, hatasız son kayıt kullanılmıştır.
Copyleaks'in 27 ölçümü protokol öncesinde elle kaydedilmiştir ve JSONL'de
karşılığı yoktur (CSV'de 'Excel(tarihsiz)' kökenli). Originality.ai İngilizce
metinlerde aiModelVersion=1 istenmiş, yanıtta 5 dönmüştür.

## Ekler

| Dosya | İçerik |
|---|---|
| `ekler/EK_A_URETIM_ISTEMLERI.md` | G2 üretim istemleri |
| `ekler/EK_B_INSANLASTIRMA_YONERGESI.md` | G3 insanlaştırma protokolü |
| `ekler/EK_B1_HUMANIZER_SKILL.md` | `humanizer` skill tam metni (v2.8.2) |
| `ekler/EK_C_SDT_TABLOSU.md` | d′, c, c′, β, AUC (araç × dil) |
| `ekler/EK_D_ESIK_DUYARLILIK.md` | Dokuz eşikte FPR ve TPR |
| `ekler/EK_E_UZUNLUK_KONTROLU.md` | TOST, bant içi McNemar, Spearman, Mann–Whitney |
| `ekler/EK_F_URETICI_MODEL.md` | Üretici model (Claude/Gemini) kırılımı |

## Analizleri yeniden üretme

```bash
pip install -r requirements.txt

python analiz_yontem.py          # ki-kare/Fisher, McNemar, Cochran Q
python analiz_sdt.py             # d', c, AUC, eşik duyarlılığı
python analiz_uzunluk.py         # TOST, bant içi yineleme, kovaryat denetimleri
python analiz_uretici_model.py   # üretici model kırılımı
```

Betikler `veri/` altındaki ham dosyaları okur ve `sonuclar/` altındaki
JSON/metin çıktılarını yeniden üretir. API anahtarı gerekmez — yeni ölçüm
yapılmaz.

## Yeni ölçüm yapma (isteğe bağlı)

Yeni bir dedektör eklemek veya ölçümleri tazelemek için API anahtarı gerekir:

```bash
cp .env.example .env      # anahtarları doldurun
python run.py --dogrula   # anahtar tanımlı mı
python run.py --kalibrasyon --arac <ARAÇ>   # skor yönü ve ölçek denetimi
python run.py --olc --arac <ARAÇ> --grup G3_Insanlastirilmis
```

`.env` dosyası depoya **dahil değildir** ve asla commit edilmemelidir.

**Uyarı:** Ticari dedektörlerin modelleri ve eşikleri zamanla değişir. Yeni
ölçümler, bu depodaki 2026 tarihli değerlerle birebir örtüşmeyebilir; makalede
raporlanan bulguların skor denetimi için `veri/HAM_OLCUMLER.csv`, yanıt yapısı
ve model sürümü denetimi için `veri/ham_api_yanitlari.jsonl` esas alınmalıdır.

## Lisans

- **Kod:** MIT Lisansı (`LICENSE`)
- **Veri ve dokümantasyon:** CC BY 4.0 (`LICENSE-data`)

G1 kaynakça listesindeki künye bilgileri ilgili yayıncılara aittir.

## Atıf

⟦DOLDUR: makale yayımlandığında künye ve DOI buraya eklenecek⟧

## İlgili depo

İnsanlaştırma protokolü (`bote-academic`) ayrı bir depoda sürdürülmektedir:
https://github.com/cihanemres/bote-academic — o depo çalışmadan bağımsız
gelişebileceğinden, bu çalışma için bağlayıcı olan metin `ekler/` altındaki
dondurulmuş v5 sürümüdür.

Protokolün alt bileşeni olan `humanizer` skill'i üçüncü tarafa aittir
(https://github.com/blader/humanizer, MIT). `ekler/EK_B1_HUMANIZER_SKILL.md`,
üretim tarihinde geçerli olan sürümün (v2.8.2, commit `1b48564`) birebir
kopyasıdır ve yazarına atıfla MIT lisansı altında çoğaltılmıştır.
