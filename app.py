from dotenv import load_dotenv
load_dotenv() 

import os
import re

from flask import Flask, request, Response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from server.clients.twilio_client import send_sms

DEBUG_MODE = False

app = Flask(__name__)

# db setup
uri = os.environ.get('DATABASE_URL')
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri

db = SQLAlchemy(app)
migrate = Migrate(app, db)

import server.model

@app.route('/')
def index():
    return "Welcome to Samurai Claus Secret Santa! Normies!"

@app.route('/test-sms')
def test_sms():
    result = send_sms('+17142935548', 'Hello, world!')
    print('result', result) # this is message sid
    return "Sent!"

@app.route('/sms', methods=['POST'])
def sms_reply():
    body = request.values.get('Body', None)
    from_number = request.values.get('From', None)
    message_sid = request.values.get('MessageSid', None)
    print('body', body)
    print('from_number', from_number)
    print('message_sid', message_sid)
    return Response("Message received", 200)

if __name__ == '__main__':
    app.run(debug=DEBUG_MODE)
