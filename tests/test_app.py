from unittest.mock import patch

from flaskpp import FlaskPP
from flaskpp.app.config.default import DefaultConfig


@patch("flaskpp.generate_tailwind_css")
@patch("flaskpp.register_modules")
@patch("flaskpp.init_i18n")
@patch("flaskpp.handlers")
def test_flaskpp_basic_init(mock_handlers, mock_i18n, mock_register, mock_generate):
    mock_handlers.__getitem__.return_value = lambda *a, **k: None

    with patch("flaskpp.enabled", return_value=False):
        app = FlaskPP(__name__, "DEFAULT")

    assert isinstance(app.config, dict)
    assert isinstance(app.config["DEBUG"], bool)
    assert app.blueprints.get("fpp_default") is not None

    mock_i18n.assert_called_once()
    mock_register.assert_called_once()
    mock_generate.assert_called_once()


@patch("flaskpp.generate_tailwind_css")
@patch("flaskpp.register_modules")
@patch("flaskpp.init_i18n")
def test_flaskpp_proxy_fix(mock_i18n, mock_register, mock_generate):
    class C(DefaultConfig):
        PROXY_FIX = True
        PROXY_COUNT = 1

    with patch("flaskpp.CONFIG_MAP", {"X": C}):
        with patch("flaskpp.enabled", return_value=False):
            app = FlaskPP(__name__, "X")

    assert hasattr(app, "wsgi_app")


@patch("flaskpp.generate_tailwind_css")
@patch("flaskpp.register_modules")
@patch("flaskpp.init_i18n")
@patch("flaskpp.handlers")
def test_flaskpp_processing_handlers(mock_handlers, mock_i18n, mock_register, mock_generate):
    mock_handlers.__getitem__.return_value = lambda *a, **k: None

    def enabled_mock(key):
        return key == "FPP_PROCESSING"

    with patch("flaskpp.enabled", enabled_mock):
        app = FlaskPP(__name__, "DEFAULT")

    assert mock_handlers.__getitem__.call_count >= 3


@patch("flaskpp.generate_tailwind_css")
@patch("flaskpp.register_modules")
@patch("flaskpp.init_i18n")
def test_flaskpp_asgi(mock_i18n, mock_register, mock_generate):
    with patch("flaskpp.enabled", return_value=False):
        app = FlaskPP(__name__, "DEFAULT")

    asgi = app.to_asgi()
    assert hasattr(asgi, "__call__")
