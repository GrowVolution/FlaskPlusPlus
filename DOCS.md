# Flask++ v0.3.x Documentation

## Core

### App Factory

The default Flask app factory hasn't changed much. But the FlaskPP class can do a lot of repetitive work for you. A sample factory is written into **project_root/main.py** by the `fpp init` command:

```python
from flaskpp import FlaskPP

def create_app():
    app = FlaskPP(__name__)

    # TODO: Extend the Flask++ default setup with your own factory

    return app

if __name__ == "__main__":
    app = create_app()
    app.start()  
```

The FlaskPP class just extends Flask with basic factory tasks like setting up the most common extensions and its config.

### Configuration

There are two ways of configuring your apps. The first and most important one is app configs, which you can find in **project_root/app_configs**. They are named like that: **[app_name].conf** and used by the `fpp run` command to load your apps. (Config variables are passed as environment.)

With app configs you can control which features and extensions you want to use or pass secrets, defaults and every other data that you would usually write into your env files. A basic Flask++ **app.conf** file looks like that:

```
[core]
SERVER_NAME = localhost
SECRET_KEY = supersecret

[database]
DATABASE_URI = sqlite:///appdata.db

[redis]
REDIS_URL = redis://localhost:6379

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
EXT_BABEL = 1
EXT_FST = 0
EXT_AUTHLIB = 0
EXT_MAILING = 0
EXT_CACHE = 0
EXT_API = 0
EXT_JWT_EXTENDED = 0

[features]
FPP_PROCESSING = 1
FPP_I18N_FALLBACK = 1
AUTOGENERATE_TAILWIND_CSS = 1
FPP_MODULES = 1
FRONTEND_ENGINE = 1

[dev]
DB_AUTOUPDATE = 0

[modules]
module_id = 1
module_id_01 = 0
module_id_02 = 0
...

MODULE_HOME = module_id
```

It can be generated and configured automatically by running `fpp setup` inside your project root.

The second way of configuring your app is by using config classes. We provide a registration function, so you can plug in your own config classes with ease. They will be extended with each other to one big config class by priority (values 1 to 10). In the end it will be extended with our default config class:

```python
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
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI", "sqlite:///database.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # -------------------------------------------------
    # Flask-Limiter (Rate Limiting)
    # -------------------------------------------------
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URI = f"{os.getenv('REDIS_URL', 'redis://localhost:6379')}/1"
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

So you can overwrite config keys by priority. This is especially useful to provide specific configuration for your modules.

### Lifecycle

You may have noticed the `app.start()` method inside our autogenerated **main.py** file shown in the ["App Factory" chapter](#app-factory). This method is an automated lifecycle manager that replaces the `app.run()` method. It will automatically run itself inside a daemon thread using Uvicorn. To handle SIGINT and SIGTERM signals, it uses a `threading.Event` flag. The FlaskPP class provides decorators to register startup and shutdown hooks which will be executed before and after the app starts and stops. You can register hooks like that:

```python
@app.on_startup
def startup_hook():
    # TODO: Whatever you want to do before the server thread gets started
    pass

@app.on_shutdown
def shutdown_hook():
    # TODO: Whatever you want to do when the server thread has been stopped
    pass
```

### ASGI Wrapper

If you are running your app using the start method, you may ask how a wsgi app is running itself inside an asgi server. Well, therefore the FlaskPP class provides a `app.to_asgi()` wrapper. It will map itself into an asgi compatible class, but sensitive to the **EXT_SOCKET** switch:

```python
class FlaskPP(Flask):
    ...
    def to_asgi(self) -> WsgiToAsgi | ASGIApp:
        if self._asgi_app is not None:
            return self._asgi_app

        wsgi = WsgiToAsgi(self)

        if enabled("EXT_SOCKET"):
            from flaskpp.app.extensions import socket
            app = ASGIApp(socket, other_asgi_app=wsgi)
        else:
            app = wsgi

        self._asgi_app = app
        return self._asgi_app
