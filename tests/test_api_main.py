from apps.api.app import main


def test_cors_options_disable_credentials_for_wildcard(monkeypatch):
    monkeypatch.setenv("WEB_CORS_ORIGINS", "*")
    main.get_settings.cache_clear()

    try:
        options = main.cors_options()
    finally:
        main.get_settings.cache_clear()

    assert options["allow_origins"] == ["*"]
    assert options["allow_credentials"] is False


def test_cors_options_allow_credentials_for_explicit_origins(monkeypatch):
    monkeypatch.setenv("WEB_CORS_ORIGINS", "https://civic-pulse-roan.vercel.app,http://localhost:3000")
    main.get_settings.cache_clear()

    try:
        options = main.cors_options()
    finally:
        main.get_settings.cache_clear()

    assert options["allow_origins"] == [
        "https://civic-pulse-roan.vercel.app",
        "http://localhost:3000",
    ]
    assert options["allow_credentials"] is True
