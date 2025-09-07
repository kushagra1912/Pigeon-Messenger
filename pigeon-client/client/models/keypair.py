from datetime import datetime
from . import db
from enum import  Enum, auto
from sqlalchemy import create_engine, Column, Integer, String

class KeyPair(db):
    __tablename__ = 'keypair'

    id = Column(Integer, primary_key=True)
    private_key = Column(String, nullable=False) 
    public_key = Column(String, nullable=False)
    # email = Column(String(80), nullable=False)
    # username = Column(String(80), nullable=False)
    # password = Column(String(80), nullable=False)
    # age = Column(Integer, nullable=False)
    # contacts = Column(String(200), default="[]", nullable=False)