from flask import Flask
from flask_socketio import SocketIO
from .game_manager import GameManager

socketio = SocketIO()
game_manager = GameManager()

def create_app():
    app = Flask(__name__)

    from . import routes
    app.register_blueprint(routes.bp)

    socketio.init_app(app)
    return app
