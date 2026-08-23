"""Olcum orkestrasyonu.

Tasarim ilkesi: her sonuc alinir alinmaz JSONL'e yazilir. Cokme, kota bitisi
veya Ctrl+C hicbir zaman toplanmis veriyi kaybettirmez. Yeniden calistirma
kaldigi yerden devam eder.
"""
from __future__ import annotations

import json
import time
from datetime import datetime

from . import config
from .corpus import Metin, yukle
from .detectors import Sonuc, olustur


def _onbellek_oku() -> set[tuple[str, str]]:
    """Basariyla olculmus (metin_id, arac) ciftleri."""
    tamam: set[tuple[str, str]] = set()
    if not config.RESULTS_JSONL.exists():
        return tamam
    with config.RESULTS_JSONL.open(encoding="utf-8") as f:
        for satir in f:
            satir = satir.strip()
            if not satir:
                continue
            try:
                k = json.loads(satir)
            except json.JSONDecodeError:
                continue
            # Sadece BASARILI olcumler onbellege sayilir; hatalilar yeniden denenir
            if k.get("yz_olasilik") is not None:
                tamam.add((k["metin_id"], k["arac"]))
    return tamam


def _yaz(sonuc: Sonuc, metin: Metin) -> None:
    kayit = {
        "metin_id": sonuc.metin_id,
        "grup": metin.grup,
        "gercek_etiket": metin.gercek_etiket,
        "dil": metin.dil,
        "kelime": metin.kelime,
        "arac": sonuc.arac,
        "yz_olasilik": sonuc.yz_olasilik,
        "karar": sonuc.karar,
        "etiket": sonuc.etiket,
        "hata": sonuc.hata,
        "tarih": datetime.now().isoformat(timespec="seconds"),
        "ham_yanit": sonuc.ham_yanit,
    }
    with config.RESULTS_JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(kayit, ensure_ascii=False) + "\n")


def _sirala(m: Metin):
    """metin_id'yi sondaki sayiya gore sirala ('_10' < '_11' < '_100')."""
    from .corpus import _son_sayi
    return (m.grup, _son_sayi(m.metin_id))


