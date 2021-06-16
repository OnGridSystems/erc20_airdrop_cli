from enum import Enum
import peewee as pw
from enumfield import EnumField
from web3 import Web3
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
    class TxStatus(Enum):
        WAITING = 1
        READY_TO_SEND = 2
        UPLOADING = 3
        OCR = 4
        DONE = 5

    nonce = pw.IntegerField()
    recipient = pw.ForeignKeyField(Recipient, backref='txes')
    status = EnumField(TxStatus)


db.connect()
db.create_tables([Config, Recipient, Tx])


def add_recipient(args):
    Recipient.create(address=args['address'], amount=args['amount'])


def show(args):
    print('show current state', args)


def prepare_txes(args):
    for i in Recipient.select(Recipient.address).join(Tx, on=(Tx.recipient == Recipient.id)):
        print("ttt", i)


def init(args):
    print('Initializing...')

    web3_url = Config.get_or_none(Config.name == 'web3_url')
    if web3_url:
        w3 = Web3(Web3.HTTPProvider(web3_url))
    else:
        web3_url = input("Enter web3 node url: ")
        Config(name='web3_url', value=web3_url).save()
        w3 = Web3(Web3.HTTPProvider(web3_url))

    if not w3.isConnected():
        print('Web3 is not connected')

    if not Config.get_or_none(Config.name == 'priv_key'):
        priv_key = input("Enter private key in hex: ")
        sender = w3.eth.account.from_key(priv_key)
        print(f"Account: {sender.address}")
        Config(name='priv_key', value=priv_key).save()
        Config(name='sender_addr', value=sender.address).save()

    if not Config.get_or_none(Config.name == 'token_contract'):
        token_contract = input("Enter token contract: ")
        Config(name='token_contract', value=token_contract).save()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Make ERC-20 tokens airdrop')
    subparsers = parser.add_subparsers()

    parser_init = subparsers.add_parser('init', help='Initialize db')
    parser_init.set_defaults(func=init)

    parser_add_recipient = subparsers.add_parser('add', help='Add recipient')
    parser_add_recipient.add_argument('to', nargs='?', type=str)
    parser_add_recipient.add_argument('amount', nargs='?', type=float)
    parser_add_recipient.set_defaults(func=add_recipient)

    parser_show = subparsers.add_parser('show', help='show application stats')
    parser_show.set_defaults(func=show)

    parser_prepare = subparsers.add_parser('prepare', help='Prepare txes')
    parser_prepare.set_defaults(func=prepare_txes)

    args = parser.parse_args()
    args.func(args)
