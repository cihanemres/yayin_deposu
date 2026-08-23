"""Olcum sonuclarindan metrik hesaplama.

Yontem_Notu'ndaki metrikler: Duyarlilik, Ozgulluk, FPR, FNR, Dogruluk, F1, AUC.
Dil (TUR/ENG) karsilastirmasi G1 uzerinden.

SKOR SECIMI — arac basina, bilerek:
  Pangram   : windows[].ai_assistance_score (DERECELI, agirlikli ortalama)
              fraction_ai belge seviyesinde ikili (0/1) — AUC icin iseyaramaz.
  Copyleaks : summary.ai (IKILI). results[].probability'den dereceli skor
              TURETILMEDI: 20 kayitta classification=1 iken probability<0.5
              cikiyor; alan "atanan sinifa guven" ise bu imkansiz. Anlami
              belirsiz -> kullanilmadi. Copyleaks icin AUC RAPORLANAMAZ.
  ZeroGPT   : fakePercentage (dereceli)
  Sapling   : score (dereceli)
"""
from __future__ import annotations

import json
from collections import defaultdict

from yzdetect import config

ESIK = config.KARAR_ESIGI  # 50.0


def _pangram_dereceli(ham: dict) -> float | None:
    """windows[].ai_assistance_score -> kelime sayisiyla agirlikli ortalama, %0-100.

    Metinlerin 260/300'unde tek pencere var; 40'inda iki pencere.
    """
    w = ham.get("windows") or []
    if not w:
        return None
    toplam_agirlik = sum(x.get("word_count") or 1 for x in w)
    if not toplam_agirlik:
        return None
    s = sum((x.get("ai_assistance_score") or 0) * (x.get("word_count") or 1) for x in w)
    return 100.0 * s / toplam_agirlik


def yukle_sonuclar() -> list[dict]:
    kayitlar = []
    for satir in config.RESULTS_JSONL.read_text(encoding="utf-8").splitlines():
        satir = satir.strip()
        if not satir:
            continue
        k = json.loads(satir)
        if k.get("yz_olasilik") is None:
            continue
        # Dereceli skor (AUC icin). Yoksa None -> AUC hesaplanmaz.
        if k["arac"] == "Pangram":
            k["dereceli"] = _pangram_dereceli(k["ham_yanit"])
        elif k["arac"] == "Copyleaks":
            k["dereceli"] = None      # bilerek: yukaridaki nota bakin
        else:
            k["dereceli"] = k["yz_olasilik"]
        kayitlar.append(k)
    # Ayni (metin_id, arac) icin en son kayit gecerli
    son = {}
    for k in kayitlar:
        son[(k["metin_id"], k["arac"])] = k
    return list(son.values())


def auc(pozitif: list[float], negatif: list[float]) -> float | None:
    """Mann-Whitney U ile AUC. Beraberlikler 0.5 sayilir."""
    if not pozitif or not negatif:
        return None
    kazanan = 0.0
    for p in pozitif:
        for n in negatif:
            if p > n:
                kazanan += 1
            elif p == n:
                kazanan += 0.5
    return kazanan / (len(pozitif) * len(negatif))


def metrikler(kayitlar: list[dict]) -> dict:
    """gercek_etiket'e gore TP/FP/TN/FN ve turev metrikler."""
    tp = sum(1 for k in kayitlar if k["gercek_etiket"] == "YZ" and k["yz_olasilik"] > ESIK)
    fn = sum(1 for k in kayitlar if k["gercek_etiket"] == "YZ" and k["yz_olasilik"] <= ESIK)
    fp = sum(1 for k in kayitlar if k["gercek_etiket"] == "Insan" and k["yz_olasilik"] > ESIK)
    tn = sum(1 for k in kayitlar if k["gercek_etiket"] == "Insan" and k["yz_olasilik"] <= ESIK)

    def oran(a, b):
        return a / b if b else None

    duyarlilik = oran(tp, tp + fn)      # recall / TPR
    ozgulluk = oran(tn, tn + fp)        # TNR
    kesinlik = oran(tp, tp + fp)        # precision
    f1 = (2 * kesinlik * duyarlilik / (kesinlik + duyarlilik)
          if kesinlik and duyarlilik and (kesinlik + duyarlilik) else None)

    d = [k["dereceli"] for k in kayitlar if k["gercek_etiket"] == "YZ" and k["dereceli"] is not None]
    i = [k["dereceli"] for k in kayitlar if k["gercek_etiket"] == "Insan" and k["dereceli"] is not None]

    return {
        "n": len(kayitlar), "TP": tp, "FP": fp, "TN": tn, "FN": fn,
        "duyarlilik": duyarlilik, "ozgulluk": ozgulluk,
        "FPR": oran(fp, fp + tn), "FNR": oran(fn, tp + fn),
        "dogruluk": oran(tp + tn, len(kayitlar)),
        "kesinlik": kesinlik, "F1": f1,
        "AUC": auc(d, i) if (d and i) else None,
    }


