from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Text,
    DateTime,
    func,
)
from sqlalchemy.schema import UniqueConstraint

from factory import db

class SeasonalPreference(db.Model):
    __tablename__ = 'seasonal_preference'

    id = Column(Integer, primary_key=True)
    
    member_id = Column(
        Integer,
        ForeignKey('member.id'),
        nullable=False,
        unique=False,
        index=True,
    )

    season = Column(String(4), nullable=False)  # YYYY

    wishlist = Column(Text, nullable=True)

    # This is the member for whom this member is the secret santa
    secret_santee_id = Column(
        Integer, ForeignKey('member.id'), nullable=True
    )

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

    __table_args__ = (
        UniqueConstraint('member_id', 'season', name='member_id_season_unique_idx_sp'),
        UniqueConstraint('secret_santee_id', 'season', name='secret_santee_id_season_unique_idx_sp')
    )

    def __init__(self, member_id, season, wishlist=None, secret_santee_id=None):
        self.member_id = member_id
        self.season = season
        self.wishlist = wishlist
        self.secret_santee_id = secret_santee_id