```

## Modules

Modules are the most important feature of Flask++ apps. They work like little blueprint-based Flask apps, which can be plugged into your main app using the module switches inside your app config files. Of course, you can turn off this feature by setting the **FPP_MODULES** switch to 0.

### Module Setup

The easiest way to create a module is to use the `fpp modules create` command. But you can also create modules manually. It would be way more work, but we will explain what it would look like. Not because it is recommended but to provide a basic understanding of how modules work.

At first, you would create a new python package inside **project_root/modules**. It is recommended to use the module id as the package name, but you don't necessarily have to.

#### Manifest

For your module to be recognized by Flask++ you need to create a **manifest.json** file inside your module package. It has to contain at least one field named "version". The following version string formats are supported (they are not case-sensitive):

```
x
x alpha
x beta
x rc

x.x
x.x alpha
x.x beta
x.x rc

x.x.x
x.x.x alpha
x.x.x beta
x.x.x rc
```

A fully qualified manifest file would then look like this:

```json5
{
  "id": "module_id",            // if not set, the package name will be used as id
  "name": "Module Name",
  "description": "This module does ...",
  "version": "0.1",
  "requires": {
    "fpp": ">=0.3.5",           // the minimum required version of Flask++
    "packages": [               // PyPI packages that are required by your module
      // e.g. "numpy", "pandas",
      // ...
    ],
    "modules": {                // other modules that are required by your module
      "module_id_01": "==0.2",
      "module_id_02": "<0.7"
    }
  }
}
```

#### Init File

Inside your **\_\_init__.py** file, you create a `module: Module` variable and optionally register a `module.on_enable` hook:

```python
from flaskpp import Module
from flaskpp.utils import enabled
from flaskpp.exceptions import ModuleError

module = Module(
    __file__,
    __name__,
    
    # Optional a list of required_extensions:
    [
    #    "sqlalchemy",
    #    "socket",
    #    "babel",
    #    "fst",
    #    "authlib",
    #    "mailing",
    #    "cache",
    #    "api",
    #    "jwt_extended"
    ],
    # init_routes_on_enable=False
    # -> You can optionally turn off automated route initialization when the module gets enabled.
    # This could be especially useful, if you are working with socket i18n. (More in the later chapters.)
)

# Now if you need to do stuff when your module gets enabled:
@module.on_enable
def on_enable(app: FlaskPP):
    # Check for required features, for example:
    if not enabled("FPP_PROCESSING"):
        raise ModuleError(f"Module '{module.module_name}' requires FPP_PROCESSING.")
    
    with app.app_context():
        # TODO: Do something that requires the app context if you need to
        pass
    
    # And if you disabled automated route initialization:
    module.init_routes()
    
    # The module has got its own context dict, which is used by the modules context_processor.
    # So you can set up default variables which will be available inside your modules templates:
    module.context["my_variable"] = "Hello World!"
    
    # You do not need to register your module as a blueprint, this will happen automatically

```

#### Handling

To abstract the handling of your module from its routes, the Module class provides a `module.handle_request(handler_name: str)` function. You can combine this with a handling package inside your module. The handling feature is automated as well. For it to work, you need to create an `init_handling(mod: Module)` function inside its **\_\_init__.py** file. The default init file created by the`fpp modules create` command looks like this:

```python
from pathlib import Path
from importlib import import_module

from flaskpp import Module

_package = Path(__file__).parent

def init_handling(mod: Module):
    for file in _package.rglob("*.py"):
        if file.stem == "__init__" or file.stem.startswith("noinit"):
            continue

        rel = file.relative_to(_package).with_suffix("")
        handler_name = ".".join(rel.parts)

        handler = import_module(f"{mod.import_name}.handling.{handler_name}")
        handle_request = getattr(handler, "handle_request", None)
        if not handle_request:
            continue

        mod.handler(handler_name)(handle_request)
```

Handler files should then at least contain this:

```python
def handle_request(mod: Module, *args):
    # TODO: Handle your request here
    pass
