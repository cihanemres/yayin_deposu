"""Uzunluk karistiricisinin analitik denetimi — hakem raporu 3/8 icin.

Hakem elestirisi: "%95 metin +/-%10 bandinda" ile "t(99) = -20.21, p < .001"
ayni paragrafta duruyor; anlamlilik 'pratikte onemsiz' denerek savusturulmus.

Bu betik savunmayi soze degil sinamaya baglar:
  1) Etki buyuklugu (Cohen's dz) — anlamlilik ile buyukluk ayristirilir.
  2) ESDEGERLIK SINAMASI (TOST; Lakens, 2017): H0 "fark +/-%10 bandinin
     DISINDA" seklinde kurulur. Iki tek-yonlu t-testinin ikisi de anlamliysa
     esdegerlik ISPATLANIR — "fark yok" demenin dogru istatistiki yolu budur.
  3) BANT-ICI ALT ORNEKLEM: banda uymayan 5 cift atilarak McNemar yinelenir;
     bulgular bu 5 cifte bagimli mi?
  4) G3 icinde skor ile kelime sayisi iliskisi (Spearman) — kisa metin
     gercekten daha mi az yakalaniyor?
  5) Kacirilan ciftlerin uzunluk farki, kacirilmayanlardan farkli mi
     (Mann-Whitney)? Duyarlilik kaybini uzunluk mu suruklüyor?

Cikti: konsol + sonuclar/uzunluk_kontrol_istatistik.json
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from scipy import stats

from analiz_yontem import ARACLAR, basli, p_yaz, son_sayi, yukle

ROOT = Path(__file__).resolve().parent
ESIK = 50.0
BANT = 0.10          # +/- %10


def main() -> None:
    kayitlar = yukle()
    rapor: dict = {}

    # metin_id sonundaki sira no -> kelime (grup bazinda)
    kelime_g2: dict[int, int] = {}
    kelime_g3: dict[int, int] = {}
    dil_hb: dict[int, str] = {}
    for (mid, _arac), k in kayitlar.items():
        no = son_sayi(mid)
        if k["grup"] == "G2_YZ":
            kelime_g2[no] = k["kelime"]
            dil_hb[no] = k["dil"]
        elif k["grup"] == "G3_Insanlastirilmis":
            kelime_g3[no] = k["kelime"]

    ortak = sorted(set(kelime_g2) & set(kelime_g3))
    w2 = [kelime_g2[i] for i in ortak]
    w3 = [kelime_g3[i] for i in ortak]
    oran = [b / a for a, b in zip(w2, w3)]
    fark = [b - a for a, b in zip(w2, w3)]
    n = len(ortak)

    # ------------------------------------------------- 1. ETKI BUYUKLUGU
    basli("1. ETKI BUYUKLUGU — anlamlilik ile buyuklugun ayristirilmasi")
    t_es = stats.ttest_rel(w3, w2)
    dz = t_es.statistic / math.sqrt(n)
    ort_fark = sum(fark) / n
    ss_fark = statistics_ss(fark)
    print(f"  n cift            : {n}")
    print(f"  Ortalama fark     : {ort_fark:.4f} sozcuk (SS = {ss_fark:.4f})")
    print(f"  Eslesmis t({n-1})   : {t_es.statistic:.4f}, p = {p_yaz(t_es.pvalue)}")
    print(f"  Cohen's dz        : {dz:.4f}")
    print(f"  G3/G2 oran ort    : {sum(oran)/n:.4f} (SS = {statistics_ss(oran):.4f})")
    print("\n  Not: dz buyuk cikabilir; cunku farkin DEGISKENLIGI cok kucuktur")
    print("  (protokol her cifti dar bir banda zorluyor). Buyuk dz burada")
    print("  'buyuk fark' degil, 'cok tutarli kucuk fark' anlamina gelir.")
    rapor["etki"] = {"n": n, "ort_fark": ort_fark, "ss_fark": ss_fark,
                     "t": t_es.statistic, "p": t_es.pvalue, "cohen_dz": dz,
                     "ort_oran": sum(oran) / n, "ss_oran": statistics_ss(oran)}

    # ----------------------------------------------- 2. ESDEGERLIK (TOST)
    basli("2. ESDEGERLIK SINAMASI (TOST) — H0: fark +/-%10 bandinin DISINDA\n"
          "   Olcek: G3/G2 uzunluk orani. Esdegerlik siniri: [0.90, 1.10]")
    alt_sinir, ust_sinir = 1 - BANT, 1 + BANT
    ss_o = statistics_ss(oran)
    ort_o = sum(oran) / n
    sh = ss_o / math.sqrt(n)
    t_alt = (ort_o - alt_sinir) / sh          # H01: mu <= 0.90 (tek yonlu ust)
    p_alt = stats.t.sf(t_alt, n - 1)
    t_ust = (ort_o - ust_sinir) / sh          # H02: mu >= 1.10 (tek yonlu alt)
    p_ust = stats.t.cdf(t_ust, n - 1)
    p_tost = max(p_alt, p_ust)
    gg = stats.t.ppf(0.95, n - 1) * sh        # %90 GA (TOST'un karsiligi)
    print(f"  Ortalama oran      : {ort_o:.4f}   (%90 GA: "
          f"[{ort_o-gg:.4f}, {ort_o+gg:.4f}])")
    print(f"  H01 (mu <= 0.90)   : t({n-1}) = {t_alt:.4f}, p = {p_yaz(p_alt)}")
    print(f"  H02 (mu >= 1.10)   : t({n-1}) = {t_ust:.4f}, p = {p_yaz(p_ust)}")
    print(f"  TOST kararı        : p = {p_yaz(p_tost)} -> "
          f"{'ESDEGERLIK KANITLANDI' if p_tost < .05 else 'ESDEGERLIK GOSTERILEMEDI'}")
    print("\n  Yorum: klasik t-testi 'fark sifir degil' der; TOST 'fark, onceden")
    print("  ilan edilen onemlilik esiginden kucuk' der. Ikisi celiskili degildir.")
    rapor["tost"] = {"alt": alt_sinir, "ust": ust_sinir, "ort_oran": ort_o,
                     "ga90": [ort_o - gg, ort_o + gg],
                     "t_alt": t_alt, "p_alt": p_alt,
                     "t_ust": t_ust, "p_ust": p_ust, "p_tost": p_tost,
                     "esdeger": bool(p_tost < .05)}

    # ------------------------------- 3. BANT-ICI ALT ORNEKLEMDE McNEMAR
    bant_ici = [i for i in ortak if alt_sinir <= kelime_g3[i] / kelime_g2[i] <= ust_sinir]
    disari = [i for i in ortak if i not in set(bant_ici)]
    basli(f"3. BANT-ICI ALT ORNEKLEM — banda uymayan {len(disari)} cift atildi\n"
          f"   (kalan {len(bant_ici)} cift uzerinde McNemar yinelendi)")
    print(f"   Atilan cift no'lari: {disari}")
    mc = {}
    print(f"\n{'arac':16s} {'kapsam':8s} {'n':>4s} {'R_G2':>7s} {'R_G3':>7s} "
          f"{'b':>3s} {'c':>3s} {'p_exact':>12s}")
    for a in ARACLAR:
        for etiket, havuz in (("TUM", ortak), ("BANT", bant_ici)):
            g2k = {son_sayi(m): k for (m, ar), k in kayitlar.items()
                   if ar == a and k["grup"] == "G2_YZ"}
            g3k = {son_sayi(m): k for (m, ar), k in kayitlar.items()
                   if ar == a and k["grup"] == "G3_Insanlastirilmis"}
            ort = [i for i in havuz if i in g2k and i in g3k]
            if len(ort) < 5:
                continue
            y2 = {i: g2k[i]["yz_olasilik"] > ESIK for i in ort}
            y3 = {i: g3k[i]["yz_olasilik"] > ESIK for i in ort}
            b = sum(1 for i in ort if y2[i] and not y3[i])
            c = sum(1 for i in ort if not y2[i] and y3[i])
            r2 = sum(y2.values()) / len(ort)
            r3 = sum(y3.values()) / len(ort)
            p = stats.binomtest(b, b + c, 0.5).pvalue if b + c else 1.0
            print(f"{a:16s} {etiket:8s} {len(ort):4d} {r2:7.4f} {r3:7.4f} "
                  f"{b:3d} {c:3d} {p:12.6f}")
            mc[f"{a}|{etiket}"] = dict(n=len(ort), recall_G2=r2, recall_G3=r3,
                                       b=b, c=c, p_exact=p)
        print()
    rapor["mcnemar_bant_ici"] = mc
    rapor["bant_disi_ciftler"] = disari

    # ------------------------- 4. G3 ICINDE SKOR ~ KELIME ILISKISI (Spearman)
    basli("4. G3 ICINDE SKOR ile KELIME SAYISI ILISKISI (Spearman rho)\n"
          "   'Metin kisaldigi icin kacirildi' savi dogruysa rho POZITIF ve\n"
          "   anlamli olmalidir (uzun metin -> yuksek YZ skoru).")
    kor = {}
    print(f"{'arac':16s} {'dil':4s} {'n':>4s} {'rho':>8s} {'p':>12s}")
    for a in ARACLAR:
        for dil in ("TUM", "TUR", "ENG"):
            alt = [k for (m, ar), k in kayitlar.items()
                   if ar == a and k["grup"] == "G3_Insanlastirilmis"
                   and (dil == "TUM" or k["dil"] == dil)]
            if len(alt) < 10:
                continue
            x = [k["kelime"] for k in alt]
            y = [k["yz_olasilik"] for k in alt]
            if len(set(y)) < 2:
                print(f"{a:16s} {dil:4s} {len(alt):4d} {'—':>8s} "
                      f"{'(skor sabit)':>12s}")
                kor[f"{a}|{dil}"] = {"n": len(alt), "rho": None, "p": None,
                                     "not": "skor varyansi yok"}
                continue
            rho, p = stats.spearmanr(x, y)
            print(f"{a:16s} {dil:4s} {len(alt):4d} {rho:8.4f} {p:12.6f}")
            kor[f"{a}|{dil}"] = {"n": len(alt), "rho": float(rho), "p": float(p)}
        print()
    rapor["spearman_g3"] = kor

    # ---------------- 5. KACIRILAN CIFTLERDE UZUNLUK FARKI DAHA MI BUYUK?
    basli("5. KACIRILAN CIFTLER (b hucresi) vs DIGERLERI — uzunluk farki\n"
          "   Uzunluk karistiricisi gecerliyse, G3'te kacirilan ciftlerin\n"
          "   kisalma miktari digerlerinden BUYUK olmalidir (Mann-Whitney).")
    kac = {}
    for a in ARACLAR:
        g2k = {son_sayi(m): k for (m, ar), k in kayitlar.items()
               if ar == a and k["grup"] == "G2_YZ"}
        g3k = {son_sayi(m): k for (m, ar), k in kayitlar.items()
               if ar == a and k["grup"] == "G3_Insanlastirilmis"}
        ort = sorted(set(g2k) & set(g3k))
        if len(ort) < 10:
            continue
        b_no = [i for i in ort if g2k[i]["yz_olasilik"] > ESIK
                and not g3k[i]["yz_olasilik"] > ESIK]
        digeri = [i for i in ort if i not in set(b_no)]
        if len(b_no) < 3:
            print(f"\n  {a}: b hucresi n={len(b_no)} — sinama icin yetersiz.")
            kac[a] = {"n_b": len(b_no), "yetersiz": True}
            continue
        d_b = [kelime_g3[i] / kelime_g2[i] for i in b_no]
        d_d = [kelime_g3[i] / kelime_g2[i] for i in digeri]
        u = stats.mannwhitneyu(d_b, d_d, alternative="two-sided")
        print(f"\n  {a}: kacirilan n={len(b_no)}, diger n={len(digeri)}")
        print(f"    kacirilanlarda G3/G2 oran ort = {sum(d_b)/len(d_b):.4f}")
        print(f"    digerlerinde   G3/G2 oran ort = {sum(d_d)/len(d_d):.4f}")
        print(f"    Mann-Whitney U = {u.statistic:.1f}, p = {p_yaz(u.pvalue)}"
              f"   {'FARK VAR' if u.pvalue < .05 else 'fark yok'}")
        kac[a] = {"n_b": len(b_no), "n_diger": len(digeri),
                  "oran_b": sum(d_b) / len(d_b), "oran_diger": sum(d_d) / len(d_d),
                  "U": float(u.statistic), "p": float(u.pvalue)}
    rapor["kacirilan_uzunluk"] = kac

    cikti = ROOT / "sonuclar" / "uzunluk_kontrol_istatistik.json"
    cikti.write_text(json.dumps(rapor, ensure_ascii=False, indent=2, default=float),
                     encoding="utf-8")
    print(f"\n\nJSON ozet yazildi: {cikti}")


def statistics_ss(x: list[float]) -> float:
    """Ornek standart sapmasi (n-1)."""
    m = sum(x) / len(x)
    return math.sqrt(sum((v - m) ** 2 for v in x) / (len(x) - 1))


if __name__ == "__main__":
    main()