def _y(x, bicim="{:.3f}"):
    return bicim.format(x) if x is not None else "  —  "


def rapor() -> None:
    kayitlar = yukle_sonuclar()
    araclar = sorted({k["arac"] for k in kayitlar})

    print("=" * 78)
    print("METRIKLER — tum korpus (G1 insan + G2/G3 YZ)")
    print("=" * 78)
    print(f"{'arac':11s} {'n':>4s} {'Duyar':>7s} {'Ozgul':>7s} {'FPR':>7s} {'FNR':>7s} "
          f"{'Dogru':>7s} {'F1':>7s} {'AUC':>7s}")
    print("-" * 78)
    for a in araclar:
        m = metrikler([k for k in kayitlar if k["arac"] == a])
        print(f"{a:11s} {m['n']:4d} {_y(m['duyarlilik'])} {_y(m['ozgulluk'])} "
              f"{_y(m['FPR'])} {_y(m['FNR'])} {_y(m['dogruluk'])} {_y(m['F1'])} {_y(m['AUC'])}")

    print()
    print("=" * 78)
    print("DIL KARSILASTIRMASI")
    print("=" * 78)
    print(f"{'arac':11s} {'dil':4s} {'n':>4s} {'Duyar':>7s} {'Ozgul':>7s} {'FPR':>7s} "
          f"{'Dogru':>7s} {'AUC':>7s}")
    print("-" * 78)
    for a in araclar:
        for dil in ["TUR", "ENG"]:
            alt = [k for k in kayitlar if k["arac"] == a and k["dil"] == dil]
            if not alt:
                continue
            m = metrikler(alt)
            print(f"{a:11s} {dil:4s} {m['n']:4d} {_y(m['duyarlilik'])} {_y(m['ozgulluk'])} "
                  f"{_y(m['FPR'])} {_y(m['dogruluk'])} {_y(m['AUC'])}")

    print()
    print("=" * 78)
    print("HUMANIZER ETKISI — G2 (ham YZ) -> G3 (humanize), YZ yakalama orani")
    print("=" * 78)
    print(f"{'arac':11s} {'dil':4s} {'G2 yakalama':>12s} {'G3 yakalama':>12s} {'KACIS':>8s}")
    print("-" * 78)
    for a in araclar:
        for dil in ["TUR", "ENG"]:
            g2 = [k for k in kayitlar if k["arac"] == a and k["dil"] == dil and k["grup"] == "G2_YZ"]
            g3 = [k for k in kayitlar if k["arac"] == a and k["dil"] == dil
                  and k["grup"] == "G3_Insanlastirilmis"]
            if not g2 or not g3:
                continue
            y2 = sum(1 for k in g2 if k["yz_olasilik"] > ESIK) / len(g2)
            y3 = sum(1 for k in g3 if k["yz_olasilik"] > ESIK) / len(g3)
            print(f"{a:11s} {dil:4s} {y2:11.1%} {y3:11.1%} {y2-y3:+8.1%}")

    print()
    print("NOT: Copyleaks AUC raporlanamaz — summary.ai ikili (0/1), "
          "probability alaninin\n     anlami dogrulanamadi (bkz. metrikler.py ust aciklamasi).")


if __name__ == "__main__":
    rapor()