def calistir(
    araclar: list[str] | None = None,
    gruplar: list[str] | None = None,
    diller: list[str] | None = None,
    limit: int | None = None,
    hucre_basi: int | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> None:
    korpus = yukle()
    metinler = sorted(korpus.values(), key=_sirala)
    if gruplar:
        metinler = [m for m in metinler if m.grup in gruplar]
    if diller:
        metinler = [m for m in metinler if m.dil in diller]

    if hucre_basi:
        # Kisitli kredi icin dengeli ornek: her (grup, dil) hucresinden N metin.
        # Duz --limit siralama geregi hepsini tek gruba harcardi.
        secili, sayac = [], {}
        for m in metinler:
            anahtar = (m.grup, m.dil)
            if sayac.get(anahtar, 0) < hucre_basi:
                secili.append(m)
                sayac[anahtar] = sayac.get(anahtar, 0) + 1
        metinler = secili

    if limit:
        metinler = metinler[:limit]

    adaptorler = olustur(araclar)
    onbellek = set() if force else _onbellek_oku()

    # Anahtari olmayan araclari basta bildir, sessizce 1800 hata uretme
    hazir = [a for a in adaptorler if a.hazir]
    eksik = [a for a in adaptorler if not a.hazir]
    if eksik:
        print("! Anahtari yok, atlanacak: " +
              ", ".join(f"{a.ad} ({a.anahtar_env})" for a in eksik))
    if not hazir:
        print("! Hicbir aracin anahtari yok. .env dosyasini doldurun.")
        return

    isler = [
        (m, a) for m in metinler for a in hazir
        if force or (m.metin_id, a.ad) not in onbellek
    ]
    atlanan = len(metinler) * len(hazir) - len(isler)
    print(f"Planlanan: {len(isler)} cagri | Onbellekten atlanan: {atlanan} "
          f"| Metin: {len(metinler)} | Arac: {len(hazir)}")

    if dry_run:
        print("(dry-run — istek gonderilmedi)")
        return

    basarili = hatali = 0
    for i, (m, a) in enumerate(isler, 1):
        sonuc = a.tara(m.metin_id, m.metin, m.dil)
        _yaz(sonuc, m)
        if sonuc.yz_olasilik is None:
            hatali += 1
            durum = f"HATA: {sonuc.hata[:70]}"
        else:
            basarili += 1
            durum = f"{sonuc.yz_olasilik:5.1f}% -> {sonuc.karar}"
        print(f"[{i:4d}/{len(isler)}] {m.metin_id:26s} {a.ad:14s} {durum}")
        time.sleep(config.RATE_LIMIT.get(a.ad, 1.0))

    print(f"\nBitti. Basarili: {basarili} | Hatali: {hatali}")
    print(f"Sonuclar: {config.RESULTS_JSONL}")


def kalibrasyon(araclar: list[str] | None = None) -> None:
    """Her araci 3 bilinen metinle sinar ve SKOR YONUNU dogrular.

    Bu adim atlanirsa 1800 olcum yanlis yonde toplanabilir.
    """
    korpus = yukle()

    def _ornek(grup: str, dil: str) -> Metin:
        return next(m for m in korpus.values() if m.grup == grup and m.dil == dil)

    testler = [
        ("G1_Insan (insan/TUR)", _ornek("G1_Insan", "TUR"), "DUSUK"),
        ("G1_Insan (insan/ENG)", _ornek("G1_Insan", "ENG"), "DUSUK"),
        ("G2_YZ   (YZ/TUR)", _ornek("G2_YZ", "TUR"), "YUKSEK"),
        ("G2_YZ   (YZ/ENG)", _ornek("G2_YZ", "ENG"), "YUKSEK"),
        ("G3      (insanlastirilmis/TUR)", _ornek("G3_Insanlastirilmis", "TUR"), "?"),
    ]

    for a in olustur(araclar):
        print("\n" + "=" * 72)
        print(f"ARAC: {a.ad}   (Turkce destegi: {a.turkce_destek})")
        print("=" * 72)
        if not a.hazir:
            print(f"  ATLANDI — {a.anahtar_env} tanimli degil")
            continue

        skorlar = {}
        ilk_ham = None
        for etiket, m, beklenti in testler:
            s = a.tara(m.metin_id, m.metin, m.dil)
            if s.hata:
                print(f"  {etiket:32s} HATA: {s.hata[:80]}")
            else:
                print(f"  {etiket:32s} {s.yz_olasilik:6.1f}%  "
                      f"(beklenti: {beklenti})  etiket={s.etiket}")
                skorlar[m.grup] = skorlar.get(m.grup, []) + [s.yz_olasilik]
                if ilk_ham is None:
                    ilk_ham = s.ham_yanit
            time.sleep(config.RATE_LIMIT.get(a.ad, 1.0))

        # HAM YANIT — alan adini ve araligi GOZLE dogrulamak icin.
        # Adaptordeki alan adi yanlissa hata burada gorunur.
        if ilk_ham:
            print("\n  --- ham yanit (alan adlarini dogrulayin) ---")
            dokum = json.dumps(ilk_ham, ensure_ascii=False, indent=2)
            if len(dokum) > 1500:
                dokum = dokum[:1500] + "\n  ... (kisaltildi)"
            print("  " + dokum.replace("\n", "\n  "))

        # YON KONTROLU
        g1 = skorlar.get("G1_Insan")
        g2 = skorlar.get("G2_YZ")
        if g1 and g2:
            o1, o2 = sum(g1) / len(g1), sum(g2) / len(g2)
            print(f"\n  G1 ort={o1:.1f}%  G2 ort={o2:.1f}%")
            if o2 > o1:
                print("  ✓ YON DOGRU (G2 > G1)")
            else:
                print("  ✗✗ YON TERS OLABILIR! G2 <= G1. "
                      "Adaptordeki skor alanini kontrol edin — "
                      "arac 'insan' skoru donduruyor olabilir.")
        else:
            print("\n  ! Yon kontrolu yapilamadi (yetersiz sonuc)")
