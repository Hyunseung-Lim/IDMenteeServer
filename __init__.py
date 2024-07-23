from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta
from os.path import join, dirname, realpath

db = SQLAlchemy()

def create_app():
    app = Flask(__name__) # creates the Flask instance, __name__ is the name of the current Python module
    CORS(app)
    
    app.config['SECRET_KEY'] = 'hyunseung' # it is used by Flask and extensions to keep data safe
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db' #it is the path where the SQLite database file will be saved
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 

    # This is the directory that flask-file-upload saves files to. Make sure the UPLOAD_FOLDER is the same as Flasks's static_folder or a child. For example:
    app.config["UPLOAD_FOLDER"] = join(dirname(realpath(__file__)), "static/uploads")    
    app.config["ALLOWED_EXTENSIONS"] = ["jpg", "png", "mov", "mp4", "mpg"]
    app.config["MAX_CONTENT_LENGTH"] = 1000 * 1024 * 1024  # 1000mb
    
    app.config['JWT_SECRET_KEY'] = 'hyunseung'
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
    jwt = JWTManager(app)
    
    db.init_app(app) # Initialiaze sqlite database
    
    from main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    return app