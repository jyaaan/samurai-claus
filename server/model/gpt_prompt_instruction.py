from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    func,
)

from factory import db

class GPTPromptInstruction(db.Model):
    __tablename__ = 'gpt_prompt_instruction'

    id = Column(Integer, primary_key=True)
    key = Column(String(255), unique=True, nullable=False)
    prompt_template = Column(Text, nullable=False)
    description = Column(Text)

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

    def __init__(self, key, prompt_template, description=None):
        self.key = key
        self.prompt_template = prompt_template
        self.description = description
