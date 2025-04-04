import os
from dotenv import load_dotenv
from flask import Flask
from flask_socketio import SocketIO


socketio = SocketIO()

def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

    from . import routes
    app.register_blueprint(routes.bp)

    socketio.init_app(app)
    return app