import json
import peewee as pw
import airdrop as ad
from models import BaseModel, Config, Recipient, Tx


# Note.
# All of addresses are valid the for binance testnet (97).
# But no one transaction will happend due to using pytest monkeypatch in
# the methods send (tranfer) and get receipts.


DBFILE = "db_test.sqlite"


def delete_tables():
    BaseModel._meta.database.init(DBFILE)
    Config.drop_table()
    Recipient.drop_table()
    Tx.drop_table()


def test_create_empty_db():
    BaseModel._meta.database.init(DBFILE)
    db = pw.SqliteDatabase(DBFILE)
    db.connect()
    db.create_tables([Config, Recipient, Tx])

    assert db.table_exists('config')
    assert db.table_exists('recipient')
    assert db.table_exists('tx')
    assert db.get_tables() == ['config', 'recipient', 'tx']
    assert len(Config.select()) == 0
    assert len(Recipient.select()) == 0
    assert len(Tx.select()) == 0

    delete_tables()
    db.close()


def test_init_command():
    db = pw.SqliteDatabase(DBFILE)
    BaseModel._meta.database.init(DBFILE)

    ad.initialize()
    assert db.get_tables() == ['config', 'recipient', 'tx']

    config = Config.get(1)
    assert config.address == "0x0000000000000000000000000000000000000000"
    assert config.private_key == "0000000000000000000000000000000000000000000000000000000000000000"
    assert config.gas_price == 10000000000
    assert config.web3_node == "https://data-seed-prebsc-2-s1.binance.org:8545/"
    assert config.token == "0x0000000000000000000000000000000000000000"
    assert config.current_nonce == 0
    assert config.eth_balance == '0'
    assert config.token_balance == '0'
    delete_tables()
    db.close()


def test_import_command(monkeypatch):
    db = pw.SqliteDatabase(DBFILE)
    BaseModel._meta.database.init(DBFILE)
    db.connect()
    ad.initialize()

    monkeypatch.setattr('builtins.input', 
                        lambda _: "a181ad022696f68244129bc35559d9fe28005d5289fca5961d3ce91dc29d13b3")
    ad.import_key()

    config = Config.get(1)
    assert config.address == "0xB0718e1085E1E34537ff9fdAeeC5Ec1AfFe1872c"
    assert config.private_key == "a181ad022696f68244129bc35559d9fe28005d5289fca5961d3ce91dc29d13b3"

    # check again
    assert config.gas_price == 10000000000
    assert config.web3_node == "https://data-seed-prebsc-2-s1.binance.org:8545/"
    assert config.token == "0x0000000000000000000000000000000000000000"
    assert config.current_nonce == 0
    assert config.eth_balance == '0'
    assert config.token_balance == '0'

    db.close()


def test_token_command():
    db = pw.SqliteDatabase(DBFILE)
    BaseModel._meta.database.init(DBFILE)
    db.connect()

    ad.set_token("0x688ce8a97d5f1193261DB2271f542193D1dFd866")

    config = Config.get(1)
    assert config.token == "0x688ce8a97d5f1193261DB2271f542193D1dFd866"

    db.close()


def test_token_command_with_wrong_address():
    db = pw.SqliteDatabase(DBFILE)
    BaseModel._meta.database.init(DBFILE)
    db.connect()

    token_before = Config.get(1).token

    ad.set_token("0x688ce8a97d5f1193261DB2271f542193D83742323234ac1dFd86693849")
    assert Config.get(1).token == token_before

    ad.set_token("0xce8a97d5f1193261D")
    assert Config.get(1).token == token_before

    ad.set_token("12e8a97d5f1193261D")
    assert Config.get(1).token == token_before

    ad.set_token(12345678901234567890)
    assert Config.get(1).token == token_before

    db.close()


def test_web3_command():
    db = pw.SqliteDatabase(DBFILE)
    BaseModel._meta.database.init(DBFILE)
    db.connect()

    ad.set_node_address("https://data-seed-prebsc-1-s3.binance.org:8545/")

    config = Config.get(1)
    assert config.web3_node == "https://data-seed-prebsc-1-s3.binance.org:8545/"

    db.close()


