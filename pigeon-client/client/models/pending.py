"""
Stores pending message requests
"""

from datetime import datetime
from . import db
from enum import  Enum, auto
from sqlalchemy import create_engine, Column, Integer, String

class Pending(db):
    __tablename__ = 'pending'

    uid = Column(String(80), primary_key=True)
    # email = Column(String(80), nullable=False)
    # username = Column(String(80), nullable=False)
    # password = Column(String(80), nullable=False)
    # age = Column(Integer, nullable=False)
    # contacts = Column(String(200), default="[]", nullable=False)

    def __repr__(self):
        return self.uid