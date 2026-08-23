"""Adaptor testleri — sahte HTTP yanitlariyla, gercek API cagrisi YOK.

Amac: alan adlarinin ve skor yonunun dogru okundugunu kanitlamak.
Bu testler, aslinda yasanmis bir hataya karsi savunma: ilk yazilan adaptorlerin
UCUNDE birden alan adi yanlisti (Pangram ai_likelihood, GPTZero
completely_generated_prob, Originality score.ai). Dokumanlar eskiyor.

Calistirma:  pip install responses pytest && pytest test_detectors.py -v
"""
import json
import uuid

import pytest
import responses

from yzdetect.detectors import Copyleaks, GPTZero, Originality, Pangram, Sapling, ZeroGPT


@responses.activate
def test_pangram_async_akis_ve_fraction_ai():
    """Pangram ASENKRON: POST /task -> poll GET /task/{id}. Alan: fraction_ai."""
    responses.add(responses.POST, "https://text.external-api.pangram.com/task",
                  json={"task_id": "t1"}, status=200)
    responses.add(responses.GET, "https://text.external-api.pangram.com/task/t1",
                  json={"stage": "STAGE_PENDING"}, status=200)
    responses.add(responses.GET, "https://text.external-api.pangram.com/task/t1",
                  json={"stage": "STAGE_SUCCESS", "fraction_ai": 0.93,
                        "fraction_human": 0.07, "prediction_short": "AI"}, status=200)

    p = Pangram()
    p.api_key = "sahte"
    p.POLL_ARALIK = 0
    s = p.tara("X", "metin")

    assert s.yz_olasilik == 93.0
    assert s.karar == "YZ"
    assert s.etiket == "AI"


@responses.activate
def test_pangram_basarisiz_gorev_hata_verir():
    responses.add(responses.POST, "https://text.external-api.pangram.com/task",
                  json={"task_id": "t2"}, status=200)
    responses.add(responses.GET, "https://text.external-api.pangram.com/task/t2",
                  json={"stage": "STAGE_FAILED"}, status=200)

    p = Pangram()
    p.api_key = "sahte"
    p.POLL_ARALIK = 0
    s = p.tara("X", "metin")

    assert s.yz_olasilik is None
    assert s.hata is not None


def test_copyleaks_255_karakter_tabani_istemcide_engellenir():
    c = Copyleaks()
    c.api_key, c.email = "k", "e@x.com"
    s = c.tara("X", "kisa metin")
    assert s.yz_olasilik is None
    assert "minimum" in s.hata


@responses.activate
def test_copyleaks_summary_ai_kullanir_probability_tuzagina_dusmez(monkeypatch):
    """results[].probability atanan SINIFA olan guven — YZ olasiligi degil.

    classification=1 (insan) + probability=0.95 -> %95 guvenle INSAN.
    Bu alani YZ skoru sanmak, insan siniflanan her bolumde skoru ters cevirir.
    """
    responses.add(responses.POST, "https://id.copyleaks.com/v3/account/login/api",
                  json={"access_token": "tok"}, status=200)
    responses.add(responses.POST, "https://api.copyleaks.com/v2/writer-detector/x/check",
                  json={"summary": {"ai": 0.88, "human": 0.12},
                        "results": [{"classification": 1, "probability": 0.95}]},
                  status=200)
    monkeypatch.setattr(uuid, "uuid4", lambda: type("u", (), {"hex": "x"})())

    c = Copyleaks()
    c.api_key, c.email = "k", "e@x.com"
    s = c.tara("X", "a" * 300)

    assert s.yz_olasilik == 88.0          # summary.ai
    assert s.yz_olasilik != 95.0          # probability tuzagi
    assert s.yz_olasilik != 5.0           # ters cevrilmis probability


@responses.activate
def test_copyleaks_token_onbelleklenir():
    """Giris 12 istek/15dk ile sinirli — her taramada login edilmemeli."""
    responses.add(responses.POST, "https://id.copyleaks.com/v3/account/login/api",
                  json={"access_token": "tok"}, status=200)
    c = Copyleaks()
    c.api_key, c.email = "k", "e@x.com"
    assert c._login() == "tok"
    assert c._login() == "tok"
    girisler = [r for r in responses.calls if "login" in r.request.url]
    assert len(girisler) == 1


@responses.activate
def test_gptzero_class_probabilities_kullanir_deprecated_alani_okumaz():
    responses.add(responses.POST, "https://api.gptzero.me/v2/predict/text",
                  json={"documents": [{
                      "class_probabilities": {"ai": 0.77, "human": 0.2, "mixed": 0.03},
                      "completely_generated_prob": 0.11,   # KULLANIM DISI
                      "document_classification": "AI_ONLY"}]}, status=200)

    g = GPTZero()
    g.api_key = "k"
    s = g.tara("X", "metin")

    assert s.yz_olasilik == 77.0
    assert s.yz_olasilik != 11.0          # deprecated alan okunmamali


@responses.activate
def test_gptzero_multilingual_bayragi_gonderilmez():
    """multilingual=true, desteklenmeyen dilde hata vermek yerine metni
    Ingilizce modeline yonlendiriyor. Varsayilani kayit altina almak daha durust."""
    responses.add(responses.POST, "https://api.gptzero.me/v2/predict/text",
                  json={"documents": [{"class_probabilities": {"ai": 0.5},
                                       "document_classification": "MIXED"}]}, status=200)
    g = GPTZero()
    g.api_key = "k"
    g.tara("X", "metin")
    govde = json.loads(responses.calls[0].request.body)
    assert "multilingual" not in govde


