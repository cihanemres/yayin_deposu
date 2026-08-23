"""SDT (d', c) + karar esigi duyarlilik analizi — hakem raporu 3/8 icin.

Girdi : analiz_yontem.yukle() ile ayni kayitlar (HAM_OLCUMLER.csv + JSONL)
Cikti : konsol raporu + sonuclar/sdt_esik_istatistik.json

Hesaplananlar
  1) Sinyal Tespit Teorisi olcutleri: d' (duyarlilik) ve c (karar olcutu),
     ayrica c' = c/d' ve beta. Iki sinyal kurgusu:
       - G2 vs G1  : saf YZ tespiti (temel kosul)
       - G2+G3 vs G1 : insanlastirma saldirisi dahil (zorlu kosul)
     Oran 0 veya 1 oldugunda z(.) tanimsizlastigindan log-lineer duzeltme
     (Hautus, 1995) uygulanir: H = (hit + 0.5)/(n_sinyal + 1) vb.
  2) Esik duyarliligi: tau in {10,...,90} icin FPR/TPR; %50'de varilan
     sonuclarin esik tercihine baglanip baglanmadigi.
  3) Nonparametrik ayirt etme gucu: AUC (Mann-Whitney U'ya denk).
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

from scipy import stats

from analiz_yontem import ARACLAR, ANA_BES, basli, p_yaz, yukle

ROOT = Path(__file__).resolve().parent
ESIKLER = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0]


def sdt_olcutleri(hit: int, n_sinyal: int, fa: int, n_gurultu: int) -> dict:
    """Log-lineer duzeltmeli d' ve c (Hautus, 1995; Stanislaw & Todorov, 1999)."""
    if n_sinyal == 0 or n_gurultu == 0:
        return {}
    H_ham = hit / n_sinyal
    F_ham = fa / n_gurultu
    duzeltme = H_ham in (0.0, 1.0) or F_ham in (0.0, 1.0)
    H = (hit + 0.5) / (n_sinyal + 1)
    F = (fa + 0.5) / (n_gurultu + 1)
    zH, zF = stats.norm.ppf(H), stats.norm.ppf(F)
    d = zH - zF
    c = -0.5 * (zH + zF)
    return {
        "hit": hit, "n_sinyal": n_sinyal, "fa": fa, "n_gurultu": n_gurultu,
        "H_ham": H_ham, "F_ham": F_ham, "H_duz": H, "F_duz": F,
        "d_prime": d, "c": c,
        "c_norm": c / d if d else None,
        "beta": math.exp(d * c) if abs(d * c) < 700 else None,
        "log_lineer_duzeltme": duzeltme,
    }


def auc_hesapla(poz: list[float], neg: list[float]) -> tuple[float, float]:
    """Mann-Whitney U'dan AUC + p."""
    if not poz or not neg:
        return float("nan"), float("nan")
    u = stats.mannwhitneyu(poz, neg, alternative="two-sided")
    return u.statistic / (len(poz) * len(neg)), u.pvalue


def alt_kume(kayitlar: dict, arac: str, dil: str) -> list[dict]:
    return [k for (m, ar), k in kayitlar.items()
            if ar == arac and (dil == "TUM" or k["dil"] == dil)]


