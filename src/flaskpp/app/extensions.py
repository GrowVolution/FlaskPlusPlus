from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from socketio import AsyncServer
from flask_babelplus import Babel
from flask_security import Security
from authlib.integrations.flask_client import OAuth
from flask_mailman import Mail
from flask_caching import Cache
from flask_smorest import Api
from flask_jwt_extended import JWTManager
from functools import wraps

from flaskpp.utils import enabled
from flaskpp.utils.debugger import log

limiter = Limiter(get_remote_address)
db = SQLAlchemy()
migrate = Migrate()
socket = AsyncServer(async_mode="asgi", cors_allowed_origins="*")
babel = Babel()
security = Security()
oauth = OAuth()
mailer = Mail()
cache = Cache()
api = Api()
jwt = JWTManager()


def require_extensions(*extensions):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for ext in extensions:
                if not isinstance(ext, str):
                    log("warn", f"Invalid extension '{ext}'.")
                    continue

                if not enabled(f"EXT_{ext.upper()}"):
                    raise RuntimeError(f"Extension '{ext}' is not enabled.")
            return func(*args, **kwargs)

        return wrapper
    return decorator
