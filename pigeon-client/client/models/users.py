from datetime import datetime
from . import db
from enum import  Enum, auto
from sqlalchemy import create_engine, Column, Integer, String
class Users(db):
    __tablename__ = 'users'

    uid = Column(String(80), primary_key=True)
    public_key = Column(String, nullable=False)
    # email = Column(String(80), nullable=False)
    # username = Column(String(80), nullable=False)
    # password = Column(String(80), nullable=False)
    # age = Column(Integer, nullable=False)
    # contacts = Column(String(200), default="[]", nullable=False)

    def to_dict(self):
        return {
            'id': self.uid,
            'key': self.public_key
        }

    def get(self, var):
        if var =='uid':
            return self.uid
        # if var =='username':
        #     return self.email
        # if var =='email':
        #     return self.email
        
    # def check_login(self, email):
    #     #Testing getting data from email
    #     return self.query.get(email)