```

But you can also build your own handling structure working with the `module.handler(handler_name: str)` decorator, as long as you stick with the handle_request function signature shown above. The module parameter will be passed by a wrapper inside the function's decorator.

#### Routes

You will also need to create a **routes.py** file inside your module package. This file will have to contain an `init_routes(mod: Module)` function, which will be imported and called automatically by the `module.init_routes()` function. So your file should look something like this:

```python
def init_routes(mod: Module):
    @mod.route("/my-route")
    def my_route():
        # Modules provide their own render_template function, so you can easily target the templates of your module:
        return mod.render_template("module_template.html")
        # This automatically renders the templates of your modules template folder.

    # Of course, you can work with your handlers, which we set up before:
    mod.route("/handle")(
        mod.handle_request("my_handler")
    )
    
    # Or you can go really crazy and do something like this, for example:
    @mod.route("/handle/<string:handler_name>/<path:path>")
    def handle_id(handler_name: str, path: str):
        return mod.handle_request(handler_name)(path)
```

#### Config

You can optionally create a **config.py** file inside your module package. There you can create your modules config class (like mentioned earlier in the ["Configuration" chapter](#configuration)) and add a config function for the `fpp setup` command if you need:

```python
from flaskpp.app.config import register_config

@register_config(
    # Optionally set a priority (default is 1):
    priority=2
)
class ModuleConfig:
    # TODO: Overwrite default config values or provide your own
    pass

def module_config():
    # return {
        # TODO: Write required config data (will be prompted by the setup if module is set to 1)
    
        # "protected_MY_SECRET": token_hex(32),
        # -> protected keys won't be prompted to the user
    
        # "default_FEATURE_KEY": "Hello World!",
        # -> default keys will be prompted with their default value shown (and written with if input left empty)
    
        # "ADDITIONAL_DATA": "",
        # -> simple config prompt without default value
    # }
    pass
```

#### Data Package

If your module requires **EXT_SQLALCHEMY** you need to create a **data** package inside your module. There you can create your modules model classes. For this to work, you have to create an `init_models()` function inside its **\_\_init__.py** file. The generated default looks like this:

```python
from pathlib import Path
from importlib import import_module

from flaskpp import Module

_package = Path(__file__).parent

def init_models(mod: Module):
    for file in _package.rglob("*.py"):
        if file.stem == "__init__" or file.stem.startswith("noinit"):
            continue
        rel = file.relative_to(_package).with_suffix("")
        import_module(f"{mod.import_name}.data.{".".join(rel.parts)}")
```

#### Extracting

The Module class provides a `module.extract()` function. This function is meant to be used by the Flask++ CLI to extract the modules globals to the app's static / templates when the module gets installed. This is especially useful if your module needs to install global templates if it is not meant to be installed as a home module. To use this feature, you need to create an **extract** folder containing a **templates** and/or **static** folder inside your module package. Their contents will then be extracted to the app's static and templates folder.

### Working with Modules

To simplify the work with modules, they provide their own render_template (like mentioned above) and url_for functions. So when you are handling a request inside a module, we recommend using these functions instead of the global ones. Modules are sensitive to the **HOME_MODULE** configuration. Defining a home module is optional, but if you do so, the module will be registered as if it was the main app when it gets enabled.

#### Context

As shown earlier, modules do have their own context dict. It has a default value called "NAME", which you can use inside your modules templates to resolve its templates or urls:

```html
{% extends NAME ~ "/base.html" %}

