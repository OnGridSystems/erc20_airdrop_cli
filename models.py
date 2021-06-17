from enum import Enum

import peewee as pw

from enumfield import EnumField

DBFILE = 'db.sqlite'
db = pw.SqliteDatabase(DBFILE)


class BaseModel(pw.Model):
    class Meta:
        database = db


class Config(BaseModel):
    name = pw.CharField(max_length=255)
    value = pw.CharField(max_length=255)


class Recipient(BaseModel):
    address = pw.CharField(max_length=42)
    amount = pw.DecimalField()


class Tx(BaseModel):

    choises = {
        'WAITING': 1,
        'READY_TO_SEND': 2,
        'UPLOADING': 3,
        'OCR': 4,
        'DONE': 5,
    }

    nonce = pw.IntegerField()
    recipient = pw.ForeignKeyField(Recipient, backref='txes')
    status = EnumField(choices=choises)
