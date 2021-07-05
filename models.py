import peewee as pw


DBFILE = 'db.sqlite'
db = pw.SqliteDatabase(DBFILE)


class BaseModel(pw.Model):
    class Meta:
        database = db


class Config(BaseModel):
    address = pw.CharField(max_length=42)
    private_key = pw.CharField(max_length=64)
    gas_price = pw.IntegerField()
    web3_node = pw.CharField(max_length=255)
    
    current_nonce = pw.IntegerField(default=0)
    eth_balance = pw.CharField(default=0)
    token_balance = pw.CharField(default=0)


class Recipient(BaseModel):
    address = pw.CharField(max_length=42)
    amount = pw.DecimalField()


class Tx(BaseModel):

    choices = (
        ('NEW', 'NEW'),
        ('SIGNED', 'SIGNED'),
        ('SENT', 'SENT'),
        ('MINED', 'MINED'),
    )

    raw_tx = pw.TextField(default="")
    signed_tx = pw.BlobField(default="")
    tx_hash = pw.BlobField(default="")
    tx_receipt = pw.TextField(default="")

    nonce = pw.IntegerField(null=True)
    recipient = pw.ForeignKeyField(Recipient, backref='txes')
    status = pw.CharField(choices=choices)