{% block content %}
    <h1>My Title</h1>
    <p>
        See my beautiful image:<br>
        &nbsp;&nbsp;&nbsp;&nbsp;
        <a href="{{ url_for(NAME ~ '.static', filename='img/my_image.png') }}">
            Me riding a rollercoaster
        </a>
    </p>
{% endblock %}
```

## Features

When you take a look at our app config example, which we have shown in the ["Configuration" chapter](#configuration), you may have noticed that there are some feature switches. Besides those switches, some of the extension switches are also enabling adopted Flask++ extension classes and features, which extend the underlying Flask extension. We will show you which extensions are affected, so you can turn them off if you would like to stick with Flask defaults.

The FlaskPP class uses the `flaskpp.utils.enabled` function to check if a feature or extension switch is enabled. If so, it will automatically set up the specific feature or initialize the extension.

### FPP_PROCESSING

The first feature switch is **FPP_PROCESSING**. This will cause the app to use the Flask++ processing utils to register request processors. Therefore, it uses the `flaskpp.app.utils.processing` module. It provides its own decorators that replace the Flask ones, which is useful if you want to use some of the Flask++ processing utility. The decorators will then overwrite the Flask++ default processors.

Flask++ default processors provide some useful features like extended context processing (matching to the Flask++ environment), request logging and error handling (rendering "404.html" on NotFound errors or else "error.html").

To overwrite processors, use their matching decorators like this:

```python
from flaskpp.app.utils.processing import (
    # context_processor,
    before_request #, 
    # after_request,
    # handle_app_error
)

@before_request
def before_request():
    # TODO: Do your own handling
    pass
```

The FlaskPP class uses the `set_default_handlers(app: Flask)` function to set its default processors. This util then uses the `get_handler(name: str) -> Callable` function to get the matching handler from the processing utils. Both are part of the processing module and look like this:

```python
def get_handler(name: str) -> Callable:
    handler = _handlers.get(name)
    if not handler or not callable(handler):
        if name == "context_processor":
            return _context_processor
        if name == "before_request":
            return _before_request
        if name == "after_request":
            return _after_request
        if name == "handle_app_error":
            return _handle_app_error
    return handler

def set_default_handlers(app: Flask):
    app.context_processor(
        lambda: get_handler("context_processor")()
    )
    app.before_request(
        lambda : get_handler("before_request")()
    )
    app.after_request(
        lambda response: get_handler("after_request")(response)
    )
    app.errorhandler(Exception)(
        lambda error: get_handler("handle_app_error")(error)
    )
```

### EXT_SOCKET

When we talk about **FPP_PROCESSING** we should also mention the **EXT_SOCKET** extension switch. It extends SocketIOs AsyncServer with some Flask++ specific features. Some of those features are default features of the FppSocket class, and others rely on the default_processing switch. The sockets default processing features will either be turned on by the **FPP_PROCESSING** config switch or by setting its default_processing value to True (before you initialize the FlaskPP class).

The default features of the FppSocket class are its event_context (inspired by Flasks request_context) and the enable_sid_passing value of its init function (default is True because it's the AsyncServers default too) or the `socket.sid_passing` switch itself (if you are using the socket from `flaskpp.app.extensions` and want to turn it off):

```python
from flaskpp.app.extensions import socket
from flaskpp.utils.debugger import log

@socket.on("my_event")
async def event(
    sid: str,       # if you did not set sid_passing to False
    payload: Any
):
    # here you can access:
    ctx = socket.event_context
    # which currently only contains the current session, which you can either access via context now:
    log("info", f"Current session data from context: {ctx.session}")
    # or via:
    log("info", f"Current session data from socket: {socket.current_session}")
```

If you enable default processing, you will get access to the full power of the FppSocket class. This includes default events (a socket event called "default_event" or – if you initialize your own FppSocket – whatever default_event_name you pass to its init function), a default connect handler (which writes the session and lang cookie into the session), error handling, HTML injectors (A default_event called "html". It can be used to return HTML strings that you can write into DOM blocks with your scripts.), decorators to replace the default processing functions with your own ones and a get_handler function to fetch default handlers:

```python
from flaskpp.app.extensions import socket

@socket.on_default(
    "my_event",
    # namespace="my_namespace",
    # pass_sid=True,
    # **test_request_ctx 
    # -> Default events are additionally executed inside app.test_request_context() to use Flasks rendering utility there
)
async def my_event(
    # sid: str,
    payload: Any
):
    # TODO: Handle your default event
    pass

@socket.html_injector(
    "my_html",
    # namespace="my_namespace"
)
async def my_html():
    return "<div>Hello World!</div>"

