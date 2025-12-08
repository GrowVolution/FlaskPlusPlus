
test_config = """
[core]
SERVER_NAME = test.local
SECRET_KEY = supersecret

[database]
DATABASE_URL = sqlite:///appdata.db

[redis]
REDIS_URL = redis://redis:6379

[babel]
SUPPORTED_LOCALES = en;de

[security]
SECURITY_PASSWORD_SALT = supersecret

[mail]
MAIL_SERVER = 
MAIL_PORT = 25
MAIL_USE_TLS = True
MAIL_USE_SSL = False
MAIL_USERNAME = 
MAIL_PASSWORD = 
MAIL_DEFAULT_SENDER = noreply@example.com

[jwt]
JWT_SECRET_KEY = supersecret

[extensions]
EXT_SQLALCHEMY = 1
EXT_SOCKET = 0
EXT_BABEL = 0
EXT_FST = 0
EXT_AUTHLIB = 0
EXT_MAILING = 0
EXT_CACHE = 0
EXT_API = 0
EXT_JWT_EXTENDED = 0

[features]
FPP_PROCESSING = 1

[dev]
DB_AUTOUPDATE = 0

[modules]
"""
