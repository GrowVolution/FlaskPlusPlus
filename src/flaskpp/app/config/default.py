import os

from flaskpp.app.config import register_config


@register_config('default')
class DefaultConfig:
    # -------------------------------------------------
    # Core / Flask
    # -------------------------------------------------
    SERVER_NAME = os.getenv("SERVER_NAME")
    SECRET_KEY = os.getenv("SECRET_KEY", "151ca2beba81560d3fd5d16a38275236")

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    MAX_FORM_MEMORY_SIZE = 16 * 1024 * 1024

    PROXY_FIX = False
    PROXY_COUNT = 1

    # -------------------------------------------------
    # Flask-SQLAlchemy & Flask-Migrate
    # -------------------------------------------------
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///database.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # -------------------------------------------------
    # Flask-Limiter (Rate Limiting)
    # -------------------------------------------------
    RATELIMIT = True
    RATELIMIT_STORAGE_URL = f"{os.getenv('REDIS_URL', 'redis://localhost:6379')}/1"
    RATELIMIT_DEFAULT = "500 per day; 100 per hour"
    RATELIMIT_STRATEGY = "fixed-window"

    # -------------------------------------------------
    # Flask-SocketIO
    # -------------------------------------------------
    SOCKETIO_MESSAGE_QUEUE = f"{os.getenv('REDIS_URL', 'redis://localhost:6379')}/2"
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"

    # -------------------------------------------------
    # Flask-BabelPlus (i18n/l10n)
    # -------------------------------------------------
    BABEL_DEFAULT_LOCALE = "de"
    SUPPORTED_LOCALES = os.getenv("SUPPORTED_LOCALES", BABEL_DEFAULT_LOCALE)
    BABEL_DEFAULT_TIMEZONE = "Europe/Berlin"
    BABEL_TRANSLATION_DIRECTORIES = "translations"

    # -------------------------------------------------
    # Flask-Security-Too
    # -------------------------------------------------
    SECURITY_PASSWORD_SALT = os.getenv("SECURITY_PASSWORD_SALT", "8869a5e751c061792cd0be92b5631f25")
    SECURITY_REGISTERABLE = True
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_UNAUTHORIZED_VIEW = None
    SECURITY_TWO_FACTOR = False

    # -------------------------------------------------
    # Authlib (OAuth2 / OIDC)
    # -------------------------------------------------
    OAUTH_CLIENTS = {
        # For example:
        # "github": {
        #     "client_id": os.getenv("GITHUB_CLIENT_ID"),
        #     "client_secret": os.getenv("GITHUB_CLIENT_SECRET"),
        #     "api_base_url": "https://api.github.com/",
        #     "authorize_url": "https://github.com/login/oauth/authorize",
        #     "access_token_url": "https://github.com/login/oauth/access_token",
        # },
    }

    # -------------------------------------------------
    # Flask-Mailman
    # -------------------------------------------------
    MAIL_SERVER = os.getenv("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 25))
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "noreply@example.com")

    # -------------------------------------------------
    # Flask-Caching (Redis)
    # -------------------------------------------------
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = f"{os.getenv('REDIS_URL', 'redis://localhost:6379')}/3"
    CACHE_DEFAULT_TIMEOUT = 300

    # -------------------------------------------------
    # Flask-Smorest (API + Marshmallow)
    # -------------------------------------------------
    API_TITLE = "My API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/api"
    OPENAPI_JSON_PATH = "openapi.json"
    OPENAPI_REDOC_PATH = "/redoc"
    OPENAPI_REDOC_URL = "https://cdn.jsdelivr.net/npm/redoc/bundles/redoc.standalone.js"
    OPENAPI_SWAGGER_UI_PATH = "/swagger"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    # -------------------------------------------------
    # Flask-JWT-Extended
    # -------------------------------------------------
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "119b385ec26411d271d9db8fd0fdc5c3")
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    JWT_REFRESH_TOKEN_EXPIRES = 86400
