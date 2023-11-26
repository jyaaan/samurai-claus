from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Integer,
    String,
    ForeignKey,
    Boolean,
    Text,
    func,
)
from sqlalchemy.orm import relationship
from factory import db
from ..constants import SequenceStageEnum

class Sequence(db.Model):
    __tablename__ = 'sequence'

    id = Column(Integer, primary_key=True)
    
    member_id = Column(
        Integer,
        ForeignKey('member.id'),
        nullable=False,
        unique=False,
        index=True,
    )
    member = relationship('Member', back_populates='sequence')

    season = Column(String(4), nullable=False)  # YYYY
    stage = Column(Enum(SequenceStageEnum), nullable=False)

    conversation_summary = Column(Text, nullable=True)
    enabled = Column(Boolean, default=True)

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

    def __init__(self, member_id, season, stage=SequenceStageEnum.Initialized, conversation_summary=None, enabled=True):
        self.member_id = member_id
        self.season = season
        self.stage = stage
        self.conversation_summary = conversation_summary
        self.enabled = enabled
