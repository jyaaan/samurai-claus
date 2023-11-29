from dotenv import load_dotenv
load_dotenv()

import os

from flask import Flask, request, Response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

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

        from server.message_queue_handler import MessageQueueHandler
        MessageQueueHandler.enqueue_received_message(
            from_number=from_number,
            to_number=to_number,
            body=body,
            message_sid=message_sid,
        )
        return Response("Message received", 200)

    @app.route('/create-member', methods=['POST'])
    def create_member():
        from server.model import Member, Sequence, SeasonalPreference
        from server.constants import SequenceStageEnum
        print('request', request)
        print('request.json', request.json)
        member_name = request.json.get('member_name', None)
        print('member_name', member_name)
        member_phone = request.json.get('member_phone', None)
        print('member_phone', member_phone)

        try:
            new_member = Member(
                name=member_name,
                phone=member_phone,
            )
            db.session.add(new_member)
            db.session.flush()
            new_sequence = Sequence(
                member_id=new_member.id,
                season='2023',
                enabled=False,
                stage=SequenceStageEnum.Initialized,
            )

            db.session.add(new_sequence)
            db.session.flush()
            new_preference = SeasonalPreference(
                member_id=new_member.id,
                season='2023',
            )
            db.session.add(new_preference)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
        return "Created!"

    @app.route('/start-sequences')
    def start_sequences():
        from server.model import Sequence, SeasonalPreference
        sequences = db.session.query(Sequence).all()
        seasonal_preferences = db.session.query(SeasonalPreference).all()
        for sequence in sequences:
            seasonal_preference = next((x for x in seasonal_preferences if x.member_id == sequence.member_id), None)
            if seasonal_preference.secret_santee_id:
                sequence.enabled = True
        db.session.commit()
        return "Started!"
    return app

# Import MessagingClient after creating the app factory
from server.clients.messaging_client import MessagingClient
