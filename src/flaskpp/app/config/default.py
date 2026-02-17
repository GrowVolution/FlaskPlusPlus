import os

from flaskpp.utils import enabled


class DefaultConfig:
    SERVER_NAME = os.getenv("SERVER_NAME")
    SECRET_KEY = os.getenv("SECRET_KEY", "151ca2beba81560d3fd5d16a38275236")

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    MAX_FORM_MEMORY_SIZE = 16 * 1024 * 1024

    PROXY_FIX = False
    PROXY_COUNT = 1

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI", "sqlite:///database.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URI = f"{os.getenv('REDIS_URL', 'redis://localhost:6379')}/1"
    RATELIMIT_DEFAULT = "500 per day; 100 per hour"
    RATELIMIT_STRATEGY = "fixed-window"

    SOCKETIO_MESSAGE_QUEUE = f"{os.getenv('REDIS_URL', 'redis://localhost:6379')}/2"
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"

    BABEL_DEFAULT_LOCALE = "en"
    SUPPORTED_LOCALES = os.getenv("SUPPORTED_LOCALES", BABEL_DEFAULT_LOCALE)
    BABEL_DEFAULT_TIMEZONE = "UTC"
    BABEL_TRANSLATION_DIRECTORIES = "translations"

    SECURITY_PASSWORD_SALT = os.getenv("SECURITY_PASSWORD_SALT", "8869a5e751c061792cd0be92b5631f25")
    SECURITY_REGISTERABLE = True
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_UNAUTHORIZED_VIEW = None
    SECURITY_TWO_FACTOR = False

    OAUTH_CLIENTS = {}

    MAIL_SERVER = os.getenv("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 25))
    MAIL_USE_TLS = enabled("MAIL_USE_TLS")
    MAIL_USE_SSL = enabled("MAIL_USE_SSL")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "noreply@example.com")

    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = f"{os.getenv('REDIS_URL', 'redis://localhost:6379')}/3"
    CACHE_DEFAULT_TIMEOUT = 300

    API_TITLE = "My API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/api"
    OPENAPI_JSON_PATH = "openapi.json"
    OPENAPI_REDOC_PATH = "/redoc"
    OPENAPI_REDOC_URL = "https://cdn.jsdelivr.net/npm/redoc/bundles/redoc.standalone.js"
    OPENAPI_SWAGGER_UI_PATH = "/swagger"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "119b385ec26411d271d9db8fd0fdc5c3")
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    JWT_REFRESH_TOKEN_EXPIRES = 86400
