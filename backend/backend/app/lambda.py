from .main import app
from mangum import Mangum


def handler(event, context):
    asgi_handler = Mangum(app)
    return asgi_handler(event, context)
