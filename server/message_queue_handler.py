import os
from factory import db

from sqlalchemy import func

from server.model import MessageLog, MessageQueue, Member
from server.constants import MessageQueueStatusEnum
from server.clients.messaging_client import MessagingClient


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
    def enqueue_outbound_message(to_number, body, member_id=None):
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
                    send_status = messaging_client.send_sms(
                        to_number=message.to_number,
                        body=message.message_body,
                        member_id=message.member_id,
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