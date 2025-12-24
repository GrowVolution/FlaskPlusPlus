# Flask++ Documentation

### App Factory

The default Flask app factory hasn't changed much. The FlaskPP class does a lot of repetitive work for you.
But the default factory which is also written into **project_root/main.py** by the `fpp init` command looks very similar:

```python
from flaskpp import FlaskPP
            
def create_app(config_name: str = "default"):
    app = FlaskPP(__name__, config_name)
    # TODO: Extend the Flask++ default setup with your own factory
    return app

app = create_app().to_asgi()    
```

The FlaskPP class just extended Flask with basic factory tasks like setting up extensions and config.

### Configuration

There are two ways of configuring your apps. The first and most important one are app configs, which you can find in project_root/app_configs.
They are named like that: **[app_name].conf** and used by the `fpp run` command to load your apps. (Config variables are passed as environment.)

With app configs you can control which extensions you want to use and pass secrets, defaults and every other data which you would usually write into your env files.
A basic Flask++ app.conf file looks like that:

```
[core]
SERVER_NAME = localhost
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
EXT_SOCKET = 1
EXT_BABEL = 0
EXT_FST = 0
EXT_AUTHLIB = 0
EXT_MAILING = 0
EXT_CACHE = 0
EXT_API = 0
EXT_JWT_EXTENDED = 0

[features]
FPP_PROCESSING = 1
FRONTEND_ENGINE = 1

[dev]
DB_AUTOUPDATE = 0

[modules]
module_name = 1
HOME_MODULE = module_name
```

And can be generated and configured automatically by running `fpp setup` inside your project root.

The second way of configuring your app, is by using config classes. You may have noticed, that the Flask++ app factory takes an
config name argument. There you can provide your own config name if you like to. We provide a registration function, so you can
plug in your own config files with ease. But of course we also provide a default config which you could just extend by your own config class:

```python
import os

from flaskpp.app.config import register_config
# If you want to extend this config, you can import it:
# from flaskpp.app.config.default import DefaultConfig


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
```

### Full-Stack Features & FPP Magic

Inside our app.conf example you may have noticed that there are two feature switches, which are set to 1 by default.
The first one is **FPP_PROCESSING** which brings a slightly changed app processor registration to offer you some fueatures
like request logging and socket default events. If you have enabled this, you would have to use the Flask++
processing utils to overwrite our default processors:

```python
from flaskpp.app.utils.processing import before_request

@before_request
def before_app_request():
    # TODO: Handle app request
    pass

# Or if you are using EXT_SOCKET we provide a default handler:
from flaskpp.app.utils.processing import socket_event_handler

@socket_event_handler # equivalent to socket.on("default_event")
def default_event(sid: str, data):
    # TODO: Your own default handling
    pass

# If you decide to use FPP_PROCESSING you can register socket events with:
from flaskpp.app.socket import default_event

@default_event("my_event")
def handle(data):
    # TODO: Handle your default socket event
    pass
```

And of course we do also have some JavaScript utility that matches with our socket default handlers:

```javascript
/**
 * To use this utility you just need to include this inside the head section of you base template:
 * 
 * <script src="https://cdn.socket.io/4.8.1/socket.io.min.js"
 *         integrity="sha384-mkQ3/7FUtcGyoppY6bz/PORYoGqOl7/aSUMn2ymDOJcapfS6PHqxhRTMh1RR0Q6+"
 *         crossorigin="anonymous">
 * </script>
 * <script id="fppSocketScript"
 *         src="{{ url_for('fpp_default.static', filename='js/socket.js') }}" type="module"
 *         data-socket-domain="{{ request.scheme.replace('http', 'ws') }}://{{ request.host }}">
 * </script>
 * */

const socketScript = document.getElementById("fppSocketScript");

export function connectSocket() {
    const domain = socketScript.dataset.socketDomain;
    return io(domain, {
        transports: ['websocket'],
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
        timeout: 20000
    })
}
export let socket = connectSocket();


export function emit(event, data=null, callback=null) {
    socket.emit('default_event', {
        event: event,
        payload: data
    }, callback);
}
```

