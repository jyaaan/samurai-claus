from factory import db
from server.model import MessageLog

class MessageLogClient:

    @staticmethod
    def create_log(member_id, message_sid, message_body, to_number, from_number, direction, status=None):
        """
        Creates a log entry for a Twilio SMS message.

        Args:
            member_id (int): The ID of the member associated with the message.
            message_sid (str): The SID of the message.
            message_body (str): The body of the message.
            to_number (str): The phone number the message was sent to.
            from_number (str): The phone number the message was sent from.
        """
        new_log = MessageLog(
            member_id=member_id,
            message_sid=message_sid,
            message_body=message_body,
            to_number=to_number,
            from_number=from_number,
            direction=direction,
            status=status,
        )
        try:
            db.session.add(new_log)
            db.session.flush()
            return new_log
        except Exception as e:
            print(e)
            db.session.rollback()
            # Handle or log the exception as needed
            raise e
