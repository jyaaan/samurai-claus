import os
import random
from factory import db

from sqlalchemy import func

from server.model import MessageLog, MessageQueue, Member
from server.constants import MessageQueueStatusEnum, SequenceStageEnum, samurai_claus_images
from server.clients.messaging_client import MessagingClient
from server.openai_utils import get_welcome_message_prompt


TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

class MessageQueueHandler:
    @staticmethod
    def enqueue_received_message(from_number, to_number, body, message_sid, member_id=None):
        """
        Enqueues a received message into the message queue.

        :param from_number: The phone number that sent the message.
        :param to_number: The Twilio phone number that received the message.
        :param body: The body of the message.
        :param message_sid: The SID of the message from Twilio.
        :param member_id: The ID of the member associated with the message.
        """
        try:
            member = (
                db.session.query(Member)
                .filter(Member.phone == from_number)
                .one_or_none()
            )
            member_id = member.id if member else None

            new_message = MessageQueue(
                direction='inbound',
                from_number=from_number,
                to_number=to_number,
                message_body=body,
                message_sid=message_sid,
                member_id=member_id,
                status=MessageQueueStatusEnum.PENDING
            )
            db.session.add(new_message)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

        return new_message.id
    
    @staticmethod
    def enqueue_outbound_message(to_number, body, attach_image=False, member_id=None):
        """
        Enqueues an outbound message into the message queue.

        :param to_number: The phone number to send the message to.
        :param body: The body of the message.
        :param member_id: The ID of the member associated with the message.
        """
        new_message = MessageQueue(
            direction='outbound',
            from_number=TWILIO_PHONE_NUMBER,
            to_number=to_number,
            message_body=body,
            member_id=member_id,
            # status=MessageQueueStatusEnum.HOLD  # Set to HOLD for manual review
            status=MessageQueueStatusEnum.PENDING,
            attach_image=attach_image,
        )
        db.session.add(new_message)
        db.session.commit()

        return new_message.id
    
    @staticmethod
    def process_message_queue():
        """
        Processes pending messages in the queue.
        """
        messages = MessageQueue.query.filter(
            MessageQueue.status.in_([MessageQueueStatusEnum.PENDING])
        ).all()

        # Initialize messaging client if there are outbound messages
        messaging_client = None
        if messages:
            messaging_client = MessagingClient()

        for message in messages:
            try:
                # This effectively locks the row so we don't risk spamming the
                # same message
                message.status = MessageQueueStatusEnum.PROCESSING
                db.session.commit()
                if message.direction == 'outbound':
                    print('outbound')
                    random_image = None
                    if message.attach_image:
                        random_image = random.choice(samurai_claus_images)

                    send_status = messaging_client.send_sms(
                        to_number=message.to_number,
                        body=message.message_body,
                        member_id=message.member_id,
                        media_url=random_image,
                    )
                    message.status = MessageQueueStatusEnum.SENT
                    print(send_status)

                elif message.direction == 'inbound':
                    print('inbound')
                    member = (
                        db.session.query(Member)
                        .filter(Member.phone == message.from_number)
                        .one_or_none()
                    )
                    if not member:
                        raise Exception(f"Member not found for phone number {message.from_number}")

                    messaging_client.receive_sms(
                        body=message.message_body,
                        from_number=message.from_number,
                        to_number=message.to_number,
                        message_sid=message.message_sid,
                        member_id=member.id,
                    )
                    message.status = MessageQueueStatusEnum.RECEIVED

            except Exception as e:
                message.status = MessageQueueStatusEnum.ERROR
                message.error_message = str(e)

            db.session.commit()

    @staticmethod
    def get_message_status():
        pending_statuses = [
            'queued',
            'sending',
            'sent',
        ]
        messages = (
            db.session.query(MessageLog)
            .filter(
                MessageLog.status.in_(pending_statuses),
                MessageLog.direction == 'outbound',
            )
            .all()
        )
    
        messaging_client = None
        if messages:
            messaging_client = MessagingClient()
        
        for message in messages:
            try:
                current_status = messaging_client.get_message_status(message.message_sid)
                if current_status != message.status:
                    message.status = current_status
                elif current_status == 'sent':
                    message.status = 'not_received'
                    message.error_message = 'Message was sent but not received after 2 cycles'
            except Exception as e:
                print(e)
                message.status = 'error'
                message.error_message = str(e)
        db.session.commit()
    
    @staticmethod
    def start_sequences():
        from server.model import Member, Sequence, SeasonalPreference
        from server.clients.openai_client import OpenAIClient
        from server.clients.ai_database_client import AIDatabaseClient
        try:
            sequences = (
                db.session.query(Sequence)
                .filter(
                    Sequence.enabled == True,
                    Sequence.stage == SequenceStageEnum.Initialized,
                )
                .all()
            )
            if not sequences:
                return
            openai_client = OpenAIClient()
            ai_database_client = AIDatabaseClient()
            members = db.session.query(Member).all()
            for sequence in sequences:
                member = next((x for x in members if x.id == sequence.member_id), None)
                secret_santee_name = ai_database_client.get_my_santee_name(member.id)
                sequence.stage = SequenceStageEnum.Participant_Confirmation
                db.session.commit()

                openai_client.send_template_message(
                    message=get_welcome_message_prompt(secret_santee_name),
                    member_id=member.id,
                    to_number=member.phone,
                    attach_image=True,
                )
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e