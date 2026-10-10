"""Şekil 1 ve Şekil 2'yi tek kaynaktan üretir (BULGULAR bölümü).

Girdi : sonuclar/yontem_istatistik.json   (analiz_yontem.py çıktısı)
Çıktı : sonuclar/sekil_1_fpr.png|.pdf     — Şekil 1
        sonuclar/sekil_2_g2_g3.png|.pdf   — Şekil 2

Şekil 1 : Araç x dil yanlış pozitif oranı (FPR), %95 Wilson güven aralığı
          hata çubuklarıyla. Veri: rapor["ki_kare_dil"][araç] (G1 metinleri,
          her araç için TUR ve ENG alt örneklemi).
Şekil 2 : G2 (saf YZ) -> G3 (insanlaştırılmış) duyarlılık düşüşü; eşleşmiş
          çiftler. Veri: rapor["mcnemar"]["<araç>|TUM"].
          Copyleaks, G3 ölçümleri v9 öncesi (bayat) olduğu için şekilden
          çıkarılır; şekil altına not düşülür.

Çalıştırma:  python sekil_uret.py
Bağımlılık:  matplotlib >= 3.8
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
KAYNAK = ROOT / "sonuclar" / "yontem_istatistik.json"
CIKTI = ROOT / "sonuclar"
ARACLAR = ["GPTZero", "ZeroGPT", "Copyleaks", "Sapling", "Originality_ai", "Pangram"]
ETIKET = {"Originality_ai": "Originality.ai"}
# G3 ölçümleri v9 öncesi metinlere ait: G2 -> G3 karşılaştırması geçersiz
GECERSIZ_G2G3 = {"Copyleaks"}
DPI = 300

plt.rcParams.update({"font.size": 9, "axes.grid": True, "grid.alpha": .3,
                     "grid.linestyle": ":", "axes.axisbelow": True})


def ad(a: str) -> str:
    return ETIKET.get(a, a)


def kaydet(fig, isim: str) -> None:
    for uzanti in ("png", "pdf"):
        yol = CIKTI / f"{isim}.{uzanti}"
        fig.savefig(yol, dpi=DPI, bbox_inches="tight")
        print(f"  yazıldı: {yol}")
    plt.close(fig)


def sekil_1(rapor: dict) -> None:
    ki = rapor["ki_kare_dil"]
    x = range(len(ARACLAR))
    gen = 0.38
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    for kaydir, dil, renk in ((-gen / 2, "TUR", "#c0392b"), (gen / 2, "ENG", "#2c6fbb")):
        oran = [ki[a][f"FPR_{dil}"] for a in ARACLAR]
        ga = [ki[a][f"FPR_{dil}_GA95"] for a in ARACLAR]
        alt = [max(0.0, o - g[0]) for o, g in zip(oran, ga)]
        ust = [max(0.0, g[1] - o) for o, g in zip(oran, ga)]
        ax.bar([i + kaydir for i in x], oran, gen, label=dil, color=renk,
               edgecolor="black", linewidth=.5)
        ax.errorbar([i + kaydir for i in x], oran, yerr=[alt, ust], fmt="none",
                    ecolor="black", elinewidth=.9, capsize=3)
    ax.set_xticks(list(x))
    ax.set_xticklabels([ad(a) for a in ARACLAR], rotation=12, ha="right")
    ax.set_ylabel("Yanlış pozitif oranı (FPR)")
    ax.set_ylim(0, 1.12)
    ax.set_title("Şekil 1. İnsan metinlerinde (G1) araç × dil yanlış pozitif oranı\n"
                 "Hata çubukları: %95 Wilson güven aralığı  ·  n = 50 TUR / 50 ENG "
                 "(Copyleaks: 30 / 16)", loc="left", fontsize=9.5)
    ax.legend(title="Dil", frameon=False, ncol=2, loc="upper center")
    ci = ARACLAR.index("Copyleaks")
    ax.annotate("eksik veri", xy=(ci, .43), ha="center", fontsize=7.5,
                color="#555555", style="italic")
    kaydet(fig, "sekil_1_fpr")


def sekil_2(rapor: dict) -> None:
    mc = rapor["mcnemar"]
    araclar = [a for a in ARACLAR if a not in GECERSIZ_G2G3]
    fig, ax = plt.subplots(figsize=(8.6, 4.0))
    for i, a in enumerate(araclar):
        v = mc.get(f"{a}|TUM")
        if not v:
            continue
        r2, r3 = v["recall_G2"], v["recall_G3"]
        renk = "#c0392b" if r3 < r2 else "#2c6fbb"
        ax.plot([i - .16, i + .16], [r2, r3], "-", color=renk, linewidth=1.6, zorder=2)
        ax.plot(i - .16, r2, "o", color="#333333", markersize=6, zorder=3)
        ax.plot(i + .16, r3, "s", color=renk, markersize=6, zorder=3)
        alt, ust = v["fark_GA95"]
        not_ = (f"Δ = {r2 - r3:+.2f}\n"
                f"[{alt:+.2f}, {ust:+.2f}]\n"
                f"b = {v['b']}, c = {v['c']}\n"
                f"n = {v['n']}")
        # ust ust binmemesi icin tek/cift sutunlarda kaydirmali yerlesim
        y0 = min(r2, r3) - (.05 if i % 2 == 0 else .17)
        ax.annotate(not_, xy=(i, y0), ha="center", va="top", fontsize=6.6)
    ax.plot([], [], "o", color="#333333", label="G2 (saf YZ)")
    ax.plot([], [], "s", color="#c0392b", label="G3 (insanlaştırılmış)")
    ax.set_xticks(range(len(araclar)))
    ax.set_xticklabels([ad(a) for a in araclar], rotation=12, ha="right")
    ax.set_ylabel("Duyarlılık (recall)")
    ax.set_ylim(.35, 1.06)
    ax.set_title("Şekil 2. G2 → G3 duyarlılık düşüşü (eşleşmiş çiftler, tüm korpus)\n"
                 "Δ: eşleşmiş oran farkı, köşeli parantez: %95 GA; b/c: uyumsuz hücreler",
                 loc="left", fontsize=9.5)
    ax.legend(frameon=False, ncol=2, loc="lower left")
    fig.text(0.01, -0.06, "Not. Copyleaks G3 ölçümleri raporlanmamıştır.",
             ha="left", va="top", fontsize=8, style="italic")
    kaydet(fig, "sekil_2_g2_g3")


def main() -> None:
    rapor = json.loads(KAYNAK.read_text(encoding="utf-8"))
    print(f"Kaynak: {KAYNAK}")
    sekil_1(rapor)
    sekil_2(rapor)


if __name__ == "__main__":
    main()