Alright, before we talk about some further switch-less Flask++ magic... Let's talk about the second feature switch in our
app.conf file, which is **FRONTEND_ENGINE**. This switch enables you built in Vite engine. Your app and every module you may create has
got a Vite folder inside it, which contains a main.js entrypoint. This is generated by default as a template you can use to
integrate Vite into your Flask project. It will eiter run as `vite dev` if you run your app in debug mode or be built when starting your app
and then integrated using the .vite/manifest.json. If you want to integrate Vite files into your template, simply use:
`{{ vite_main("file.ending") }}` to integrate Vite files from your apps root and `{{ vite("file.ending") }}` inside module templates
to use the vite files of your modules. The framework does the configuration automatically for your. You can either write JavaScript or TypeScript.
And you can also work with Tailwind (Notice that there is a <a href="#externals">standalone Tailwind integration</a> too. This is intended to
be fully seperated from your vite builds. We highly recommend to keep the autogenerated `@source not "../../vite"` part.), the default structure for
that is autogenerated as well.

Okay, but now let's come to further Flask++ magic. The biggest switch-less feature is our module system. Modules look like little Flask apps
which can simply be plugged into your app using the app.conf file. This process can be automated, if you install or create your modules before
running `fpp setup`. To work with modules, just use the modules sub-cli:

```bash
# To install a module use:
fpp modules install module_name --src [path/git-url]
# And in future a module hub is planned, on which you'll be able to share your modules
# as well as install modules from there by their name:
fpp modules install hub_module_name

# To create a module use:
fpp modules create module_name
```

Our next feature is the i18n database (**EXT_BABEL**) with fallback to .po/.mo files for which we will offer an extra module to manage your translation keys
using a graphical web interface. ([FPP_i18n_module](https://github.com/GrowVolution/FPP_i18n_module) - coming soon.) But you can also manage your translations
by using our utility functions:

```python
from flaskpp.app.data.babel import (add_entry, 
                                    remove_entry, remove_entries, 
                                    get_entry, get_entries)

add_entry("en", "WELCOME_TEXT", "Welcome to our new website!")
# TODO: Further work with the i18n database
```

And if you use Flask Security Too (**EXT_FST**), you can easily modify and extend the fsqla mixin using our mixin decorators:

```python
from flaskpp.app.data.fst_base import user_mixin, role_mixin
from flaskpp.app.extensions import db

@user_mixin
class MyUserMixin:
    bio = db.Column(db.String(512))

    # TODO: Add your own features and functionality
```

Your mixin classes extend the user / role model, before the fsqla mixin extension is added. So be careful working with security features and utility.
In future, we'll add a priority feature, which will allow you to define the priority of your mixin when you decide to publish your own modules.

### Running / Managing your apps

Attentive readers may have also noticed the `app.to_asgi()` wrapper. (This wrapper automatically wraps your app into the correct format - so it is sensitive to the **EXT_SOCKET** switch.)
This feature is required, if you want to execute your apps with our built-in executing utility, because Flask++ is running your apps using Uvicorn to offer
cross-platform compatibility. You've got two options to run your apps:

```bash
# To run your apps standalone and straight up:
fpp run [-a/--app] app_name [-p/--port] 5000 [-d/--debug]

# If you would like to run and manage multiple apps at once:
fpp run [-i/--interactive]
```

### App Registry

If you are system administrator, you can also use our automated app registry (of course also cross-platform compatible):

```bash
fpp registry register app_name
fpp registry [start/stop] app_name
fpp registry remove app_name
```

On NT based systems make sure you have pywin32 installed in your Python environment.

<h3 id="externals">Standalone Node & Tailwind implementation</h3>

Flask++ provides a native integration of Tailwind CSS and Node.js.

To use Tailwind, simply integrate:

```html
<!-- Requires FPP_PROCESSING -->
<head>
    ...
    <!-- For your main app: -->
    {{ tailwind_main }}
    
    <!-- Inside a module: -->
    {{ tailwind }}
    
    <!-- Flask++ Tailwind -->
    {{ fpp_tailwind }}
    ...
</head>
```

into your templates and work with its CSS utility. The app will (re-)generate all **tailwind.css** files based on your **tailwind_raw.css** files (auto generated by
`fpp init` and `fpp modules create [mod_name]` in all **static/css** folders) when it is initialized.

And if you'd like to work with the native standalone node bundle, you can simply use the Flask++ Node CLI:

```bash
fpp node [npm/npx] [args]
```

Of course, you can use the Tailwind CLI in a similar way:

```bash
fpp tailwind [args]
```

But to be able to use them, you must run `fpp init` at least once, if you are using a fresh installation of Flask++.

### Get Help

Of course, you can simply use `fpp [-h/--help]` to get a quick overview on how to use the Flask++ CLI. And if you still
have questions, which haven't been answered in this documentation **feel free to join the [discussions](https://github.com/GrowVolution/FlaskPlusPlus/discussions)**.

---

**Thank you for working with Flask++**