# Like you can do with the Flask++ default processors,
# you can also overwrite the sockets default processors:

@socket.on_connect
async def handle_connect(sid: str, environ: dict):
    # TODO: Handle the incoming socket connection
    pass

@socket.default_handler
def handle_default_event(sid: str, data: dict):
    # TODO: Handle every socket event called default_event (or whatever name you gave it)
    pass

@socket.html_handler
def handle_html_request(key: str):
    # TODO: Handle every default_event called "html"
    pass

@socket.on_error
def handle_error(error: Exception):
    # TODO: Handle the exception
    # Every exception that happens while executing your events lands here
    pass

# You can retrieve default handlers using:
handler = socket.get_handler(
    "my_handler",
    # namespace="my_namespace",
    # event_type="html"
    # -> event_type defines which type of handler should be retrieved. It defaults to "default" for default events.
    # If the passed event_type neither matches "default" nor "html", it will try to fetch the classic BaseServer handler.
)
# This function escalates its fallback similar to SocketIOs BaseServer:
# handler_dict[namespace][handler_name]
# handler_dict[namespace]["*"]
# handler_dict["*"][handler_name]
# handler_dict["*"]["*"]
```

Be aware that default events should not contain any "@" inside their names, because the FppSocket resolves namespaces of default events using the "@" character.

### EXT_BABEL & FPP_I18N_FALLBACK

These two switches come together. The **FPP_I18N_FALLBACK** switch only takes effect if the **EXT_BABEL** switch is enabled too. This is because Flask++ also provides its own Babel class called FppBabel, which extends `flask_babelplus.Babel`. Besides that, Flask++ also changes the internationalization process to fit into the Flask++ environment. That's why **EXT_BABEL** requires the **EXT_SQLALCHEMY** switch to be enabled. The Flask++ i18n system primarily stores translations inside the database and only uses the message catalogs as fallback.

It also provides its own domain resolving system, which matches with the Flask++ module system. This is also where the **FPP_I18N_FALLBACK** switch comes into play, because it adds a fallback domain called "flaskpp" which contains default translation keys providing German and English translations, that are used by the Flask++ [app utility](#further-utilities).

Let's take a look at how you set up Babel for a specific module and how the fallback escalation works:

```python
# Use the on_enable hook of your module and build your modules __init__.py file like this, for example:
from flaskpp import Module
from flaskpp.babel import register_module
from flaskpp.utils import enabled
from flaskpp.exceptions import ModuleError

module = Module(
    __file__,
    __name__,
    [
        "sqlalchemy",
        "socket",
        "babel"
    ],
    False
    # -> False to install translations before route setup.
    # This is especially useful if you are using translations inside your route setup.
)

@module.on_enable
def enable(app: FlaskPP):
    # This is where the noinit feature of the default generated data/__init__.py file comes into play:
    from .data.noinit_translations import setup_db
    with app.app_context():
        setup_db(module)            # We will show you a quick example of how this could look like in the next code block.
        register_module(
            module,
            # domain_name="custom_name"
            # -> default is module.name
        )   # This will register the domain_name as the modules translation domain, pass it as a variable called "DOMAIN" to the
            # context processor and automatically cause _ and ngettext to primarily resolve translation keys from that domain.
        
    # Now you can enable routes after you registered your translations
    module.init_routes()

# If you now do something like this, for example:
from flask import render_template_string
@module.route("/example")
def example():
    return render_template_string(
        "<h1>{{ _('EXAMPLE_TITLE') }}</h1>"
    )
# The EXAMPLE_TITLE translation will be resolved in this order:
# 1. Try to find it in the modules registered domain_name
# 2. Try to find it inside FppBabels fallback domain (set by flaskpp.babel.set_fallback_domain function)
# 3. Try to find it inside "messages" (or whatever you set as the default domain)
# 4. Try to find it inside the "flaskpp" domain (if FPP_I18N_FALLBACK is enabled)
# 5. Stick with the original key
```

And here is an example of what your **module_package/data/noinit_translations.py** file could look like:

```python
from flaskpp.app.data import commit
from flaskpp.app.data.babel import add_entry, get_entries, get_entry

