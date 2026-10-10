"""YONTEM bolumu icin istatistiki analiz.

Girdi : HAM_OLCUMLER.csv (birincil, 1624 kayit) — yoksa
        sonuclar/olcum_sonuclari.jsonl (1597 kayit; CSV'nin alt kumesi)
        Kelime sayilari korpus xlsx'inden, tarih/kaynak bilgisi JSONL'den
        zenginlestirilir.
Cikti : konsol raporu + sonuclar/yontem_istatistik.json

Testler:
  1) G1 (insan) TUR vs ENG yanlis pozitif farki  -> Ki-Kare / Fisher's Exact
  2) G2 -> G3 duyarlilik dususu (eslesmis)       -> McNemar (exact + chi2)
  3) G1'de 5 aracin yanlis alarm kararlari       -> Cochran Q
Ek: uzunluk confound kontrolu (G2 vs G3 eslesmis kelime bandi)
"""
from __future__ import annotations

import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

from scipy import stats

ROOT = Path(__file__).resolve().parent
JSONL = ROOT / "sonuclar" / "olcum_sonuclari.jsonl"
CSV_HAM = ROOT / "HAM_OLCUMLER.csv"
ESIK = 50.0
ARACLAR = ["GPTZero", "ZeroGPT", "Copyleaks", "Sapling", "Originality_ai", "Pangram"]
ANA_BES = ["GPTZero", "ZeroGPT", "Sapling", "Originality_ai", "Pangram"]


def son_sayi(s: str) -> int:
    import re
    return int(re.findall(r"(\d+)", s)[-1])


def _jsonl_kayitlari() -> dict[tuple[str, str], dict]:
    son: dict[tuple[str, str], dict] = {}
    with JSONL.open(encoding="utf-8") as f:
        for satir in f:
            satir = satir.strip()
            if not satir:
                continue
            k = json.loads(satir)
            if k.get("yz_olasilik") is None:
                continue
            k.pop("ham_yanit", None)          # bellek
            son[(k["metin_id"], k["arac"])] = k   # sonraki eskisini ezer
    return son


def _kelime_haritasi() -> dict[str, int]:
    """metin_id -> kelime sayisi (korpus xlsx'i tek dogru kaynak)."""
    try:
        from yzdetect.corpus import yukle as korpus_yukle
        return {m.metin_id: m.kelime for m in korpus_yukle().values()}
    except Exception as e:                                  # korpus okunamazsa
        print(f"! Korpus okunamadi ({e}); kelime sayilari JSONL'den alinacak.")
        return {}


def yukle() -> dict[tuple[str, str], dict]:
    """CSV birincil kaynak; kelime korpustan, tarih/kaynak JSONL'den eklenir.

    CSV'de olup JSONL'de olmayan kayitlar 'kaynak=Excel(tarihsiz)' olarak
    isaretlenir — bunlar API protokolu disinda kalmis eski olcumlerdir.
    """
    jsonl = _jsonl_kayitlari()
    kelime = _kelime_haritasi()
    if not CSV_HAM.exists():
        print(f"! {CSV_HAM.name} yok; yalnizca JSONL kullanilacak.")
        for k in jsonl.values():
            k["kaynak"] = "API(JSONL)"
        return jsonl

    son: dict[tuple[str, str], dict] = {}
    with CSV_HAM.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            anahtar = (r["metin_id"], r["arac"])
            j = jsonl.get(anahtar)
            kayit = {
                "metin_id": r["metin_id"],
                "grup": r["grup"],
                "gercek_etiket": r["gercek_etiket"],
                "dil": r["dil"],
                "arac": r["arac"],
                "yz_olasilik": float(r["yz_olasilik"]),
                "karar": r["karar"],
                "kelime": kelime.get(r["metin_id"], (j or {}).get("kelime")),
                "tarih": (j or {}).get("tarih"),
                "kaynak": "API(JSONL)" if j else "Excel(tarihsiz)",
            }
            # CSV ile JSONL skoru catisirsa gorunur olsun
            if j and abs(j["yz_olasilik"] - kayit["yz_olasilik"]) > 1e-9:
                print(f"! SKOR CATISMASI {anahtar}: CSV={kayit['yz_olasilik']} "
                      f"JSONL={j['yz_olasilik']}")
            son[anahtar] = kayit
    eksik = set(jsonl) - set(son)
    if eksik:
        print(f"! JSONL'de olup CSV'de olmayan {len(eksik)} kayit CSV'ye eklendi.")
        for a in eksik:
            jsonl[a]["kaynak"] = "API(JSONL)"
            son[a] = jsonl[a]
    return son


