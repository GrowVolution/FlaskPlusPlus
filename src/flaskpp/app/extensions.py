from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_security import Security
from authlib.integrations.flask_client import OAuth
from flask_mailman import Mail
from flask_caching import Cache
from flask_smorest import Api
from flask_jwt_extended import JWTManager

from flaskpp.socket import FppSocket
from flaskpp.babel import FppBabel

limiter = Limiter(get_remote_address)
db = SQLAlchemy()
migrate = Migrate()
socket = FppSocket(async_mode="asgi")
babel = FppBabel()
security = Security()
oauth = OAuth()
mailer = Mail()
cache = Cache()
api = Api()
jwt = JWTManager()
