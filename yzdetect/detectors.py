"""Arac adaptorleri.

Her adaptor tek bir sozu yerine getirir:
    tara(metin) -> Sonuc(yz_olasilik = 0..100, HER ZAMAN "YZ olma" yonunde)

KRITIK: Bazi araclar "insan/orijinal" skoru dondurur (Originality gibi).
Normalizasyon ve ters cevirme adaptorun ICINDE yapilir ve her biri
`run.py --kalibrasyon` ile gercek cagriyla dogrulanmalidir.
Yon hatasi tum bulgulari tersine cevirir.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import requests

from . import config


@dataclass
class Sonuc:
    arac: str
    metin_id: str
    yz_olasilik: float | None       # 0-100, "YZ olma olasiligi"
    etiket: str | None = None       # aracin kendi metinsel etiketi
    ham_yanit: dict[str, Any] = field(default_factory=dict)
    hata: str | None = None

    @property
    def karar(self) -> str | None:
        if self.yz_olasilik is None:
            return None
        return "YZ" if self.yz_olasilik > config.KARAR_ESIGI else "Insan"


class AracHatasi(Exception):
    pass


class Adaptor:
    ad: str = ""
    anahtar_env: str = ""
    # Aracin resmi olarak Turkce destekleyip desteklemedigi (yol haritasindan)
    turkce_destek: str = "bilinmiyor"

    # Aralik kontrolunde tolere edilen kayan nokta artigi. GPTZero tam
    # kesinlikte 1.0 yerine 1.0000000000000003 donduruyor -> x100 = 100.000...03.
    # Bu kadarlik tasma kirpilir; gercek olcek/yon hatasi (or. 0-1 yerine 0-100
    # sanmak) EPSILON'u asacagi icin hala hata olarak patlar.
    EPSILON = 1e-6

    def __init__(self):
        self.api_key = config.key(self.anahtar_env)

    @property
    def hazir(self) -> bool:
        return bool(self.api_key)

    def _istek(self, method: str, url: str, **kw) -> dict:
        """Ortak HTTP: retry + ustel geri cekilme (429/5xx)."""
        son_hata = None
        for deneme in range(config.MAX_RETRY):
            try:
                r = requests.request(method, url, timeout=config.TIMEOUT, **kw)
                if r.status_code in (429, 500, 502, 503, 504):
                    bekle = 2 ** deneme * 3
                    son_hata = f"HTTP {r.status_code}: {r.text[:200]}"
                    time.sleep(bekle)
                    continue
                if not r.ok:
                    raise AracHatasi(f"HTTP {r.status_code}: {r.text[:300]}")
                return r.json()
            except requests.RequestException as e:
                son_hata = str(e)
                time.sleep(2 ** deneme * 3)
        raise AracHatasi(f"{config.MAX_RETRY} denemede basarisiz: {son_hata}")

    def _cagir(self, metin: str, dil: str | None = None
               ) -> tuple[float, str | None, dict]:
        """Alt siniflar burayi doldurur: (yz_olasilik_0_100, etiket, ham).

        `dil` ('TUR'/'ENG') yalnizca dile gore model secen araclar (Originality)
        icin anlamlidir; digerleri gormezden gelir.
        """
        raise NotImplementedError

    def tara(self, metin_id: str, metin: str, dil: str | None = None) -> Sonuc:
        if not self.hazir:
            return Sonuc(self.ad, metin_id, None,
                         hata=f"{self.anahtar_env} tanimli degil")
        try:
            skor, etiket, ham = self._cagir(metin, dil)
            if -self.EPSILON <= skor <= 100.0 + self.EPSILON:
                skor = min(max(float(skor), 0.0), 100.0)   # kayan nokta artigini kirp
            else:
                raise AracHatasi(f"skor aralik disi: {skor}")
            return Sonuc(self.ad, metin_id, round(float(skor), 2), etiket, ham)
        except Exception as e:
            return Sonuc(self.ad, metin_id, None, hata=f"{type(e).__name__}: {e}")


# ---------------------------------------------------------------------------
# ADAPTORLER
# Endpoint/alan adlari yol haritasindaki dogrulanmis bilgiye gore ayarlanir.
# Her birinin yaninda: skorun yonu ve alan adi acikca belirtilir.
# ---------------------------------------------------------------------------

class Sapling(Adaptor):
    ad = "Sapling"
    anahtar_env = "SAPLING_API_KEY"
    turkce_destek = "YOK — dokuman: 'currently only available for English'"

    def _cagir(self, metin, dil=None):
        ham = self._istek(
            "POST", "https://api.sapling.ai/api/v1/aidetect",
            json={"key": self.api_key, "text": metin},
        )
        # 'score': 0-1, YZ yonunde. Ters cevirme YOK.
        # (Bloglardaki 0-100 rakamlari web arayuzune ait, API'ye degil.)
        return ham["score"] * 100, None, ham


class Originality(Adaptor):
    ad = "Originality_ai"
    anahtar_env = "ORIGINALITY_API_KEY"
    turkce_destek = "VAR — TR->multilang, EN->lite (saticinin 16.07.2026 onerisi)"

    # Dile gore model (aiModelVersion). Originality'nin resmi onerisi
    # (16.07.2026 e-postasi): TR -> Multilingual (2.0.0), EN -> Lite (1.0.2).
    # aiModelVersion major surume eslenir; her iki deger de canli API ile
    # dogrulandi (v1/scan/ai, score.ai alani).
    MODEL_TR = "2"   # Multilingual 2.0.0
    MODEL_EN = "1"   # Lite 1.0.2

    def _cagir(self, metin, dil=None):
        # dil bilinmiyorsa multilingual'e dus (Turkce'yi Ingilizce/Lite
        # modeline dusurmekten daha guvenli varsayilan).
        model = self.MODEL_EN if dil == "ENG" else self.MODEL_TR
        ham = self._istek(
            "POST", "https://api.originality.ai/api/v1/scan/ai",
            headers={"X-OAI-API-KEY": self.api_key},
            json={
                "content": metin,
                "title": "yzdetect",       # API zorunlu alan
                "aiModelVersion": model,   # 1=Lite(EN), 2=Multilingual(TR)
            },
        )
        # score.ai : 0-1, YZ yonunde. Ters cevirme YOK. (score.original = insan)
        # ! ANLAM: bu deger metnin YZ olma olasiligi; %50 uzeri -> "YZ".
        skor = ham["score"]["ai"] * 100
        # Kullanilan modeli etikette sakla (JSONL izlenebilirligi)
        return skor, f"model={model}", ham


class GPTZero(Adaptor):
    ad = "GPTZero"
    anahtar_env = "GPTZERO_API_KEY"
    turkce_destek = ("BEYAN YOK, AMA COKDILLI — 05.08.2026 olcumunde API "
                     "version='2026-06-10-multilingual' dondu ve Turkce metinde "
                     "language='tr' raporladi (dokuman hala yalnizca FR/ES diyor)")

    def _cagir(self, metin, dil=None):
        ham = self._istek(
            "POST", "https://api.gptzero.me/v2/predict/text",
            headers={"x-api-key": self.api_key, "Content-Type": "application/json"},
            # multilingual=True GONDERMIYORUZ: desteklenmeyen dilde bu bayrak
            # hata vermek yerine metni Ingilizce modeline yonlendiriyor.
            # Varsayilan davranisi kayit altina almak daha durust.
            json={"document": metin},
        )
        d = ham["documents"][0]
        # class_probabilities.ai : 0-1, YZ yonunde.
        # ! completely_generated_prob ARTIK KULLANIM DISI (deprecated).
        skor = d["class_probabilities"]["ai"] * 100
        etiket = d.get("document_classification")
        return skor, etiket, ham


class Copyleaks(Adaptor):
    ad = "Copyleaks"
    anahtar_env = "COPYLEAKS_API_KEY"
    turkce_destek = "VAR — desteklenen 30 dil listesinde 'tr' acikca var"

    MIN_KARAKTER = 255      # sert sinir; istemci tarafinda engelle
    MAX_KARAKTER = 100_000

    def __init__(self, sandbox: bool = False):
        super().__init__()
        self.email = config.key("COPYLEAKS_EMAIL")
        self.sandbox = sandbox   # sandbox=True ucretsiz, kredi harcamaz
        self._token = None

    @property
    def hazir(self) -> bool:
        return bool(self.api_key and self.email)

    def _login(self) -> str:
        # Token 48 saat gecerli; giris 12 istek/15dk ile sinirli -> onbellekle
        if self._token:
            return self._token
        ham = self._istek(
            "POST", "https://id.copyleaks.com/v3/account/login/api",
            json={"email": self.email, "key": self.api_key},
        )
        self._token = ham["access_token"]
        return self._token

    def _cagir(self, metin, dil=None):
        import uuid
        if len(metin) < self.MIN_KARAKTER:
            raise AracHatasi(
                f"metin {len(metin)} karakter, Copyleaks minimumu {self.MIN_KARAKTER}"
            )
        tok = self._login()
        tarama_id = uuid.uuid4().hex
        ham = self._istek(
            "POST",
            f"https://api.copyleaks.com/v2/writer-detector/{tarama_id}/check",
            headers={"Authorization": f"Bearer {tok}"},
            json={"text": metin, "sandbox": self.sandbox},
        )
        # summary.ai : 0-1, YZ olarak siniflanan metin orani. DOGRU ALAN.
        #
        # ! TERS CEVIRME TUZAGI: results[].probability alanini KULLANMAYIN.
        #   O, atanan 'classification'a olan guveni ifade eder.
        #   classification=1 (insan) + probability=0.95  ->  %95 guvenle INSAN,
        #   yani YZ olasiligi ~0.05. probability'yi YZ skoru sanmak, insan
        #   siniflanan her bolumde skoru SESSIZCE ters cevirir.
        #   Enum: 1 = insan, 2 = YZ.
        skor = ham["summary"]["ai"] * 100
        return skor, None, ham


class ZeroGPT(Adaptor):
    """zerogpt.COM (zerogpt.NET degil).

    Aramada cikan cogu blog/GitHub sonucu farkli bir sirketi (zerogpt.net)
    belgeliyor; o farkli bir sema kullaniyor (is_human_written/is_gpt_generated)
    ve 'Authorization: Bearer' istiyor. Burada kullanilan 'ApiKey' basligi
    zerogpt.com icin ampirik olarak dogrulandi.
    """
    ad = "ZeroGPT"
    anahtar_env = "ZEROGPT_API_KEY"
    turkce_destek = "SUPHELI — yalnizca genel pazarlama iddiasi; Turkce hicbir yerde adiyla gecmiyor"

    def _cagir(self, metin, dil=None):
        ham = self._istek(
            "POST", "https://api.zerogpt.com/api/detect/detectText",
            headers={"ApiKey": self.api_key, "Content-Type": "application/json"},
            json={"input_text": metin},
        )
        # ! ZeroGPT hatalari HTTP 200 ile bildiriyor:
        #   {"success": false, "code": 403, "message": "Not enough credits", "data": null}
        #   Bu yuzden _istek()'in HTTP durum kontrolu bunlari yakalayamaz.
        #   Govdeyi acikca kontrol etmezsek 'data' None kalir ve anlamsiz bir
        #   TypeError olarak patlar.
        if ham.get("success") is False or ham.get("data") is None:
            raise AracHatasi(
                f"ZeroGPT reddetti (HTTP 200 govdesinde): "
                f"code={ham.get('code')} message={ham.get('message')!r}"
            )
        d = ham["data"]
        if "fakePercentage" not in d:
            raise AracHatasi(f"fakePercentage alani yok. Donen alanlar: {list(d)}")
        # fakePercentage: spec "The Percentage of AI in your text." YZ yonunde.
        # Aralik 0-100 varsayiliyor ama ampirik dogrulanmadi -> kalibrasyonda bakin.
        skor = float(d["fakePercentage"])
        return skor, d.get("feedback"), ham


class Pangram(Adaptor):
    """DIKKAT: Pangram API'si ASENKRON — iki cagri gerekir.

    Eski senkron endpoint (text.api.pangram.com) ve eski alan adlari
    (ai_likelihood, fraction_ai_content) KULLANIM DISI. Bazi bloglar ve
    pangram.readthedocs.io hala eskisini gosteriyor.
    """
    ad = "Pangram"
    anahtar_env = "PANGRAM_API_KEY"
    turkce_destek = "VAR — 24 dil listesinde Turkce adiyla geciyor (%99,90 iddia)"

    TABAN = "https://text.external-api.pangram.com"
    POLL_ARALIK = 1.5
    POLL_MAX = 40

    def _cagir(self, metin, dil=None):
        basliklar = {"x-api-key": self.api_key, "Content-Type": "application/json"}
        gorev = self._istek(
            "POST", f"{self.TABAN}/task",
            headers=basliklar,
            json={"text": metin, "public_dashboard_link": False},
        )
        gorev_id = gorev.get("task_id") or gorev.get("id")
        if not gorev_id:
            raise AracHatasi(f"task_id yok: {gorev}")

        for _ in range(self.POLL_MAX):
            ham = self._istek("GET", f"{self.TABAN}/task/{gorev_id}", headers=basliklar)
            asama = str(ham.get("stage") or ham.get("status") or "")
            if asama.endswith("SUCCESS"):
                # fraction_ai: 0-1, YZ yonunde. Ters cevirme YOK.
                skor = float(ham["fraction_ai"]) * 100
                return skor, ham.get("prediction_short"), ham
            if asama.endswith("FAILED"):
                raise AracHatasi(f"Pangram gorevi basarisiz: {ham}")
            time.sleep(self.POLL_ARALIK)
        raise AracHatasi(f"Pangram gorevi zaman asimi ({gorev_id})")


ARACLAR: dict[str, type[Adaptor]] = {
    a.ad: a for a in (Sapling, Originality, GPTZero, Copyleaks, ZeroGPT, Pangram)
}


def olustur(adlar: list[str] | None = None) -> list[Adaptor]:
    secili = adlar or list(ARACLAR)
    bilinmeyen = set(secili) - set(ARACLAR)
    if bilinmeyen:
        raise KeyError(f"Bilinmeyen arac: {bilinmeyen}. Gecerli: {list(ARACLAR)}")
    return [ARACLAR[a]() for a in secili]
