"""API anahtarlari ve genel ayarlar.

Anahtarlar .env dosyasindan okunur. .env dosyasini ASLA paylasmayin/commit etmeyin.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
XLSX = ROOT / "YZ_Tespit_Korpus_v9.xlsx"
CACHE = ROOT / "sonuclar"
CACHE.mkdir(exist_ok=True)
RESULTS_JSONL = CACHE / "olcum_sonuclari.jsonl"


def _load_dotenv():
    """Bagimlilik eklemeden basit .env okuyucu."""
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv()


def key(name: str) -> str | None:
    v = os.environ.get(name)
    return v if v else None


# Karar esigi: Yontem_Notu'na gore YZ olasiligi > %50 -> "YZ"
KARAR_ESIGI = 50.0

# Istekler arasi bekleme (saniye) - arac bazinda
RATE_LIMIT = {
    "GPTZero": 1.0,
    "ZeroGPT": 2.0,
    "Copyleaks": 1.5,
    "Sapling": 1.0,
    "Originality_ai": 1.5,
    "Pangram": 1.0,
}

TIMEOUT = 90
MAX_RETRY = 4