@responses.activate
def test_originality_v1_scan_ai_ve_dile_gore_model():
    """v3/scan + aiModelVersion='multilang' 422 veriyordu; canli API ile
    dogrulanan sozlesme v1/scan/ai + score.ai + surum numarasi ('1'/'2')."""
    responses.add(responses.POST, "https://api.originality.ai/api/v1/scan/ai",
                  json={"score": {"ai": 0.62, "original": 0.38}}, status=200)
    o = Originality()
    o.api_key = "k"
    s = o.tara("X", "metin", "TUR")

    govde = json.loads(responses.calls[0].request.body)
    assert s.yz_olasilik == 62.0
    # API'de otomatik dil secimi YOK — TR multilingual (2), EN Lite (1)
    assert govde["aiModelVersion"] == Originality.MODEL_TR
    assert govde["title"]            # zorunlu alan
    assert "/api/v1/scan/ai" in responses.calls[0].request.url


@responses.activate
def test_originality_ingilizcede_lite_modeli():
    responses.add(responses.POST, "https://api.originality.ai/api/v1/scan/ai",
                  json={"score": {"ai": 0.9, "original": 0.1}}, status=200)
    o = Originality()
    o.api_key = "k"
    o.tara("X", "metin", "ENG")
    assert json.loads(responses.calls[0].request.body)["aiModelVersion"] == Originality.MODEL_EN


@responses.activate
def test_skor_kayan_nokta_artigi_kirpilir_ama_olcek_hatasi_patlar():
    """GPTZero tam kesinlikte 1.0 yerine 1.0000000000000003 donduruyor;
    x100 = 100.000...03 ile aralik kontrolu 5 metni bosa dusurmustu.
    EPSILON kadar tasma kirpilir, GERCEK olcek hatasi hala hata verir."""
    responses.add(responses.POST, "https://api.gptzero.me/v2/predict/text",
                  json={"documents": [{"class_probabilities": {"ai": 1.0000000000000003},
                                       "document_classification": "AI_ONLY"}]}, status=200)
    g = GPTZero()
    g.api_key = "k"
    s = g.tara("X", "metin")
    assert s.hata is None and s.yz_olasilik == 100.0

    responses.reset()
    responses.add(responses.POST, "https://api.gptzero.me/v2/predict/text",
                  json={"documents": [{"class_probabilities": {"ai": 101.0},
                                       "document_classification": "AI_ONLY"}]}, status=200)
    s2 = g.tara("X", "metin")
    assert s2.yz_olasilik is None and "aralik disi" in s2.hata


@responses.activate
def test_zerogpt_fakePercentage_ve_ApiKey_basligi():
    responses.add(responses.POST, "https://api.zerogpt.com/api/detect/detectText",
                  json={"data": {"fakePercentage": 73.4, "feedback": "AI/GPT Generated"}},
                  status=200)
    z = ZeroGPT()
    z.api_key = "k"
    s = z.tara("X", "metin")

    assert s.yz_olasilik == 73.4          # zaten 0-100, olceklenmemeli
    assert responses.calls[0].request.headers["ApiKey"] == "k"
    assert "Authorization" not in responses.calls[0].request.headers


@responses.activate
def test_sapling_score_0_1_araligindan_olceklenir():
    responses.add(responses.POST, "https://api.sapling.ai/api/v1/aidetect",
                  json={"score": 0.42}, status=200)
    s_ = Sapling()
    s_.api_key = "k"
    s = s_.tara("X", "metin")
    assert s.yz_olasilik == 42.0


@responses.activate
def test_aralik_disi_skor_reddedilir():
    """Bozuk yanit sessizce gecmemelidir."""
    responses.add(responses.POST, "https://api.sapling.ai/api/v1/aidetect",
                  json={"score": 7.5}, status=200)   # 0-1 olmali -> 750%
    s_ = Sapling()
    s_.api_key = "k"
    s = s_.tara("X", "metin")
    assert s.yz_olasilik is None
    assert "aralik disi" in s.hata


def test_anahtarsiz_arac_cagri_yapmaz():
    s_ = Sapling()
    s_.api_key = None
    s = s_.tara("X", "metin")
    assert s.yz_olasilik is None
    assert "SAPLING_API_KEY" in s.hata


@pytest.mark.parametrize("skor,beklenen", [
    (50.0, "Insan"),    # esik "> 50" — tam 50 Insan
    (50.1, "YZ"),
    (0.0, "Insan"),
    (100.0, "YZ"),
])
def test_karar_esigi(skor, beklenen):
    from yzdetect.detectors import Sonuc
    assert Sonuc("X", "Y", skor).karar == beklenen


@responses.activate
def test_zerogpt_http200_govdesindeki_hatayi_yakalar():
    """ZeroGPT hatalari HTTP 200 ile bildiriyor — govde kontrol edilmezse
    'data': null anlamsiz bir TypeError'a donusur.

    Gercek yanit (kredi bitiminde, canli dogrulandi):
        {"success": false, "code": 403, "message": "Not enough credits", "data": null}
    """
    responses.add(responses.POST, "https://api.zerogpt.com/api/detect/detectText",
                  json={"success": False, "code": 403,
                        "message": "Not enough credits", "data": None}, status=200)
    z = ZeroGPT()
    z.api_key = "k"
    s = z.tara("X", "metin")

    assert s.yz_olasilik is None
    assert "Not enough credits" in s.hata
    assert "TypeError" not in s.hata      # anlamsiz hata DEGIL
