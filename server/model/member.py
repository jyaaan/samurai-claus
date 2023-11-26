from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from factory import db


class Member(db.Model):
    __tablename__ = 'member'

    id = Column(Integer, primary_key=True)

    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True, unique=True)
    phone = Column(Text, nullable=False, unique=True)
    address = Column(Text, nullable=True)

    sequences = relationship('Sequence', backref='member')

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

