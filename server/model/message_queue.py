from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Integer,
    String,
    Text,
    Boolean,
    ForeignKey,
    func,
)
from sqlalchemy.orm import relationship
from factory import db

from ..constants import MessageQueueStatusEnum

class MessageQueue(db.Model):
    __tablename__ = 'message_queue'

    id = Column(Integer, primary_key=True)

    direction = Column(Enum('inbound', 'outbound', name='message_direction'), nullable=False)
    from_number = Column(String(100), nullable=False)
    to_number = Column(String(100), nullable=False)
    message_body = Column(Text, nullable=False)
    message_sid = Column(String(100), nullable=True)
    status = Column(Enum(MessageQueueStatusEnum), nullable=False, default=MessageQueueStatusEnum.PENDING)
    hold = Column(Boolean, default=False)
    attach_image = Column(Boolean, default=False, nullable=False)

    member_id = Column(
        Integer,
        ForeignKey('member.id'),
        nullable=True,
        index=True
    )

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
