from sqlalchemy import (
    Column,
    Integer,
    String,
    Text
)

from app import db


class Member(db.Model):
    __tablename__ = 'member'

    id = Column(Integer, primary_key=True)

    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True, unique=True)
    phone = Column(Text, nullable=False, unique=True)

