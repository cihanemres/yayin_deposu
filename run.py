#!/usr/bin/env python
"""YZ Tespit Korpusu — API ile otomatik olcum.

Tipik kullanim sirasi:

    python run.py --dogrula                    # anahtarlar / korpus saglik kontrolu
    python run.py --kalibrasyon                # ZORUNLU: skor yonunu dogrula
    python run.py --olc --arac Sapling --limit 5   # kucuk deneme
    python run.py --olc                        # tam olcum (kaldigi yerden devam eder)
    python run.py --yaz                        # JSONL -> Excel
"""
from __future__ import annotations

import argparse

from yzdetect import config, runner, writer
from yzdetect.corpus import yukle
from yzdetect.detectors import ARACLAR, olustur

GRUPLAR = ["G1_Insan", "G2_YZ", "G3_Insanlastirilmis"]


def dogrula() -> None:
    print("=" * 60)
    print("ANAHTAR DURUMU")
    print("=" * 60)
    for a in olustur():
        durum = "✓ hazir" if a.hazir else f"✗ eksik ({a.anahtar_env})"
        print(f"  {a.ad:16s} {durum:28s} Turkce: {a.turkce_destek}")

    print()
    print("=" * 60)
    print("KORPUS")
    print("=" * 60)
    korpus = yukle()
    print(f"  Toplam metin: {len(korpus)}")
    for g in GRUPLAR:
        alt = [m for m in korpus.values() if m.grup == g]
        kel = [m.kelime for m in alt]
        print(f"  {g:22s} n={len(alt):3d} | kelime ort={sum(kel)/len(kel):5.1f} "
              f"min={min(kel):3d} max={max(kel):3d}")

    hazir = sum(1 for a in olustur() if a.hazir)
    print()
    print(f"  Planlanan toplam cagri: {len(korpus)} x {hazir} arac = "
          f"{len(korpus) * hazir}")
    print(f"  Sonuc dosyasi: {config.RESULTS_JSONL}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dogrula", action="store_true",
                   help="Anahtar ve korpus saglik kontrolu")
    p.add_argument("--kalibrasyon", action="store_true",
                   help="Her araci 5 bilinen metinle sinar, SKOR YONUNU dogrular")
    p.add_argument("--olc", action="store_true", help="Olcumu calistir")
    p.add_argument("--yaz", action="store_true", help="JSONL sonuclarini Excel'e yaz")
    p.add_argument("--arac", nargs="+", choices=list(ARACLAR),
                   help="Sadece bu araclar")
    p.add_argument("--grup", nargs="+", choices=GRUPLAR, help="Sadece bu gruplar")
    p.add_argument("--dil", nargs="+", choices=["TUR", "ENG"], help="Sadece bu diller")
    p.add_argument("--limit", type=int, help="Ilk N metin (deneme icin)")
    p.add_argument("--hucre-basi", type=int, metavar="N",
                   help="Her (grup,dil) hucresinden N metin — kisitli kredi icin "
                        "dengeli ornek. 3 grup x 2 dil x N.")
    p.add_argument("--force", action="store_true",
                   help="Onbellegi yoksay, hepsini yeniden olc")
    p.add_argument("--dry-run", action="store_true",
                   help="Istek gonderme, sadece plani goster")
    p.add_argument("--pangram-ekleme", action="store_true",
                   help="--yaz sirasinda Pangram satirlarini ekleme")
    a = p.parse_args()

    if a.dogrula:
        dogrula()
    elif a.kalibrasyon:
        runner.kalibrasyon(a.arac)
    elif a.olc:
        runner.calistir(araclar=a.arac, gruplar=a.grup, diller=a.dil,
                        limit=a.limit, hucre_basi=a.hucre_basi,
                        force=a.force, dry_run=a.dry_run)
    elif a.yaz:
        writer.yaz(pangram_ekle=not a.pangram_ekleme, gruplar=a.grup)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