_msg_keys = [
    "EXAMPLE_TITLE",
    # ...
]

_translations_en = {
    _msg_keys[0]: "My English Title",
    #...
}

_translations_de = {
    _msg_keys[0]: "Mein Deutscher Titel",
    # ...
}

def _add_entries(key, domain):
    add_entry("en", key, _translations_en[key], domain, False)
    add_entry("de", key, _translations_de[key], domain, False)

def setup_db(mod: Module):
    domain = mod.name
    entries = get_entries(domain=domain, locale="en")

    if entries:
        keys = [e.key for e in entries]
        for key in _msg_keys:
            if key not in keys:
                _add_entries(key, domain)

        for entry in entries:
            key = entry.key
            if _translations_en[key] != entry.text:
                entry.text = _translations_en[key]
                entry_de = get_entry(key, "de", domain)
                entry_de.text = _translations_de[key]
    else:
        for key in _msg_keys:
            _add_entries(key, domain)

    commit()
```

Like with our FppSockets default event system, our domain resolving system uses the "@" character as well. So when you are using our integrated i18n tooling, you should avoid using "@" characters inside your translation keys as well. 

### AUTOGENERATE_TAILWIND_CSS

Flask++ comes with its own Tailwind integration. Therefore, it uses Tailwinds standalone cli tool to generate your CSS files on the fly. If you enable **AUTOGENERATE_TAILWIND_CSS**, Flask++ will automatically compile every **tailwind_raw.css** file inside your apps or modules **static/css** folder and create a corresponding **tailwind.css** asset, when you run `app.start()`. 

And if you are using **FPP_PROCESSING**, you can integrate the generated assets into your <head> section like this (assuming you did not overwrite its default context_processor):

```html
<head>
    {{ tailwind_main }}
    
    <!-- And the default styles provided by Flask++: -->
    {{ fpp_tailwind }}
    
    <!-- If you have enabled FPP_MODULES, you can integrate the modules styles with: -->
    {{ tailwind }}
    <!-- This will also work without FPP_PROCESSING, because it's a module specific feature. -->
</head>
```

### FRONTEND_ENGINE

The next thing a well-balanced full-stack framework should not miss is an integrated frontend tooling. That's why Flask++ comes with its own Node.js integration. Therefore, it uses the standalone Node bundle (if you have not installed Node globally) and then uses it to integrate Vite into your project. So if you enable **FRONTEND_ENGINE**, Flask++ will automatically plug in a blueprint-based Frontend class when you start your app. If you run your app in debug mode, it will also automatically start a Vite server per module (the framework automates the request resolving for you), otherwise it will use the production build.

The frontend tooling also uses the **tailwind_raw.css** file inside the **vite/src** folder to generate the **tailwind.css** asset. In debug mode this will be regenerated on every request. For compatibility reasons and to reduce redundancy, it uses the integrated Tailwind cli tool for that as well. When you would like to use a specific vite folder to export it into standalone Vite projects, you should be aware of that.

Next is that Flask++ orchestrates the Node and Vite configuration centrally inside the framework. So you won't find dozens of config files and node_modules in every vite folder. Currently, you cannot modify the Vite configuration manually. So for now you can only stick with the very basics when working with our frontend tooling. Besides Tailwind, this only includes working with TypeScript.

To integrate vite into your templates, you can use:

```html
<head>
    {{ vite_main("main.js") }}
    
    <!-- Or like with Tailwind before in the context of a module: -->
    {{ vite("main.js") }}
</head>
```

### EXT_FST

This extension switch enables the flask_security extension. And even if there's no whole class built on top of it, there's still some tooling we should quickly mention. We are talking about user and role mixins, with which you can expand Flask Security Toos default mixins. It works very similarly to how we build up our Config class. So you should be careful with overwriting FSTs default security features and utilities.

To plug in your own mixins, we provide decorators that you can use inside your modules data package, for example:

```python
# module_package/data/noinit_fst.py
# -> Have to be named exactly like that, so that the app can see and initialize them when it sets up FST
from flaskpp.app.data.fst_base import user_mixin #, role_mixin
from flaskpp.app.extensions import db

