from unittest.mock import patch

from flaskpp import FlaskPP
from flaskpp.app.config import register_config


@patch("flaskpp.flaskpp.init_i18n")
def test_flaskpp_basic_init(mock_i18n):
    with patch("flaskpp.flaskpp.enabled", return_value=False):
        app = FlaskPP(__name__)

    assert isinstance(app.config, dict)
    assert isinstance(app.config["DEBUG"], bool)

    mock_i18n.assert_called_once()


@patch("flaskpp.flaskpp.generate_tailwind_css")
@patch("flaskpp.flaskpp.register_modules")
@patch("flaskpp.flaskpp.init_i18n")
def test_flaskpp_proxy_fix(mock_i18n, mock_register, mock_generate):
    @register_config()
    class C:
        PROXY_FIX = True
        PROXY_COUNT = 1

    with patch("flaskpp.flaskpp.enabled", return_value=False):
        app = FlaskPP(__name__)

    assert hasattr(app, "wsgi_app")


@patch("flaskpp.flaskpp.generate_tailwind_css")
@patch("flaskpp.flaskpp.register_modules")
@patch("flaskpp.flaskpp.init_i18n")
def test_flaskpp_processing_handlers(mock_i18n, mock_register, mock_generate):
    def enabled_mock(key):
        return key == "FPP_PROCESSING"

    with patch("flaskpp.flaskpp.enabled", enabled_mock):
        app = FlaskPP(__name__)


@patch("flaskpp.flaskpp.generate_tailwind_css")
@patch("flaskpp.flaskpp.register_modules")
@patch("flaskpp.flaskpp.init_i18n")
def test_flaskpp_asgi(mock_i18n, mock_register, mock_generate):
    with patch("flaskpp.flaskpp.enabled", return_value=False):
        app = FlaskPP(__name__)

    asgi = app.to_asgi()
    assert hasattr(asgi, "__call__")