def main() -> None:
    kayitlar = yukle()
    rapor: dict = {}

    # --------------------------------------------------------------- 1. SDT
    basli("1. SINYAL TESPIT TEORISI — d' (duyarlilik) ve c (karar olcutu), tau = %50\n"
          "   Kurgu A: sinyal = G2 (saf YZ)      | gurultu = G1 (insan)\n"
          "   Kurgu B: sinyal = G2 + G3 (tum YZ) | gurultu = G1 (insan)\n"
          "   * = log-lineer duzeltme uygulandi (ham oran 0 veya 1)")
    sdt_json = {}
    print(f"\n{'arac':16s} {'dil':4s} {'kurgu':6s} {'H_ham':>7s} {'F_ham':>7s} "
          f"{'d_prime':>9s} {'c':>9s} {'c/d':>8s}")
    for a in ARACLAR:
        for dil in ("TUM", "TUR", "ENG"):
            alt = alt_kume(kayitlar, a, dil)
            if not alt:
                continue
            g1 = [k for k in alt if k["grup"] == "G1_Insan"]
            g2 = [k for k in alt if k["grup"] == "G2_YZ"]
            g3 = [k for k in alt if k["grup"] == "G3_Insanlastirilmis"]
            fa = sum(1 for k in g1 if k["yz_olasilik"] > 50.0)
            for etiket, sinyal in (("A(G2)", g2), ("B(G2G3)", g2 + g3)):
                if not sinyal or not g1:
                    continue
                hit = sum(1 for k in sinyal if k["yz_olasilik"] > 50.0)
                s = sdt_olcutleri(hit, len(sinyal), fa, len(g1))
                yildiz = "*" if s["log_lineer_duzeltme"] else " "
                print(f"{a:16s} {dil:4s} {etiket:7s} {s['H_ham']:7.4f} {s['F_ham']:7.4f} "
                      f"{s['d_prime']:8.4f}{yildiz} {s['c']:9.4f} "
                      f"{(s['c_norm'] if s['c_norm'] is not None else float('nan')):8.4f}")
                sdt_json[f"{a}|{dil}|{etiket}"] = s
        print()
    rapor["sdt"] = sdt_json

    # --------------------------------------------------------------- 2. AUC
    basli("2. AUC — esikten bagimsiz ayirt etme gucu (Mann-Whitney U)")
    auc_json = {}
    print(f"{'arac':16s} {'dil':4s} {'kurgu':8s} {'n_poz':>6s} {'n_neg':>6s} "
          f"{'AUC':>8s} {'p':>14s}")
    for a in ARACLAR:
        for dil in ("TUM", "TUR", "ENG"):
            alt = alt_kume(kayitlar, a, dil)
            if not alt:
                continue
            neg = [k["yz_olasilik"] for k in alt if k["grup"] == "G1_Insan"]
            g2 = [k["yz_olasilik"] for k in alt if k["grup"] == "G2_YZ"]
            g3 = [k["yz_olasilik"] for k in alt if k["grup"] == "G3_Insanlastirilmis"]
            for etiket, poz in (("A(G2)", g2), ("B(G2G3)", g2 + g3)):
                if not poz or not neg:
                    continue
                auc, p = auc_hesapla(poz, neg)
                print(f"{a:16s} {dil:4s} {etiket:8s} {len(poz):6d} {len(neg):6d} "
                      f"{auc:8.4f} {p:14.3e}")
                auc_json[f"{a}|{dil}|{etiket}"] = {"n_poz": len(poz), "n_neg": len(neg),
                                                   "AUC": auc, "p": p}
        print()
    rapor["auc"] = auc_json

    # ------------------------------------------------------- 3. ESIK DUYARLILIGI
    basli("3. KARAR ESIGI DUYARLILIK ANALIZI — G1'de yanlis alarm orani (FPR)\n"
          "   Soru: %50 esigi araclari haksiz cezalandiriyor mu?")
    esik_json = {}
    print(f"{'arac':16s} {'dil':4s} " + " ".join(f"t={int(t):3d}" for t in ESIKLER))
    for a in ARACLAR:
        for dil in ("TUM", "TUR", "ENG"):
            g1 = [k for k in alt_kume(kayitlar, a, dil) if k["grup"] == "G1_Insan"]
            if not g1:
                continue
            satir = []
            for t in ESIKLER:
                fp = sum(1 for k in g1 if k["yz_olasilik"] > t)
                satir.append(fp / len(g1))
            print(f"{a:16s} {dil:4s} " + " ".join(f"{o:5.2f}" for o in satir)
                  + f"   (n={len(g1)})")
            esik_json[f"FPR|{a}|{dil}"] = {"n": len(g1),
                                           "esikler": ESIKLER, "oranlar": satir}
        print()

    print("\n   Ayni tabloda DUYARLILIK (recall, G2+G3 uzerinden):")
    print(f"{'arac':16s} {'dil':4s} " + " ".join(f"t={int(t):3d}" for t in ESIKLER))
    for a in ARACLAR:
        for dil in ("TUM", "TUR", "ENG"):
            yz = [k for k in alt_kume(kayitlar, a, dil) if k["gercek_etiket"] == "YZ"]
            if not yz:
                continue
            satir = [sum(1 for k in yz if k["yz_olasilik"] > t) / len(yz) for t in ESIKLER]
            print(f"{a:16s} {dil:4s} " + " ".join(f"{o:5.2f}" for o in satir)
                  + f"   (n={len(yz)})")
            esik_json[f"TPR|{a}|{dil}"] = {"n": len(yz),
                                           "esikler": ESIKLER, "oranlar": satir}
        print()
    rapor["esik_duyarlilik"] = esik_json

    # --------------------------- 4. Esige gore sonuc kararliligi: dil etkisi
    basli("4. SONUC KARARLILIGI — G1'de TUR vs ENG yanlis alarm farki her esikte\n"
          "   (Fisher's Exact, iki yonlu). Dil etkisi bulgusu esige bagimli mi?")
    kar_json = {}
    for a in ARACLAR:
        g1 = [k for k in alt_kume(kayitlar, a, "TUM") if k["grup"] == "G1_Insan"]
        if not g1:
            continue
        tur = [k for k in g1 if k["dil"] == "TUR"]
        eng = [k for k in g1 if k["dil"] == "ENG"]
        if not tur or not eng:
            continue
        print(f"\n  {a}  (TUR n={len(tur)}, ENG n={len(eng)})")
        satirlar = []
        for t in ESIKLER:
            ft = sum(1 for k in tur if k["yz_olasilik"] > t)
            fe = sum(1 for k in eng if k["yz_olasilik"] > t)
            _, p = stats.fisher_exact([[ft, len(tur) - ft], [fe, len(eng) - fe]])
            print(f"    tau={int(t):3d}: TUR {ft:3d}/{len(tur):3d} vs ENG {fe:3d}/{len(eng):3d}"
                  f"   Fisher p = {p_yaz(p)}   {'ANLAMLI' if p < .05 else '-'}")
            satirlar.append({"tau": t, "fp_tur": ft, "n_tur": len(tur),
                             "fp_eng": fe, "n_eng": len(eng), "p_fisher": p})
        kar_json[a] = satirlar
    rapor["dil_etkisi_esige_gore"] = kar_json

    # ------------------------ 5. Cochran Q her esikte (arac farki kararli mi?)
    def cochran_q(mat: list[list[int]]) -> tuple[float, int, float]:
        k, n = len(mat[0]), len(mat)
        G = [sum(s[j] for s in mat) for j in range(k)]
        L = [sum(s) for s in mat]
        N = sum(L)
        payda = k * N - sum(l * l for l in L)
        Q = ((k - 1) * (k * sum(g * g for g in G) - N * N) / payda) if payda else float("nan")
        return Q, k - 1, stats.chi2.sf(Q, k - 1)

    basli("5. COCHRAN Q HER ESIKTE — 5 arac arasindaki yanlis alarm farki (G1)")
    q_json = {}
    havuz: dict[str, dict[str, float]] = defaultdict(dict)
    for (m, ar), k in kayitlar.items():
        if k["grup"] == "G1_Insan" and ar in ANA_BES:
            havuz[m][ar] = k["yz_olasilik"]
    tam = [d for d in havuz.values() if len(d) == len(ANA_BES)]
    print(f"  Tam kayitli metin sayisi: {len(tam)}")
    for t in ESIKLER:
        mat = [[1 if d[a] > t else 0 for a in ANA_BES] for d in tam]
        Q, dof, p = cochran_q(mat)
        oran = {a: sum(s[j] for s in mat) / len(mat) for j, a in enumerate(ANA_BES)}
        print(f"    tau={int(t):3d}: Q({dof}, N={len(mat)}) = {Q:9.4f}, p = {p_yaz(p):26s}"
              + "  " + " ".join(f"{a[:4]}={o:.2f}" for a, o in oran.items()))
        q_json[str(int(t))] = {"Q": Q, "dof": dof, "p": p, "n": len(mat), "oranlar": oran}
    rapor["cochran_q_esige_gore"] = q_json

    cikti = ROOT / "sonuclar" / "sdt_esik_istatistik.json"
    cikti.write_text(json.dumps(rapor, ensure_ascii=False, indent=2, default=float),
                     encoding="utf-8")
    print(f"\n\nJSON ozet yazildi: {cikti}")


if __name__ == "__main__":
    main()