@user_mixin(
    # priority=2
    # -> Like config priority, it should be a value inclusively between 1 and 10 and defaults to 1.
)
class MyUserMixin:
    bio = db.Column(db.String(512))
    # ...
```

## Further Utilities

To make your life even easier, Flask++ provides some additional utilities and templates. You can use them to play around with the framework or integrate them into your own projects. In this chapter we will show you how to use them and how they work, so you can abstract parts of them into your own code base.

### Example Base Template

The most important file we provide is the **example_base.html** file. As long as you do not have a similar named template inside your apps or home modules **templates** folder, you can extend it by using `{% extends "example_base.html" %}`. Flask++ uses a ChoiceLoader which automatically falls back to the frameworks templates if the template does not exist anywhere else.

In the following chapters, we will introduce our further utilities and show you how they are integrated into our example base template.

### Socket and Base script

Of course, we provide utilities that close the circle when using our [Flask++ features](#features). Inside the frameworks **socket.js** file, this includes a namespace-sensitive emit and emitAsync function for default events. And for the frameworks **base.js** file, this includes further utilities like socket i18n, flashing, safe execution, info and confirm dialogs using the frameworks modal templates (they are integrated into our example base as well) and a socketHtmlInject function matching the [FppSockets](#ext_socket) HTML injectors.

Our example base template integrates them like that:

```html
<head>
    <!-- The enabled(key: str) util is injected by the FPP_PROCESSING utility (if you did not overwrite the context_processor) -->
    {% if enabled("EXT_SOCKET") %}
        <script src="https://cdn.socket.io/4.8.1/socket.io.min.js"
                integrity="sha384-mkQ3/7FUtcGyoppY6bz/PORYoGqOl7/aSUMn2ymDOJcapfS6PHqxhRTMh1RR0Q6+"
                crossorigin="anonymous">
        </script>
        <script id="fppSocketScript"
                src="{{ url_for('fpp_default.static', filename='js/socket.js') }}" type="module"
                data-socket-domain="{{ request.scheme.replace('http', 'ws') }}://{{ request.host }}">
        </script>
        <!-- You can inject a namespace variable into module.context if you want to have module-specific namespaces.
             Our scripts emit and socketHtmlInject functions will then automatically use the namespace. -->
        <meta name="sio:namespace" content="{{ namespace if namespace else '' }}">
    
        <script src="{{ url_for('fpp_default.static', filename='js/base.js') }}" type="module"></script>
    {% endif %}
</head>
```

The base script also writes all utils into window.FPP so you can use them inside your vite scripts as well. You can also use our **base_example.html** and play around with those utils inside your browser console:

```javascript
window.FPP = {
    showModal: showModal,
    hideModal: hideModal,

    confirmDialog: confirmDialog,
    showInfo: showInfo,

    flash: flash,

    safe_: safe_,

    _: _,
    _n: _n,

    socketHtmlInject: socketHtmlInject,

    socket: socket,
    emit: emit,
    emitAsync: emitAsync,
}
```

### Navigation

We do also provide an auto_nav module inside `flaskpp.app.utils`, which you can use to automatically generate your navigation bar. Here is an example of what this would look like:

```python
# Assuming you are using it inside your modules routes.py file:
from flaskpp.app.utils.auto_nav import autonav_route, DropdownBuilder

