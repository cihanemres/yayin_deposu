#!/usr/bin/env python
"""Canli olcum ilerleme paneli.

Kullanim (KENDI terminalinde):
    python ilerleme.py                          # varsayilan: GPTZero, 3 grup (300)
    python ilerleme.py --arac Sapling
    python ilerleme.py --arac Copyleaks --grup G1_Insan G2_YZ

JSONL dosyasini saniyede bir okur, secilen aracin ilerlemesini yuzde cubuk,
grup dagilimi ve tahmini kalan sure (ETA) ile gosterir. Hedefe ulasinca durur.

NOT: Panel yalnizca OKUR, olcume dokunmaz. Ctrl+C paneli kapatir, olcum
arka planda devam eder.
"""
from __future__ import annotations

import argparse
import json
import sys
import time

from yzdetect import config

GRUPLAR = ["G1_Insan", "G2_YZ", "G3_Insanlastirilmis"]
KISA = {"G1_Insan": "G1", "G2_YZ": "G2", "G3_Insanlastirilmis": "G3"}
GRUP_BOYU = 100                   # her grupta 100 metin


def durum(arac: str, gruplar: set[str]) -> tuple[int, int, dict, list[float]]:
    """(basarili, hatali, grup_basina_basarili, skorlar).

    Ayni (metin_id) icin EN SON kayit gecerli — `--force` ile tekrar olculen
    metinlerde eski satir sayilmaz.
    """
    son: dict[str, dict] = {}
    if not config.RESULTS_JSONL.exists():
        return 0, 0, {}, []
    with config.RESULTS_JSONL.open(encoding="utf-8") as f:
        for satir in f:
            satir = satir.strip()
            if not satir:
                continue
            try:
                d = json.loads(satir)
            except json.JSONDecodeError:
                continue
            if d.get("arac") != arac or d.get("grup") not in gruplar:
                continue
            son[d["metin_id"]] = d
    basarili = sum(1 for d in son.values() if d.get("yz_olasilik") is not None)
    hatali = sum(1 for d in son.values() if d.get("yz_olasilik") is None)
    grup: dict[str, int] = {}
    skorlar: list[float] = []
    for d in son.values():
        if d.get("yz_olasilik") is not None:
            grup[d["grup"]] = grup.get(d["grup"], 0) + 1
            skorlar.append(d["yz_olasilik"])
    return basarili, hatali, grup, skorlar


def cubuk(oran: float, genislik: int = 32) -> str:
    dolu = int(oran * genislik)
    return "[" + "#" * dolu + "-" * (genislik - dolu) + "]"


def _sure(sn: float) -> str:
    sn = int(max(sn, 0))
    return f"{sn // 60:d}d{sn % 60:02d}s" if sn >= 60 else f"{sn:d}s"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--arac", default="GPTZero", help="Izlenecek arac (varsayilan: GPTZero)")
    p.add_argument("--grup", nargs="+", choices=GRUPLAR, default=GRUPLAR,
                   help="Izlenecek gruplar (varsayilan: uc grup birden)")
    a = p.parse_args()

    gruplar = set(a.grup)
    hedef = GRUP_BOYU * len(gruplar)
    etiket = " + ".join(KISA[g] for g in GRUPLAR if g in gruplar)

    print(f"{a.arac} olcum ilerlemesi — {etiket} (hedef: {hedef} metin)")
    print("Cikmak icin Ctrl+C\n")

    basladi = time.time()
    # ETA, panel acildiktan SONRA olculen metinlere gore hesaplanir; panel
    # yarida acilirsa onceden birikmis satirlar hizi carpitmasin diye.
    baslangic_tamam = None
    try:
        while True:
            basarili, hatali, grup, skorlar = durum(a.arac, gruplar)
            tamam = basarili + hatali
            if baslangic_tamam is None:
                baslangic_tamam = tamam
            oran = min(tamam / hedef, 1.0) if hedef else 0.0
            gecen = time.time() - basladi

            yeni = tamam - baslangic_tamam
            if yeni > 0 and gecen > 0:
                hiz = yeni / gecen                      # metin/saniye
                eta = _sure((hedef - tamam) / hiz) if hiz else "?"
                hiz_str = f"{hiz * 60:4.1f}/dk"
            else:
                eta, hiz_str = "  ?  ", "  —  "

            sayim = " ".join(f"{KISA[g]}={grup.get(g, 0):3d}"
                             for g in GRUPLAR if g in gruplar)
            ort = f"ort%{sum(skorlar) / len(skorlar):5.1f}" if skorlar else "ort  —  "

            satir = (f"\r{cubuk(oran)} %{oran * 100:5.1f}  {tamam:3d}/{hedef}  "
                     f"{sayim}  hata={hatali:2d}  {ort}  {hiz_str}  "
                     f"gecen={_sure(gecen)} kalan~{eta}   ")
            sys.stdout.write(satir)
            sys.stdout.flush()

            if tamam >= hedef:
                print("\n\n✓ TAMAMLANDI!")
                print(f"  Arac: {a.arac} | Basarili: {basarili} | Hatali: {hatali} "
                      f"| Sure: {_sure(gecen)}")
                print("  " + "  ".join(f"{KISA[g]}={grup.get(g, 0)}"
                                       for g in GRUPLAR if g in gruplar))
                if skorlar:
                    yz = sum(1 for s in skorlar if s > config.KARAR_ESIGI)
                    print(f"  Ortalama YZ olasiligi: %{sum(skorlar) / len(skorlar):.1f} "
                          f"| YZ kararı: {yz}/{len(skorlar)}")
                if hatali:
                    print(f"  ! {hatali} metin hatali — `python run.py --olc "
                          f"--arac {a.arac}` tekrar calistirinca yalnizca onlar denenir.")
                break
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n(izleme durduruldu — olcum arka planda devam ediyor olabilir)")


if __name__ == "__main__":
    main()
