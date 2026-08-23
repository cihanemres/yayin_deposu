"""Uretici model kirilimi — oz-parafraz vs capraz-model insanlastirma.

G3 metinlerinin tamami Claude ile insanlastirildi. G2'nin yarisi Claude, yarisi
Gemini uretimi oldugundan:
  - Claude uretimi 50 metin -> Claude ile insanlastirma = OZ-PARAFRAZ
  - Gemini uretimi 50 metin -> Claude ile insanlastirma = CAPRAZ-MODEL

Soru: dedektor kararlari bu iki alt kosulda farklilasiyor mu? Farklilasiyorsa,
G3 bulgulari kismen "model ailesi esligi" etkisini tasiyor demektir.

Cikti: konsol + sonuclar/uretici_model_istatistik.json
"""
from __future__ import annotations

import json
from pathlib import Path

import openpyxl
from scipy import stats

from analiz_yontem import ARACLAR, basli, p_yaz, son_sayi, yukle

ROOT = Path(__file__).resolve().parent
KORPUS = ROOT / "YZ_Tespit_Korpus_v9.xlsx"
ESIK = 50.0


def model_haritasi() -> dict[int, str]:
    """G2 sira no -> uretici model (Claude / Gemini)."""
    wb = openpyxl.load_workbook(KORPUS, read_only=True)
    ws = wb["G2_YZ_Korpus"]
    rows = ws.iter_rows(values_only=True)
    hdr = next(rows)
    i_id, i_model = hdr.index("metin_id"), hdr.index("Model")
    return {son_sayi(r[i_id]): r[i_model] for r in rows if r[i_id]}


def main() -> None:
    kayitlar = yukle()
    model = model_haritasi()
    rapor: dict = {}

    dagilim = {m: sum(1 for v in model.values() if v == m) for m in set(model.values())}
    basli(f"URETICI MODEL DAGILIMI: {dagilim}")

    for grup, ad in (("G2_YZ", "G2 (saf YZ)"),
                     ("G3_Insanlastirilmis", "G3 (insanlastirilmis)")):
        basli(f"{ad} — YZ olarak yakalanma orani, uretici modele gore\n"
              f"   (G3'te Claude = oz-parafraz, Gemini = capraz-model)")
        print(f"{'arac':16s} {'dil':4s} {'Claude':>12s} {'Gemini':>12s} "
              f"{'fark':>7s} {'Fisher p':>12s}")
        for a in ARACLAR:
            for dil in ("TUM", "TUR", "ENG"):
                alt = [(son_sayi(m), k) for (m, ar), k in kayitlar.items()
                       if ar == a and k["grup"] == grup
                       and (dil == "TUM" or k["dil"] == dil)]
                if len(alt) < 10:
                    continue
                tablo = []
                oranlar = {}
                for mdl in ("Claude", "Gemini"):
                    d = [k for no, k in alt if model.get(no) == mdl]
                    if not d:
                        tablo = []
                        break
                    yak = sum(1 for k in d if k["yz_olasilik"] > ESIK)
                    tablo.append([yak, len(d) - yak])
                    oranlar[mdl] = (yak, len(d))
                if not tablo:
                    continue
                _, p = stats.fisher_exact(tablo)
                oc = oranlar["Claude"][0] / oranlar["Claude"][1]
                og = oranlar["Gemini"][0] / oranlar["Gemini"][1]
                isaret = "  *" if p < .05 else ""
                print(f"{a:16s} {dil:4s} "
                      f"{oranlar['Claude'][0]:4d}/{oranlar['Claude'][1]:<3d}={oc:5.2f} "
                      f"{oranlar['Gemini'][0]:4d}/{oranlar['Gemini'][1]:<3d}={og:5.2f} "
                      f"{oc-og:+7.2f} {p:12.6f}{isaret}")
                rapor[f"{grup}|{a}|{dil}"] = {
                    "claude": list(oranlar["Claude"]),
                    "gemini": list(oranlar["Gemini"]),
                    "oran_claude": oc, "oran_gemini": og,
                    "fark": oc - og, "p_fisher": float(p)}
            print()

    # G2 -> G3 dususu, uretici modele gore (eslesmis)
    basli("INSANLASTIRMANIN ETKISI, URETICI MODELE GORE (eslesmis)\n"
          "   b = G2'de yakalanip G3'te kacirilan cift sayisi")
    print(f"{'arac':16s} {'model':8s} {'n':>4s} {'R_G2':>7s} {'R_G3':>7s} "
          f"{'b':>3s} {'c':>3s} {'p_exact':>12s}")
    es = {}
    for a in ARACLAR:
        for mdl in ("Claude", "Gemini"):
            g2k = {son_sayi(m): k for (m, ar), k in kayitlar.items()
                   if ar == a and k["grup"] == "G2_YZ" and model.get(son_sayi(m)) == mdl}
            g3k = {son_sayi(m): k for (m, ar), k in kayitlar.items()
                   if ar == a and k["grup"] == "G3_Insanlastirilmis"
                   and model.get(son_sayi(m)) == mdl}
            ort = sorted(set(g2k) & set(g3k))
            if len(ort) < 5:
                continue
            y2 = {i: g2k[i]["yz_olasilik"] > ESIK for i in ort}
            y3 = {i: g3k[i]["yz_olasilik"] > ESIK for i in ort}
            b = sum(1 for i in ort if y2[i] and not y3[i])
            c = sum(1 for i in ort if not y2[i] and y3[i])
            p = stats.binomtest(b, b + c, 0.5).pvalue if b + c else 1.0
            print(f"{a:16s} {mdl:8s} {len(ort):4d} "
                  f"{sum(y2.values())/len(ort):7.4f} {sum(y3.values())/len(ort):7.4f} "
                  f"{b:3d} {c:3d} {p:12.6f}")
            es[f"{a}|{mdl}"] = dict(n=len(ort), b=b, c=c, p_exact=float(p),
                                    recall_G2=sum(y2.values()) / len(ort),
                                    recall_G3=sum(y3.values()) / len(ort))
        print()
    rapor["eslesmis_model"] = es

    cikti = ROOT / "sonuclar" / "uretici_model_istatistik.json"
    cikti.write_text(json.dumps(rapor, ensure_ascii=False, indent=2, default=float),
                     encoding="utf-8")
    print(f"\nJSON ozet yazildi: {cikti}")


if __name__ == "__main__":
    main()
