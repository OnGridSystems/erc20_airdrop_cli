import peewee as pw

from models import (
    db,
    Recipient,
    Config,
    Tx,
)

db.connect()
db.create_tables([Config, Recipient, Tx])


def generate_txes():
    recipients = Recipient.select(
        Recipient.id,
        Recipient.amount,
        Recipient.address
    ).where(
        Recipient.id.not_in(Tx.select(Tx.recipient_id))
    ).execute()
    for recipient in recipients:
        Tx.create(nonce=0, recipient_id=recipient.id, status="WAITING")


if __name__ == '__main__':
    generate_txes()
