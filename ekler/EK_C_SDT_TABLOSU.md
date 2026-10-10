# Ek C — Sinyal Tespit Teorisi Göstergeleri (araç × dil)

> **Kaynak dosya(lar):** `sonuclar/sdt_rapor.txt`, `sonuclar/sdt_esik_istatistik.json`  
> **Üretim tarihi:** 2026-10-10  
> Sayılar kaynak dosyalardan olduğu gibi aktarılmıştır; yeniden hesaplama veya yuvarlama yapılmamıştır.

Karar eşiği τ = %50. Kurgu A: sinyal = G2 (saf YZ), gürültü = G1 (insan). Kurgu B: sinyal = G2 + G3 (tüm YZ), gürültü = G1 (insan). `*` = log-lineer düzeltme uygulandı (ham oran 0 veya 1). c′ = c/d′ (`sdt_rapor.txt` içindeki `c/d` sütunu; JSON'da `c_norm`). β yalnızca `sdt_esik_istatistik.json` içinde bulunduğundan JSON'daki ham değeriyle verilmiştir; d′, c, c′ ve AUC `sdt_rapor.txt`'te yazıldığı biçimdedir. AUC eşikten bağımsızdır (Mann–Whitney U).

| Araç | Dil | Kurgu | d′ | c | c′ (c/d′) | β | AUC |
|---|---|---|---|---|---|---|---|
| GPTZero | TUM | A(G2) | 5.1585* | 0.0000 | 0.0000 | 1.000000000000001 | 1.0000 |
| GPTZero | TUM | B(G2G3) | 4.6896* | 0.2344 | 0.0500 | 3.002561914150944 | 1.0000 |
| GPTZero | TUR | A(G2) | 4.6675* | -0.0000 | -0.0000 | 0.999999999999999 | 1.0000 |
| GPTZero | TUR | B(G2G3) | 4.1502* | 0.2587 | 0.0623 | 2.9257722475931063 | 1.0000 |
| GPTZero | ENG | A(G2) | 4.6675* | -0.0000 | -0.0000 | 0.999999999999999 | 1.0000 |
| GPTZero | ENG | B(G2G3) | 4.9130* | -0.1227 | -0.0250 | 0.5471270826838568 | 1.0000 |
| ZeroGPT | TUM | A(G2) | 2.0886 | -0.9199 | -0.4404 | 0.14641138859623723 | 0.8347 |
| ZeroGPT | TUM | B(G2G3) | 1.1748 | -0.4630 | -0.3941 | 0.5804593954123829 | 0.7221 |
| ZeroGPT | TUR | A(G2) | 1.0957* | -1.7859 | -1.6300 | 0.1413075692971523 | 0.7152 |
| ZeroGPT | TUR | B(G2G3) | 0.3650 | -1.4206 | -3.8917 | 0.5953798954187483 | 0.5296 |
| ZeroGPT | ENG | A(G2) | 3.9882* | 0.3397 | 0.0852 | 3.8754459869684363 | 1.0000 |
| ZeroGPT | ENG | B(G2G3) | 3.0318* | 0.8179 | 0.2698 | 11.936535054507877 | 0.9825 |
| Copyleaks | TUM | A(G2) | 3.3910* | -0.6075 | -0.1792 | 0.12743790361928134 | 0.9348 |
| Copyleaks | TUR | A(G2) | 2.9487* | -0.6668 | -0.2261 | 0.13997332233609647 | 0.9000 |
| Copyleaks | ENG | A(G2) | 3.7790* | -0.0000 | -0.0000 | 1.0 | 1.0000 |
| Sapling | TUM | A(G2) | 1.2449 | -0.8223 | -0.6605 | 0.35924668363284273 | 0.7697 |
| Sapling | TUM | B(G2G3) | 1.5249 | -0.9623 | -0.6311 | 0.23053237702626536 | 0.8095 |
| Sapling | TUR | A(G2) | 0.4791 | -0.8096 | -1.6900 | 0.6785167495957273 | 0.6180 |
| Sapling | TUR | B(G2G3) | 0.8747 | -1.0074 | -1.1517 | 0.414274170903987 | 0.6774 |
| Sapling | ENG | A(G2) | 2.4818* | -1.0929 | -0.4404 | 0.06638475859657132 | 0.8934 |
| Sapling | ENG | B(G2G3) | 2.3220 | -1.0130 | -0.4363 | 0.09515476768011104 | 0.9253 |
| Originality_ai | TUM | A(G2) | 3.8386* | -0.6600 | -0.1719 | 0.0793894633570982 | 0.9871 |
| Originality_ai | TUM | B(G2G3) | 3.6935 | -0.5874 | -0.1590 | 0.11421126262842775 | 0.9828 |
| Originality_ai | TUR | A(G2) | 3.5718* | -0.5478 | -0.1534 | 0.14130756929715224 | 0.9836 |
| Originality_ai | TUR | B(G2G3) | 3.4121 | -0.4680 | -0.1372 | 0.20254783194475887 | 0.9688 |
| Originality_ai | ENG | A(G2) | 3.5718* | -0.5478 | -0.1534 | 0.14130756929715224 | 1.0000 |
| Originality_ai | ENG | B(G2G3) | 3.8173* | -0.6706 | -0.1757 | 0.07731319815069793 | 0.9996 |
| Pangram | TUM | A(G2) | 5.1585* | 0.0000 | 0.0000 | 1.000000000000001 | 1.0000 |
| Pangram | TUM | B(G2G3) | 5.3879* | -0.1147 | -0.0213 | 0.5390659830316192 | 1.0000 |
| Pangram | TUR | A(G2) | 4.6675* | -0.0000 | -0.0000 | 0.999999999999999 | 1.0000 |
| Pangram | TUR | B(G2G3) | 4.9130* | -0.1227 | -0.0250 | 0.5471270826838568 | 1.0000 |
| Pangram | ENG | A(G2) | 4.6675* | -0.0000 | -0.0000 | 0.999999999999999 | 1.0000 |
| Pangram | ENG | B(G2G3) | 4.9130* | -0.1227 | -0.0250 | 0.5471270826838568 | 1.0000 |

**Not:** Copyleaks G3 ölçümleri derlemin güncel sürümünden önceki metinlere ait olduğu için raporlanmamıştır.
