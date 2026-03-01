from app.application.language import detect_language


def test_detect_language_arabic() -> None:
    assert detect_language("ما هي سياسة الطاقة؟") == "ar"


def test_detect_language_english() -> None:
    assert detect_language("What is the current transport policy?") == "en"