def kaynak_raporu(kayitlar: dict[tuple[str, str], dict]) -> dict:
    """Olcum kokeni + bayat metin uyarisi.

    G3 metinleri v9'da (2026-07-18 sonrasi) yeniden uretildi. Bu tarihten ONCE
    olculmus her G3 kaydi ARTIK KORPUSTA OLMAYAN bir metne aittir.
    """
    basli("0c. OLCUM KOKENI VE GECERLILIK DENETIMI")
    kok = defaultdict(lambda: defaultdict(int))
    bayat = defaultdict(int)
    for (mid, arac), k in kayitlar.items():
        kok[arac][k["kaynak"]] += 1
        if k["grup"] == "G3_Insanlastirilmis" and (k["tarih"] or "") < "2026-07-18":
            bayat[arac] += 1
    print(f"{'arac':16s} {'API(JSONL)':>12s} {'Excel(tarihsiz)':>16s} {'BAYAT G3':>10s}")
    for a in ARACLAR:
        print(f"{a:16s} {kok[a]['API(JSONL)']:12d} {kok[a]['Excel(tarihsiz)']:16d} "
              f"{bayat[a]:10d}")
    if any(bayat.values()):
        print("\n  ! BAYAT G3: v9 oncesi (eski, uzunluk-confound'lu) metinlere ait "
              "olcumler.\n    Bu araclar icin G2->G3 karsilastirmasi GECERSIZDIR.")
    return {"koken": {a: dict(kok[a]) for a in ARACLAR}, "bayat_g3": dict(bayat)}


def karar_yz(k: dict) -> int:
    return 1 if k["yz_olasilik"] > ESIK else 0


def basli(s: str) -> None:
    print("\n" + "=" * 82)
    print(s)
    print("=" * 82)


def p_yaz(p: float) -> str:
    if p is None:
        return "—"
    if p < .001:
        return f"{p:.3e} (p < .001)"
    return f"{p:.6f}"


# ----------------------------------------------------------------------------
# GUVEN ARALIGI VE ETKI BUYUKLUGU YARDIMCILARI
# Hakem 5/7 (Bulgular) talebi: her oran ve etki buyuklugu icin %95 GA.
# ----------------------------------------------------------------------------
Z95 = 1.959963984540054           # standart normalin 0.975 kuantili
NAN = float("nan")


def wilson_ci(k: int, n: int, z: float = Z95) -> tuple[float, float]:
    """Bir oran icin Wilson skor araligi (%95). n kucukken Wald'dan ustun."""
    if not n:
        return (NAN, NAN)
    p = k / n
    d = 1 + z * z / n
    orta = (p + z * z / (2 * n)) / d
    yari = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, orta - yari), min(1.0, orta + yari)