def init_routes(mod: Module):
    
    _ = mod.t
    # -> If you want the message catalogue resolver of default Babel to work as well
    
    @autonav_route(
        mod, 
        "/example",
        _("EXAMPLE_LABEL"),
        # priority=2,
        # -> Same priority concept; defaults to 1.
        # additional_classes="text-green-400 hover:bg-green-500/10"
        # -> To add additional classes to the nav item; default is "".
    )
    def example():
        return mod.render_template("example.html")

    builder = DropdownBuilder(
        _("DROPDOWN_LABEL"),
        # dropdown_priority=2,
        # -> Same priority concept.
        # additional_dropdown_classes="text-black-400 hover:bg-black-500/10"
        # -> To add additional classes to the dropdown item.
    )
    @builder.dropdown_route(
        mod,
        "/dropdown-item-1",
        _("DROPDOWN_ITEM_1_LABEL"),
        # same as autonav_route
        # ...
    )
    def dropdown_item_1():
        return mod.render_template("dropdown_item_1.html")

    # TODO: Add more dropdown items here.
    
    # And at the end save your menu (you cannot register further items after that):
    builder.save()
```

This is integrated into our example base template like this:

```html
<nav>
    <div class="nav-inner-div">
        <a class="nav-brand" href="/">{{ _('NAV_BRAND') }}</a>

        <button class="nav-collapse-btn" type="button" data-collapse-toggle="navbarCollapse"
                aria-controls="navbarCollapse" aria-expanded="false" aria-label="Toggle navigation">
            <span class="mb-1 nav-collapse-btn-stripe"></span>
            <span class="mb-1 nav-collapse-btn-stripe"></span>
            <span class="nav-collapse-btn-stripe"></span>
        </button>

        <div id="navbarCollapse" class="nav-collapse max-md:hidden">
            <!-- The NAV variable is injected by the FPP_PROCESSING utility (if you did not overwrite the context_processor) -->
            {% for nav_type, nav_data in NAV.items() %}
                {% if nav_type == "links" %}
                    {% for link in nav_data %}
                        {% include "nav_link.html" with context %}
                    {% endfor %}
                {% elif nav_type == "dropdowns" %}
                    {% for dropdown in nav_data %}
                        {% include "dropdown.html" with context %}
                    {% endfor %}
                {% endif %}
            {% endfor %}

            {% block nav %}{% endblock %}

            <div class="relative ml-auto pl-3">
                <details class="group">
                    <summary class="nav-lang-summary">
                        <!-- The get_locale_data function and LANG variable are injected by FPP_PROCESSING as well -->
                        {% with data = get_locale_data(LANG) %}
                            <span class="fi fi-{{ data[0] }}"></span>
                        {% endwith %}
                        <svg viewBox="0 0 20 20"
                             fill="currentColor">
                            <path fill-rule="evenodd" d="M7 5l6 5-6 5V5z" clip-rule="evenodd"></path>
                        </svg>
                    </summary>

                    <div class="nav-lang-dropdown">
                        {% for locale in config["SUPPORTED_LOCALES"].split(";") %}
                            {% with data = get_locale_data(locale) %}
                                <!-- If you have EXT_BABEL enabled, Flask++ will automatically register that route for you. -->
                                <a href="/lang/{{ locale }}?path={{ request.path }}" class="nav-lang-link">
                                    <span class="fi fi-{{ data[0] }} fis mr-2 rounded-4xl"></span> {{ data[1] }}
                                </a>
                            {% endwith %}
                        {% endfor %}
                    </div>
                </details>
            </div>
        </div>
    </div>
</nav>
```

### Further Sources of Truth

As we already mentioned, there is a Tailwind-based modal system as well as flashing utility that can be used with our natively provided [script utilities](#socket-and-base-script). And besides that, we do also provide a default **404.html** and **error.html** template as well as a basic framework-specific **tailwind_raw.css** file.

If you are interested in what they look like and how they work, we highly recommend taking a look inside the frameworks **templates** and **static** folders. You can find them inside **src/flaskpp/app** in the [Flask++ repository](https://github.com/GrowVolution/FlaskPlusPlus).

## Get Help

You can simply use `fpp [-h/--help]` to get an overview on how to work with the Flask++ CLI. And if you still have questions, which haven't been answered in this documentation **feel free to join the [discussions](https://github.com/GrowVolution/FlaskPlusPlus/discussions)**.

---

**&copy; GrowVolution e.V. 2025 – Thank you for working with Flask++**
