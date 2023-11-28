from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.schema import ForeignKey
from sqlalchemy.orm import relationship

from factory import db

class MessageLog(db.Model):
    __tablename__ = 'message_log'

    id = Column(Integer, primary_key=True)

    member_id = Column(
        Integer,
        ForeignKey('member.id'),
        nullable=False,
        unique=False,
        index=True,
    )

    message_sid = Column(String(255), nullable=False, unique=True)
    message_body = Column(Text, nullable=True)
    to_number = Column(String(255), nullable=False)
    from_number = Column(String(255), nullable=False)
    direction = Column(Enum('inbound', 'outbound', name='message_log_direction'), nullable=False)
    status = Column(String(20), nullable=False)
    error_message = Column(Text, nullable=True)

    created = Column(DateTime, default=func.current_timestamp())
    created_ts = Column(
        Integer,
        default=func.date_part('epoch', func.now()),
    )
    last_modified = Column(
        DateTime,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
    last_modified_ts = Column(
        Integer,
        default=func.date_part('epoch', func.now()),
        onupdate=func.date_part('epoch', func.now()),
    )

