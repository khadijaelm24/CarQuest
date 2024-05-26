from flask import Flask
from livereload import Server

from .main.routes import main
from .extensions import mongo
import secrets



   
def create_app():
    app = Flask(__name__)
     # Generate a random secret key
    app.secret_key = secrets.token_hex(16)
    # Initialize livereload server
    server = Server(app)

    # Watch static files for changes
    server.watch('static/css/*.css')
    server.watch('static/js/*.js')
    server.watch('templates/*.html')

    app.config['MONGO_URI'] = 'mongodb://localhost:27017/carquest'

    mongo.init_app(app)
    print(mongo)

    app.register_blueprint(main)

    return app