def test_web3_command_dont_change_to_wrong_address():
    db = pw.SqliteDatabase(DBFILE)
    BaseModel._meta.database.init(DBFILE)
    db.connect()

    wen3_before = Config.get(1).web3_node

    ad.set_node_address("https://")
    assert Config.get(1).web3_node == wen3_before

    ad.set_node_address("https://google.com/")
    assert Config.get(1).web3_node == wen3_before

    ad.set_node_address("abcdefg")
    assert Config.get(1).web3_node == wen3_before

    db.close()


def test_update_command():
    db = pw.SqliteDatabase(DBFILE)
    BaseModel._meta.database.init(DBFILE)
    db.connect()
    config = Config.get(1)

    # before update
    assert config.current_nonce == 0
    assert int(config.eth_balance) == 0
    assert int(config.token_balance) == 0
    assert config.token == "0x688ce8a97d5f1193261DB2271f542193D1dFd866"
    assert config.address == "0xB0718e1085E1E34537ff9fdAeeC5Ec1AfFe1872c"
    assert config.private_key == "a181ad022696f68244129bc35559d9fe28005d5289fca5961d3ce91dc29d13b3"

    # updated
    ad.update_data()
    config = Config.get(1)
    assert config.current_nonce > 0
    assert int(config.eth_balance) > 0
    assert int(config.token_balance) > 0

    db.close()


def test_gasprice_command():
    db = pw.SqliteDatabase(DBFILE)
    BaseModel._meta.database.init(DBFILE)
    db.connect()

    # In 'init' project's default gasprice is 10000000000
    assert Config.get(1).gas_price == 10000000000

    # Let's switch gas price to 20000000002
    ad.set_gas_price(20000000002)
    assert Config.get(1).gas_price == 20000000002

    # Let's switch gas price to 30000000003
    ad.set_gas_price("30000000003")
    assert Config.get(1).gas_price == 30000000003

    # Switching back
    ad.set_gas_price(10000000000)
    assert Config.get(1).gas_price == 10000000000

    db.close()


def test_gasprice_command_with_wrong_value():
    db = pw.SqliteDatabase(DBFILE)
    BaseModel._meta.database.init(DBFILE)
    db.connect()

    gas_before = Config.get(1).gas_price

    ad.set_gas_price(" wrong value ")
    assert Config.get(1).gas_price == gas_before

    ad.set_gas_price("3434340430d")
    assert Config.get(1).gas_price == gas_before

    ad.set_gas_price("0.0000001")
    assert Config.get(1).gas_price == gas_before

    db.close()


def test_add_command():
    db = pw.SqliteDatabase(DBFILE)
    BaseModel._meta.database.init(DBFILE)
    db.connect()

    adr1, amount1 = ("0x754a2bAe5b5eEE723409A1d0013377927Fd5F539", 1.234567890123456789)
    adr2, amount2 = ("0x754a2bAe5b5eEE723409A1d0013377927Fd5F539", 0.123456789012345678)
    adr3, amount3 = ("0x754a2bAe5b5eEE723409A1d0013377927Fd5F539", 0.012345678901234567)

    # before
    assert len(Recipient.select()) == 0
    assert len(Tx.select()) == 0

    # add one
    ad.add_recepient(adr1, amount1)
    assert len(Recipient.select()) == 1
    recipient1 = Recipient.get(1)
    assert recipient1.address == adr1
    assert float(recipient1.amount) == amount1

    assert len(Tx.select()) == 1
    tx1 = Tx.get(1)
    assert tx1.raw_tx == ""
    assert tx1.signed_tx == b''
    assert tx1.tx_hash == b''
    assert tx1.tx_receipt == ""
    assert tx1.nonce == None
    assert tx1.recipient.address == "0x754a2bAe5b5eEE723409A1d0013377927Fd5F539"
    assert tx1.status == 'NEW'


    # add two more
    ad.add_recepient(adr2, amount2)
    ad.add_recepient(adr3, amount3)
    assert len(Recipient.select()) == 3
    recipient2 = Recipient.get(2)
    recipient3 = Recipient.get(3)
    assert recipient2.address == adr2
    assert float(recipient2.amount) == amount2
    assert recipient3.address == adr3
    assert float(recipient3.amount) == amount3

    assert len(Tx.select()) == 3
    assert Tx.get(2).status == 'NEW'
    assert Tx.get(3).status == 'NEW'
    assert bool(Tx.get(2).signed_tx) == False

    db.close()


