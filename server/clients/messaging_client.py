import os

from twilio.rest import Client as TwilioClient
from server.clients.openai_client import OpenAIClient
from flask import request

from .message_log_client import MessageLogClient

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

class MessagingClient:

    def __init__(self):
        self.client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    def send_sms(self, to_number, body, member_id):
        """
        Send an SMS and log the message.

        Args:
            to_number (str): The destination phone number.
            body (str): The body of the message.
            member_id (int): The ID of the member sending the message.
        """
        print('sending sms?')
        message = self.client.messages.create(
            to=to_number,
            from_=TWILIO_PHONE_NUMBER,
            body=body
        )
        print('message status', message.status)
        # Log the sent message
        MessageLogClient.create_log(
            member_id=member_id,
            message_sid=message.sid,
            message_body=body,
            to_number=to_number,
            from_number=TWILIO_PHONE_NUMBER,
            direction='outbound',
            status=message.status,
        )
        return message.status

    @staticmethod
    def receive_sms(body, from_number, to_number, message_sid, member_id):
        # Log the received message
        # Note: You need to determine how to get member_id for incoming messages
        openai_client = OpenAIClient()
        # from server.message_queue_handler import MessageQueueHandler
        MessageLogClient.create_log(
            member_id=member_id,
            message_sid=message_sid,
            message_body=body,
            to_number=to_number,
            from_number=from_number,
            direction='inbound',
            status='received',
        )
        openai_client.chat_with_samurai_claus(
            user_message=body,
            to_number=from_number,
            member_id=member_id,
        )
        
        
        return "Message received"

    def get_message_status(self, message_sid):
        message = self.client.messages.get(message_sid).fetch()
        return message.status