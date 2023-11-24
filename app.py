import os
import re

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from database import db

DEBUG_MODE = False

app = Flask(__name__)

# db setup
uri = os.environ.get('DATABASE_URL')
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = uri

@app.route('/')
def index():
    return "Welcome to Samurai Claus Secret Santa! Normies!"

if __name__ == '__main__':
    app.run(debug=DEBUG_MODE)
