from dotenv import load_dotenv
load_dotenv()

import os

from flask import Flask, request, Response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from server.clients.openai_client import OpenAIClient

# Initialize db and migrate outside of create_app
db = SQLAlchemy()
migrate = None

def create_app():
    app = Flask(__name__)

    # db setup
    uri = os.environ.get('DATABASE_URL')
    if uri and uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = uri

    # Bind db and migrate to the app
    db.init_app(app)
    global migrate
    migrate = Migrate(app, db)

    # Import models
    import server.model


    # Define routes
    @app.route('/')
    def index():
        return "Welcome to Samurai Claus Secret Santa! Normies!"

    @app.route('/test-sms')
    def test_sms():
        # messaging_client = MessagingClient()
        # result = messaging_client.send_sms('+17142935548', 'Hello, world!', 1)
        # print('result', result)  # this is message sid
        from server.message_queue_handler import MessageQueueHandler
        MessageQueueHandler.enqueue_outbound_message(
            to_number='+17142935548',
            body='Hello, world!',
            member_id=1
        )
        return "Sent!"

    @app.route('/sms', methods=['POST'])
    def sms_reply():
        body = request.values.get('Body', None)
        from_number = request.values.get('From', None)
        to_number = request.values.get('To', None)
        message_sid = request.values.get('MessageSid', None)
        print('body', body)
        print('from_number', from_number)
        print('message_sid', message_sid)
        print('to_number', to_number)

        # messaging_client = MessagingClient()
        # messaging_client.receive_sms(
        #     body=body,
        #     from_number=from_number,
        #     to_number=to_number,
        #     message_sid=message_sid,
        #     member_id=1
        # )
        from server.message_queue_handler import MessageQueueHandler
        MessageQueueHandler.enqueue_received_message(
            from_number=from_number,
            to_number=to_number,
            body=body,
            message_sid=message_sid,
        )
        return Response("Message received", 200)

    # @app.route('/test-openai')
    # def test_openai():
    #     client = OpenAIClient()
    #     response = client.get_models()
    #     print(response)
    #     return response
    return app

# Import MessagingClient after creating the app factory
from server.clients.messaging_client import MessagingClient
