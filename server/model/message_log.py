from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.schema import ForeignKey

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
    message_body = Column(String(255), nullable=True)
    to_number = Column(String(255), nullable=False)
    from_number = Column(Text, nullable=False)

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