def clopper_pearson(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Bir oran icin Clopper-Pearson (exact, binom) araligi."""
    if not n:
        return (NAN, NAN)
    alt = 0.0 if k == 0 else float(stats.beta.ppf(alpha / 2, k, n - k + 1))
    ust = 1.0 if k == n else float(stats.beta.ppf(1 - alpha / 2, k + 1, n - k))
    return alt, ust


def ora_yaz(k: int, n: int) -> str:
    """'0.9000 [0.7845, 0.9612]' bicimi (Wilson)."""
    if not n:
        return "—"
    alt, ust = wilson_ci(k, n)
    return f"{k/n:.4f} [{alt:.4f}, {ust:.4f}]"


def newcombe_fark(k1: int, n1: int, k2: int, n2: int) -> tuple[float, float, float]:
    """Bagimsiz iki oran farki icin Newcombe (skor tabanli) %95 GA."""
    if not n1 or not n2:
        return (NAN, NAN, NAN)
    a1, u1 = wilson_ci(k1, n1)
    a2, u2 = wilson_ci(k2, n2)
    p1, p2 = k1 / n1, k2 / n2
    fark = p1 - p2
    alt = fark - math.sqrt((p1 - a1) ** 2 + (u2 - p2) ** 2)
    ust = fark + math.sqrt((u1 - p1) ** 2 + (p2 - a2) ** 2)
    return fark, max(-1.0, alt), min(1.0, ust)


def phi_ci(phi: float | None, n: int) -> tuple[float, float]:
    """phi (2x2 Pearson r) icin Fisher z donusumlu %95 GA."""
    if phi is None or n <= 3:
        return (NAN, NAN)
    phic = min(max(phi, -0.999999), 0.999999)
    z = math.atanh(phic)
    se = 1.0 / math.sqrt(n - 3)
    return math.tanh(z - Z95 * se), math.tanh(z + Z95 * se)


def mcnemar_etki(b: int, c: int) -> dict | None:
    """McNemar etki buyuklugu.

    Kosullu (exact) yaklasim: uyumsuz cift sayisi m = b + c sabit tutulur ve
    pi = b/m oranindan gidilir. OR = pi/(1-pi) = b/c; c = 0 oldugunda nokta
    kestirim tanimsiz (inf) olur, bu yuzden %95 GA pi'nin Clopper-Pearson
    araligindan donusturulerek verilir (sonlu alt sinir korunur).
    Cohen g = pi - 0.5 (isaretli; |g| Cohen'in tanimi).
    """
    m = b + c
    if not m:
        return None
    pi = b / m
    alt, ust = clopper_pearson(b, m)
    orr = float("inf") if c == 0 else b / c
    or_alt = float("inf") if alt >= 1 else alt / (1 - alt)
    or_ust = float("inf") if ust >= 1 else ust / (1 - ust)
    return dict(m=m, pi=pi, pi_alt=alt, pi_ust=ust,
                OR=orr, OR_alt=or_alt, OR_ust=or_ust,
                g=pi - 0.5, g_alt=alt - 0.5, g_ust=ust - 0.5)


def eslesmis_fark_ci(b: int, c: int, n: int) -> tuple[float, float, float]:
    """Eslesmis iki oran farki (b-c)/n icin Wald %95 GA."""
    if not n:
        return (NAN, NAN, NAN)
    fark = (b - c) / n
    var = ((b + c) - (b - c) ** 2 / n) / (n * n)
    se = math.sqrt(var) if var > 0 else 0.0
    return fark, max(-1.0, fark - Z95 * se), min(1.0, fark + Z95 * se)


def sayi_yaz(x: float) -> str:
    if x is None:
        return "—"
    if math.isinf(x):
        return "inf"
    if math.isnan(x):
        return "—"
    return f"{x:.4f}"


def main() -> None:
    kayitlar = yukle()
    rapor: dict = {}

    # ---------------------------------------------------------------- KAPSAM
    basli("0. KAPSAM — (grup x dil x arac) basina basarili olcum sayisi")
    kapsam = defaultdict(int)
    for (mid, arac), k in kayitlar.items():
        kapsam[(arac, k["grup"], k["dil"])] += 1
    print(f"{'arac':16s} " + " ".join(f"{g[:6]}-{d:3s}" for g in
          ("G1_Insan", "G2_YZ", "G3_Insanlastirilmis") for d in ("TUR", "ENG")))
    kapsam_json = {}
    for a in ARACLAR:
        hucre = [kapsam[(a, g, d)] for g in ("G1_Insan", "G2_YZ", "G3_Insanlastirilmis")
                 for d in ("TUR", "ENG")]
        print(f"{a:16s} " + " ".join(f"{n:10d}" for n in hucre) + f"   toplam={sum(hucre)}")
        kapsam_json[a] = {"hucreler": hucre, "toplam": sum(hucre)}
    print(f"\nToplam basarili olcum: {len(kayitlar)}")
    rapor["kapsam"] = kapsam_json
    rapor["toplam_olcum"] = len(kayitlar)
    rapor["koken"] = kaynak_raporu(kayitlar)

    # --------------------------------------------------- UZUNLUK CONFOUND'U
    basli("0b. UZUNLUK KONTROLU — G2 -> G3 eslesmis kelime sayilari")
    uz = {}
    for (mid, arac), k in kayitlar.items():
        uz[mid] = (k["grup"], k["dil"], k["kelime"])
    g2 = {son_sayi(m): v for m, v in uz.items() if v[0] == "G2_YZ"}
    g3 = {son_sayi(m): v for m, v in uz.items() if v[0] == "G3_Insanlastirilmis"}
    g1 = {son_sayi(m): v for m, v in uz.items() if v[0] == "G1_Insan"}
    for ad, d in (("G1", g1), ("G2", g2), ("G3", g3)):
        kl = [v[2] for v in d.values()]
        print(f"  {ad}: n={len(kl):3d}  ort={sum(kl)/len(kl):7.2f}  min={min(kl):4d}  max={max(kl):4d}")
    ortak = sorted(set(g2) & set(g3))
    oranlar = [g3[i][2] / g2[i][2] for i in ortak]
    band10 = sum(1 for o in oranlar if 0.90 <= o <= 1.10)
    band20 = sum(1 for o in oranlar if 0.80 <= o <= 1.20)
    print(f"\n  Eslesmis cift: {len(ortak)}")
    print(f"  G3/G2 uzunluk orani: ort={sum(oranlar)/len(oranlar):.4f} "
          f"min={min(oranlar):.4f} max={max(oranlar):.4f}")
    print(f"  +/- %10 bandinda: {band10}/{len(ortak)} ({100*band10/len(ortak):.1f}%)")
    print(f"  +/- %20 bandinda: {band20}/{len(ortak)} ({100*band20/len(ortak):.1f}%)")
    t_es = stats.ttest_rel([g3[i][2] for i in ortak], [g2[i][2] for i in ortak])
    w_es = stats.wilcoxon([g3[i][2] for i in ortak], [g2[i][2] for i in ortak])
    print(f"  Eslesmis t-testi: t({len(ortak)-1}) = {t_es.statistic:.4f}, p = {p_yaz(t_es.pvalue)}")
    print(f"  Wilcoxon         : W = {w_es.statistic:.1f}, p = {p_yaz(w_es.pvalue)}")
    rapor["uzunluk"] = {
        "n_cift": len(ortak),
        "ort_oran": sum(oranlar) / len(oranlar),
        "min_oran": min(oranlar), "max_oran": max(oranlar),
        "band_10": band10, "band_20": band20,
        "t": t_es.statistic, "t_p": t_es.pvalue,
        "wilcoxon_W": float(w_es.statistic), "wilcoxon_p": float(w_es.pvalue),
        "G1_ort": sum(v[2] for v in g1.values()) / len(g1),
        "G2_ort": sum(v[2] for v in g2.values()) / len(g2),
        "G3_ort": sum(v[2] for v in g3.values()) / len(g3),
    }

    # ------------------------------------------------------------- METRIKLER
    basli("1. TEMEL METRIKLER — arac x (tum korpus / TUR / ENG)\n"
          "   F1_tum : pozitif sinif = G2 + G3   |   F1_G2 : pozitif sinif = yalniz G2\n"
          "   (BULGULAR_NotebookLM_1.md F1 sutunu F1_G2 kurgusunu kullaniyor)")
    met_json = {}
    print(f"{'arac':16s} {'dil':4s} {'n':>4s} {'TP':>4s} {'FN':>4s} {'FP':>4s} {'TN':>4s} "
          f"{'Recall':>7s} {'Spec':>7s} {'FPR':>7s} {'F1_tum':>7s} {'F1_G2':>7s}")
    for a in ARACLAR:
        for dil in ("TUM", "TUR", "ENG"):
            alt = [k for (m, ar), k in kayitlar.items()
                   if ar == a and (dil == "TUM" or k["dil"] == dil)]
            if not alt:
                continue
            tp = sum(1 for k in alt if k["gercek_etiket"] == "YZ" and karar_yz(k))
            fn = sum(1 for k in alt if k["gercek_etiket"] == "YZ" and not karar_yz(k))
            fp = sum(1 for k in alt if k["gercek_etiket"] == "Insan" and karar_yz(k))
            tn = sum(1 for k in alt if k["gercek_etiket"] == "Insan" and not karar_yz(k))
            rec = tp / (tp + fn) if tp + fn else float("nan")
            spec = tn / (tn + fp) if tn + fp else float("nan")
            fpr = fp / (fp + tn) if fp + tn else float("nan")
            prec = tp / (tp + fp) if tp + fp else float("nan")
            f1 = 2 * prec * rec / (prec + rec) if prec + rec else float("nan")
            # F1_G2: pozitif sinif yalniz G2 (BULGULAR belgesindeki kurgu)
            tp2 = sum(1 for k in alt if k["grup"] == "G2_YZ" and karar_yz(k))
            fn2 = sum(1 for k in alt if k["grup"] == "G2_YZ" and not karar_yz(k))
            rec2 = tp2 / (tp2 + fn2) if tp2 + fn2 else float("nan")
            pre2 = tp2 / (tp2 + fp) if tp2 + fp else float("nan")
            f1g2 = 2 * pre2 * rec2 / (pre2 + rec2) if pre2 + rec2 else float("nan")
            print(f"{a:16s} {dil:4s} {len(alt):4d} {tp:4d} {fn:4d} {fp:4d} {tn:4d} "
                  f"{rec:7.4f} {spec:7.4f} {fpr:7.4f} {f1:7.4f} {f1g2:7.4f}")
            met_json[f"{a}|{dil}"] = dict(n=len(alt), TP=tp, FN=fn, FP=fp, TN=tn,
                                          recall=rec, spec=spec, FPR=fpr, F1=f1,
                                          F1_G2=f1g2)

    # ---- 1b. ORANLAR ICIN %95 GUVEN ARALIKLARI -----------------------------
    basli("1b. ORANLAR ICIN %95 GUVEN ARALIGI\n"
          "    Wilson skor araligi (birincil) — FPR icin ayrica Clopper-Pearson (exact)")
    print(f"{'arac':16s} {'dil':4s} {'Recall [%95 GA]':>26s} {'Spec [%95 GA]':>26s} "
          f"{'FPR [%95 GA]':>26s} {'FPR exact GA':>20s}")
    for anahtar, v in met_json.items():
        a, dil = anahtar.split("|")
        n_poz = v["TP"] + v["FN"]
        n_neg = v["TN"] + v["FP"]
        cp = clopper_pearson(v["FP"], n_neg)
        print(f"{a:16s} {dil:4s} {ora_yaz(v['TP'], n_poz):>26s} "
              f"{ora_yaz(v['TN'], n_neg):>26s} {ora_yaz(v['FP'], n_neg):>26s} "
              f"{('[%.4f, %.4f]' % cp) if n_neg else '—':>20s}")
        v["recall_GA95"] = list(wilson_ci(v["TP"], n_poz))
        v["spec_GA95"] = list(wilson_ci(v["TN"], n_neg))
        v["FPR_GA95"] = list(wilson_ci(v["FP"], n_neg))
        v["FPR_GA95_clopper_pearson"] = list(cp)
        v["GA_yontemi"] = "Wilson skor araligi; FPR icin ek olarak Clopper-Pearson"
    rapor["metrikler"] = met_json

    # ------------------------- 2. KI-KARE / FISHER : G1'de TUR vs ENG yanlis pozitif
    basli("2. G1 (INSAN) — TUR vs ENG YANLIS POZITIF FARKI (Ki-Kare / Fisher)")
    ki_json = {}
    for a in ARACLAR:
        alt = [k for (m, ar), k in kayitlar.items() if ar == a and k["grup"] == "G1_Insan"]
        if not alt:
            continue
        tablo = []
        for dil in ("TUR", "ENG"):
            d = [k for k in alt if k["dil"] == dil]
            fp = sum(karar_yz(k) for k in d)
            tablo.append([fp, len(d) - fp])
        beklenen_ok = True
        chi2 = dof = p_chi = None
        try:
            chi2, p_chi, dof, bek = stats.chi2_contingency(tablo, correction=False)
            beklenen_ok = bool((bek >= 5).all())
            chi2y, p_chiy, _, _ = stats.chi2_contingency(tablo, correction=True)
        except ValueError:
            chi2y = p_chiy = None
        odds, p_fis = stats.fisher_exact(tablo)
        n = sum(map(sum, tablo))
        # phi: TANIM GEREGI duzeltmesiz (Pearson) chi2 uzerinden hesaplanir.
        # Yates tabanli phi_Y yalnizca BELGELEME icin yazdirilir: elyazmasinin
        # oz'undeki 0.28 ile Tablo 5'teki 0.26 farkinin kaynagi budur.
        phi = math.sqrt(chi2 / n) if chi2 is not None else None
        phi_y = math.sqrt(chi2y / n) if chi2y is not None else None
        phi_alt, phi_ust = phi_ci(phi, n)
        fp_t, n_t = tablo[0][0], sum(tablo[0])
        fp_e, n_e = tablo[1][0], sum(tablo[1])
        cp_t, cp_e = clopper_pearson(fp_t, n_t), clopper_pearson(fp_e, n_e)
        rd, rd_alt, rd_ust = newcombe_fark(fp_t, n_t, fp_e, n_e)
        # Fisher kosullu OR icin exact GA (OR = inf olsa da alt sinir sonlu kalir)
        or_alt = or_ust = None
        try:
            _ga = stats.contingency.odds_ratio(tablo, kind="conditional").confidence_interval(0.95)
            or_alt, or_ust = float(_ga.low), float(_ga.high)
        except Exception:
            pass
        print(f"\n  {a}")
        print(f"    TUR: FP={fp_t:3d}/{n_t:3d} (%{100*fp_t/n_t:.2f})"
              f"   ENG: FP={fp_e:3d}/{n_e:3d} (%{100*fp_e/n_e:.2f})")
        print(f"    TUR FPR = {ora_yaz(fp_t, n_t)} (Wilson)   "
              f"Clopper-Pearson [{cp_t[0]:.4f}, {cp_t[1]:.4f}]")
        print(f"    ENG FPR = {ora_yaz(fp_e, n_e)} (Wilson)   "
              f"Clopper-Pearson [{cp_e[0]:.4f}, {cp_e[1]:.4f}]")
        print(f"    Risk farki (TUR - ENG) = {rd:+.4f}, %95 GA (Newcombe) = "
              f"[{rd_alt:+.4f}, {rd_ust:+.4f}]")
        if chi2 is not None:
            print(f"    Pearson chi2({dof}, N = {n}) = {chi2:.4f}, p = {p_yaz(p_chi)}"
                  f"   [phi = {phi:.4f}, %95 GA (Fisher z) = [{phi_alt:.4f}, {phi_ust:.4f}]]")
            print(f"    Yates duzeltmeli chi2({dof}, N = {n}) = {chi2y:.4f}, p = {p_yaz(p_chiy)}"
                  f"   [phi_Yates = {phi_y:.4f} — RAPORLANMAZ, izlenebilirlik icin]")
            print(f"    Beklenen frekans >= 5 varsayimi: {'SAGLANDI' if beklenen_ok else 'IHLAL -> Fisher esas'}")
        print(f"    Fisher's Exact: OR = {odds if math.isfinite(odds) else 'inf'}, p = {p_yaz(p_fis)}"
              + (f"   %95 GA (kosullu exact) = [{or_alt:.4f}, {sayi_yaz(or_ust)}]"
                 if or_alt is not None else ""))
        ki_json[a] = dict(tablo=tablo, chi2=chi2, dof=dof, N=n, p_chi2=p_chi,
                          chi2_yates=chi2y, p_yates=p_chiy,
                          phi=phi, phi_GA95=[phi_alt, phi_ust],
                          phi_yates_belgeleme=phi_y,
                          FPR_TUR=fp_t / n_t, FPR_TUR_GA95=list(wilson_ci(fp_t, n_t)),
                          FPR_TUR_GA95_clopper_pearson=list(cp_t),
                          FPR_ENG=fp_e / n_e, FPR_ENG_GA95=list(wilson_ci(fp_e, n_e)),
                          FPR_ENG_GA95_clopper_pearson=list(cp_e),
                          risk_farki=rd, risk_farki_GA95=[rd_alt, rd_ust],
                          fisher_or=odds if math.isfinite(odds) else None,
                          fisher_or_GA95=[or_alt, or_ust] if or_alt is not None else None,
                          p_fisher=p_fis, beklenen_ok=beklenen_ok)
    rapor["ki_kare_dil"] = ki_json

    # ------------------------------- 3. McNEMAR : G2 -> G3 duyarlilik dususu
    basli("3. McNEMAR — G2 (saf YZ) -> G3 (insanlastirilmis) DUYARLILIK DUSUSU")
    mc_json = {}
    for a in ARACLAR:
        for dil in ("TUM", "TUR", "ENG"):
            g2k = {son_sayi(m): k for (m, ar), k in kayitlar.items()
                   if ar == a and k["grup"] == "G2_YZ" and (dil == "TUM" or k["dil"] == dil)}
            g3k = {son_sayi(m): k for (m, ar), k in kayitlar.items()
                   if ar == a and k["grup"] == "G3_Insanlastirilmis" and (dil == "TUM" or k["dil"] == dil)}
            ort = sorted(set(g2k) & set(g3k))
            if len(ort) < 5:
                continue
            # dil eslesmesi dogrulamasi
            uyum = all(g2k[i]["dil"] == g3k[i]["dil"] for i in ort)
            a11 = sum(1 for i in ort if karar_yz(g2k[i]) and karar_yz(g3k[i]))
            b = sum(1 for i in ort if karar_yz(g2k[i]) and not karar_yz(g3k[i]))   # G2 yakaladi, G3 kacti
            c = sum(1 for i in ort if not karar_yz(g2k[i]) and karar_yz(g3k[i]))
            d = sum(1 for i in ort if not karar_yz(g2k[i]) and not karar_yz(g3k[i]))
            r2 = (a11 + b) / len(ort)
            r3 = (a11 + c) / len(ort)
            # exact binom (b+c kucukse esas), ayrica Yates duzeltmeli chi2
            p_exact = stats.binomtest(b, b + c, 0.5).pvalue if (b + c) else 1.0
            if b + c:
                chi_y = (abs(b - c) - 1) ** 2 / (b + c)
                p_y = stats.chi2.sf(chi_y, 1)
                chi_p = (b - c) ** 2 / (b + c)
                p_p = stats.chi2.sf(chi_p, 1)
            else:
                chi_y = p_y = chi_p = p_p = None
            print(f"\n  {a} [{dil}]  n_cift={len(ort)}  (dil eslesmesi: {'OK' if uyum else 'UYUMSUZ'})")
            print(f"    Recall G2 = {r2:.4f} ({a11+b}/{len(ort)})   "
                  f"Recall G3 = {r3:.4f} ({a11+c}/{len(ort)})   fark = {r2-r3:+.4f}")
            print(f"    Uyumsuz hucreler: b (G2+/G3-) = {b}, c (G2-/G3+) = {c}   "
                  f"[a = {a11}, d = {d}]")
            if chi_y is not None:
                print(f"    McNemar chi2(1) = {chi_p:.4f} (duzeltmesiz), p = {p_yaz(p_p)}")
                print(f"    McNemar chi2(1) = {chi_y:.4f} (Yates), p = {p_yaz(p_y)}")
            print(f"    Exact binom (b+c = {b+c}): p = {p_yaz(p_exact)}")
            # ---- ETKI BUYUKLUKLERI (hakem 5/7 talebi) ----
            etki = mcnemar_etki(b, c)
            fark_d, fark_alt, fark_ust = eslesmis_fark_ci(b, c, len(ort))
            print(f"    Eslesmis oran farki (G2-G3) = {fark_d:+.4f}, %95 GA = "
                  f"[{fark_alt:+.4f}, {fark_ust:+.4f}]")
            if etki:
                print(f"    Etki buyuklugu — OR = {sayi_yaz(etki['OR'])} "
                      f"(b/c; c = 0 ise tanimsiz/inf), %95 GA (kosullu exact) = "
                      f"[{etki['OR_alt']:.4f}, {sayi_yaz(etki['OR_ust'])}]")
                print(f"    Etki buyuklugu — Cohen g = {etki['g']:+.4f} "
                      f"(pi = b/(b+c) = {etki['pi']:.4f}), %95 GA = "
                      f"[{etki['g_alt']:+.4f}, {etki['g_ust']:+.4f}]")
            else:
                print("    Etki buyuklugu: uyumsuz cift yok (b + c = 0) -> tanimsiz")
            mc_json[f"{a}|{dil}"] = dict(n=len(ort), a=a11, b=b, c=c, d=d,
                                         recall_G2=r2, recall_G3=r3, fark=r2 - r3,
                                         chi2=chi_p, p_chi2=p_p,
                                         chi2_yates=chi_y, p_yates=p_y,
                                         p_exact=p_exact,
                                         fark_GA95=[fark_alt, fark_ust],
                                         OR=(None if not etki else
                                             (None if math.isinf(etki["OR"]) else etki["OR"])),
                                         OR_sonsuz=bool(etki and math.isinf(etki["OR"])),
                                         OR_GA95=(None if not etki else
                                                  [etki["OR_alt"],
                                                   None if math.isinf(etki["OR_ust"])
                                                   else etki["OR_ust"]]),
                                         cohen_g=(None if not etki else etki["g"]),
                                         cohen_g_GA95=(None if not etki else
                                                       [etki["g_alt"], etki["g_ust"]]))
    rapor["mcnemar"] = mc_json

    # ---------------------------------- 4. COCHRAN Q : G1'de 5 aracin yanlis alarmi
    def cochran_q(mat: list[list[int]]) -> tuple[float, int, float]:
        """mat: n_denek x k_kosul, 0/1."""
        k = len(mat[0])
        n = len(mat)
        G = [sum(satir[j] for satir in mat) for j in range(k)]     # sutun toplami
        L = [sum(satir) for satir in mat]                          # satir toplami
        N = sum(L)
        pay = (k - 1) * (k * sum(g * g for g in G) - N * N)
        payda = k * N - sum(l * l for l in L)
        Q = pay / payda if payda else float("nan")
        return Q, k - 1, stats.chi2.sf(Q, k - 1)

    basli("4. COCHRAN Q — G1 (insan) metinlerinde 5 aracin YANLIS ALARM kararlari")
    coch_json = {}
    for dil in ("TUM", "TUR", "ENG"):
        satirlar, idler = [], []
        havuz = {}
        for (m, ar), k in kayitlar.items():
            if k["grup"] != "G1_Insan" or ar not in ANA_BES:
                continue
            if dil != "TUM" and k["dil"] != dil:
                continue
            havuz.setdefault(m, {})[ar] = karar_yz(k)
        for m, d in sorted(havuz.items(), key=lambda x: son_sayi(x[0])):
            if len(d) == len(ANA_BES):
                satirlar.append([d[a] for a in ANA_BES])
                idler.append(m)
        if len(satirlar) < 5:
            print(f"  [{dil}] yeterli tam kayit yok (n={len(satirlar)})")
            continue
        Q, dof, p = cochran_q(satirlar)
        oranlar = {a: sum(s[j] for s in satirlar) / len(satirlar)
                   for j, a in enumerate(ANA_BES)}
        print(f"\n  [{dil}] n = {len(satirlar)} metin x k = {len(ANA_BES)} arac")
        print("    Yanlis alarm (FPR) oranlari ve %95 GA (Wilson):")
        fpr_ga = {}
        for j, a in enumerate(ANA_BES):
            kk = sum(s[j] for s in satirlar)
            fpr_ga[a] = list(wilson_ci(kk, len(satirlar)))
            print(f"      {a:15s} FPR = {ora_yaz(kk, len(satirlar))}  "
                  f"({kk}/{len(satirlar)})")
        # H1'in operasyonel ifadesi: araclar arasi FPR yayilimi
        en_dus = min(oranlar, key=oranlar.get)
        en_yuk = max(oranlar, key=oranlar.get)
        k_dus = round(oranlar[en_dus] * len(satirlar))
        k_yuk = round(oranlar[en_yuk] * len(satirlar))
        # ayni metinler uzerinde olculdugu icin ESLESMIS fark araligi kullanilir
        i_yuk, i_dus = ANA_BES.index(en_yuk), ANA_BES.index(en_dus)
        b_uc = sum(1 for s_ in satirlar if s_[i_yuk] and not s_[i_dus])
        c_uc = sum(1 for s_ in satirlar if not s_[i_yuk] and s_[i_dus])
        yay, yay_alt, yay_ust = eslesmis_fark_ci(b_uc, c_uc, len(satirlar))
        print(f"    H1 (performans heterojenligi) operasyonel olcut — FPR yayilimi: "
              f"{en_dus} = {oranlar[en_dus]:.4f} ... {en_yuk} = {oranlar[en_yuk]:.4f}")
        print(f"      Uc-degerler arasi FPR farki = {yay:+.4f}, %95 GA (eslesmis Wald) = "
              f"[{yay_alt:+.4f}, {yay_ust:+.4f}]   "
              f"(eslesmis fark; b = {b_uc}, c = {c_uc})")
        print(f"    Cochran Q({dof}, N = {len(satirlar)}) = {Q:.4f}, p = {p_yaz(p)}")
        W = Q / (len(satirlar) * (len(ANA_BES) - 1)) if len(satirlar) else float("nan")
        print(f"    Etki buyuklugu — Kendall W = Q / [n(k-1)] = {W:.4f}  "
              f"(0 = tam uyum yok ... 1 = araclar tamamen ayrisik)")
        # ikili post-hoc (McNemar exact, Bonferroni)
        ciftler = []
        for i in range(len(ANA_BES)):
            for j in range(i + 1, len(ANA_BES)):
                b = sum(1 for s in satirlar if s[i] and not s[j])
                c = sum(1 for s in satirlar if not s[i] and s[j])
                pv = stats.binomtest(b, b + c, 0.5).pvalue if b + c else 1.0
                ciftler.append((ANA_BES[i], ANA_BES[j], b, c, pv, min(1.0, pv * 10)))
        print("    Post-hoc (ikili McNemar exact, Bonferroni x10) + etki buyuklugu:")
        for x, y, b, c, pv, pa in sorted(ciftler, key=lambda t: t[4]):
            e = mcnemar_etki(b, c)
            ek = ("g = ----   OR = ----" if not e else
                  f"g = {e['g']:+.4f} [{e['g_alt']:+.4f}, {e['g_ust']:+.4f}]   "
                  f"OR = {sayi_yaz(e['OR'])} [{e['OR_alt']:.4f}, {sayi_yaz(e['OR_ust'])}]")
            print(f"      {x:15s} vs {y:15s} b={b:3d} c={c:3d} "
                  f"p={p_yaz(pv):24s} p_adj={p_yaz(pa):24s} {ek}")
        coch_json[dil] = dict(n=len(satirlar), k=len(ANA_BES), Q=Q, dof=dof, p=p,
                              kendall_W=W, oranlar=oranlar, FPR_GA95=fpr_ga,
                              FPR_yayilimi=dict(en_dusuk=en_dus, en_yuksek=en_yuk,
                                                fark=yay, GA95=[yay_alt, yay_ust]),
                              posthoc=[dict(a=x, b_arac=y, b=b, c=c, p=pv, p_adj=pa,
                                            cohen_g=(None if not mcnemar_etki(b, c)
                                                     else mcnemar_etki(b, c)["g"]),
                                            cohen_g_GA95=(None if not mcnemar_etki(b, c)
                                                          else [mcnemar_etki(b, c)["g_alt"],
                                                                mcnemar_etki(b, c)["g_ust"]]))
                                       for x, y, b, c, pv, pa in ciftler])
    rapor["cochran_q"] = coch_json

    cikti = ROOT / "sonuclar" / "yontem_istatistik.json"
    cikti.write_text(json.dumps(rapor, ensure_ascii=False, indent=2, default=float),
                     encoding="utf-8")
    print(f"\n\nJSON ozet yazildi: {cikti}")


if __name__ == "__main__":
    main()