def test_sign_command():
    db = pw.SqliteDatabase(DBFILE)
    BaseModel._meta.database.init(DBFILE)
    db.connect()

    nonce_before = Config.get(1).current_nonce
    ad.sign()

    tx1, tx2, tx3 = Tx.select()
    assert tx1.status == 'SIGNED'
    assert tx2.status == 'SIGNED'
    assert tx3.status == 'SIGNED'
    assert tx1.nonce == nonce_before
    assert tx2.nonce == nonce_before + 1
    assert tx3.nonce == nonce_before + 2
    assert json.loads(tx1.raw_tx.replace("\'", "\""))['from'] == Config.get(1).address
    assert json.loads(tx2.raw_tx.replace("\'", "\""))['from'] == Config.get(1).address
    assert json.loads(tx3.raw_tx.replace("\'", "\""))['from'] == Config.get(1).address
    assert json.loads(tx1.raw_tx.replace("\'", "\""))['to'] == Config.get(1).token
    assert json.loads(tx2.raw_tx.replace("\'", "\""))['to'] == Config.get(1).token
    assert json.loads(tx3.raw_tx.replace("\'", "\""))['to'] == Config.get(1).token
    assert bool(json.loads(tx1.raw_tx.replace("\'", "\""))['data']) == True
    assert bool(json.loads(tx2.raw_tx.replace("\'", "\""))['data']) == True
    assert bool(json.loads(tx3.raw_tx.replace("\'", "\""))['data']) == True
    assert bool(tx1.signed_tx) == True
    assert bool(tx2.signed_tx) == True
    assert bool(tx3.signed_tx) == True

    db.close()


def test_send_command(monkeypatch):
    db = pw.SqliteDatabase(DBFILE)
    BaseModel._meta.database.init(DBFILE)
    db.connect()

    monkeypatch.setattr('airdrop.send_raw_tx',
                        lambda _, __: bytes.fromhex('593ebcf5700420b1'))
    monkeypatch.setattr('airdrop.get_tx_receipt',
                        lambda _, __: {'blockNumber': 100, 'status': 1})
    ad.send()

    tx = Tx.get(1)
    assert tx.tx_hash == bytes.fromhex('593ebcf5700420b1')
    assert tx.status == 'MINED'
    assert tx.tx_receipt == "{'blockNumber': 100, 'status': 1}"

    db.close()

    # db cleanup
    delete_tables()


def test_dont_update_without_token(monkeypatch):
    db = pw.SqliteDatabase(DBFILE)
    BaseModel._meta.database.init(DBFILE)

    ad.initialize()
    monkeypatch.setattr('builtins.input', 
                        lambda _: "a181ad022696f68244129bc35559d9fe28005d5289fca5961d3ce91dc29d13b3")
    ad.import_key()

    nonce_before = Config.get(1).current_nonce
    token_balance_before = Config.get(1).token_balance

    ad.update_data()
    assert nonce_before == Config.get(1).current_nonce
    assert token_balance_before == Config.get(1).token_balance

    db.close()
    delete_tables()


def test_add_with_wrong_inputs_dont_adds_data_to_db():
    db = pw.SqliteDatabase(DBFILE)
    BaseModel._meta.database.init(DBFILE)

    ad.initialize()

    adr1, amount1 = ("0x0000000000000000000000000000hd1100000000", 1.2345)
    adr2, amount2 = ("0x754a2bAe5b5eEE723409A1d0013377927Fd5F539", "")
    adr3, amount3 = ("0x754a2bAe5b5eEE723409A1d0013377927Fd5F539", "0.00000000000000000001")

    # before
    assert len(Recipient.select()) == 0
    assert len(Tx.select()) == 0

    ad.add_recepient(adr1, amount1)
    ad.add_recepient(adr2, amount2)
    ad.add_recepient(adr3, amount3)

    # after
    assert len(Recipient.select()) == 0
    assert len(Tx.select()) == 0

    db.close()
    delete_tables()
