"""Ham API yanitlarindan girdi metni iceren alanlari cikarir.

Girdi : veri/ham_api_yanitlari.jsonl
Cikti : veri/ham_api_yanitlari_temiz.jsonl

Her kaydin "ham_yanit" alaninda, ic ice butun sozluk ve listelerde
SILINECEK kumesindeki anahtarlar silinir; diger alanlar korunur.
"""
import json
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
GIRDI = KOK / "veri" / "ham_api_yanitlari.jsonl"
CIKTI = KOK / "veri" / "ham_api_yanitlari_temiz.jsonl"

SILINECEK = {
    "content", "blocks", "public_link", "text", "inputText", "sentences",
    "sentence_scores", "tokens", "token_probs", "windows", "input_text", "h",
    "scannedDocument",
}


def temizle(o):
    if isinstance(o, dict):
        return {k: temizle(v) for k, v in o.items() if k not in SILINECEK}
    if isinstance(o, list):
        return [temizle(v) for v in o]
    return o


def main():
    n = 0
    with open(GIRDI, encoding="utf-8") as fi, \
            open(CIKTI, "w", encoding="utf-8", newline="\n") as fo:
        for satir in fi:
            kayit = json.loads(satir)
            kayit["ham_yanit"] = temizle(kayit["ham_yanit"])
            fo.write(json.dumps(kayit, ensure_ascii=False) + "\n")
            n += 1
    print(f"{n} kayit yazildi: {CIKTI}")


if __name__ == "__main__":
    main()
