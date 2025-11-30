from asgiref.wsgi import WsgiToAsgi
from app import create_app

wsgi_app = create_app()
app = WsgiToAsgi(wsgi_app)
