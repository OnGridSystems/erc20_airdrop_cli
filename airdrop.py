#!/usr/bin/env python

import sys
import json
from web3 import Web3
from web3.exceptions import ContractLogicError, BadFunctionCallOutput
from peewee import fn
from peewee import OperationalError

from models import (
    db,
    Recipient,
    Config,
    Tx,
)

from pretty_table import print_pretty_table


def send_raw_tx(web3_endpoint, signed_tx):
    w3 = Web3(Web3.HTTPProvider(web3_endpoint, request_kwargs={"timeout": 20}))
    return w3.eth.send_raw_transaction(signed_tx)


def get_tx_receipt(web3_endpoint, tx_hash):
    w3 = Web3(Web3.HTTPProvider(web3_endpoint, request_kwargs={"timeout": 20}))
    return w3.eth.wait_for_transaction_receipt(tx_hash)


def initialize():
    db.connect()
    db.create_tables([Config, Recipient, Tx])
    Config.create(address="0x0000000000000000000000000000000000000000",
                  private_key="0000000000000000000000000000000000000000000000000000000000000000",
                  gas_price=10000000000,
                  web3_node="https://data-seed-prebsc-2-s1.binance.org:8545/",
                  token="0x0000000000000000000000000000000000000000")
    print('Db was created!')


def import_key():
    private_key = input("Paste your private key in hex format: ")

    w3 = Web3(Web3.HTTPProvider(Config.get(1).web3_node, request_kwargs={"timeout": 20}))
    address = w3.eth.account.from_key(private_key).address
    config = Config.get(1)
    config.address = address
    config.private_key = private_key
    config.save()
    print(f'Sender address: {address}')


def set_token(token_address):
    if not Web3.isChecksumAddress(token_address):
        print('Wrong token address. Try again.')
        return

    config = Config.get(1)
    config.token = token_address
    config.save()
    print(f"Now token for airdrop is {token_address}")


def set_node_address(node_address):
    try:
        w3 = Web3(Web3.HTTPProvider(node_address, request_kwargs={"timeout": 20}))
        assert w3.isConnected() == True
    except AssertionError:
        print('Wrong node URL or connection error. Try again.')
        return
    config = Config.get(1)
    config.web3_node = node_address
    config.save()
    print(f'New node address: {node_address}')


def update_data():
    config = Config.get(1)
    # balances
    w3 = Web3(Web3.HTTPProvider(config.web3_node, request_kwargs={"timeout": 20}))
    config.eth_balance = w3.eth.get_balance(config.address)
    with open("tokens_abi/ERC20.abi", "r") as file:
        erc20_abi = json.load(file)

    token_contract = w3.eth.contract(address=Web3.toChecksumAddress(config.token), abi=erc20_abi)
    try:
        config.token_balance = token_contract.functions.balanceOf(config.address).call()
    except BadFunctionCallOutput:
        print("Error. Can't update token address. Check token address.")
        return

    # nonce
    config.current_nonce = w3.eth.get_transaction_count(config.address)
    config.save()

    # update tx nonces
    txs = Tx.select().where(Tx.status == "SIGNED").order_by(Tx.nonce)
    if txs and (txs[0].nonce != config.current_nonce):
        nonce = config.current_nonce
        for tx in txs:
            tx.nonce = nonce
            updated_raw_tx = json.loads(tx.raw_tx.replace("\'", "\""))
            updated_raw_tx['nonce'] = nonce
            tx.raw_tx = updated_raw_tx
            tx.signed_tx = w3.eth.account.sign_transaction(updated_raw_tx,
                                                           config.private_key).rawTransaction            
            tx.save()
            nonce += 1
    print('Balance and nonce have been updated.')


def show():
    config = Config.get(1)
    print(f"Sender address: {config.address}")
    print(f"Sender ETH balance: {config.eth_balance} Wei")
    print(f"Token address: {config.token}")
    print(f"Token balance:  {config.token_balance} Wei")
    print(f"Sender nonce: {config.current_nonce}")
    print(f"Web3 endpoint: {config.web3_node}")
    print(f"Gas Price: {config.gas_price}\n")

    print(f"Recipients:")
    token_sum = Recipient.select(fn.SUM(Recipient.amount))[0].amount
    recipients = Recipient.select()

    header = [['Address', 'Tokens', 'Nonce', 'Status', 'Tx Hash']]
    values = [
        [rec.address,
         str(rec.amount),
         str(rec.txes[0].nonce),
         rec.txes[0].status,
         rec.txes[0].tx_hash.hex()] for rec in recipients
    ]
    data_to_print = header + values
    print_pretty_table(data_to_print)

    print(f"\nTotal {len(recipients)} recipients, {token_sum} ERC-20 Tokens.\n")


def add_recepient(recipient_address, amount):
    if not Web3.isChecksumAddress(recipient_address):
        print('Wrong recipient address. Try again.')
        return
    try:
        float(amount)
        assert float(amount) * 10**18 >= 1
    except ValueError:
        print('Wrong amount')
        return
    except AssertionError:
        print('Too less amount')
        return

    recipient = Recipient.create(address=recipient_address, amount=amount)
    Tx.create(recipient=recipient, status="NEW")
    print(f"{recipient_address} was added with amount {amount}!")


def set_gas_price(new_gas_price):
    try:
        int(new_gas_price)
    except ValueError:
        print("Wrong gas value. Try again")
        return
    config = Config.get(1)
    config.gas_price = new_gas_price
    config.save()
    print(f'New gas price {new_gas_price}')


def sign():
    config = Config.get(1)
    w3 = Web3(Web3.HTTPProvider(config.web3_node, request_kwargs={"timeout": 20}))
    with open("tokens_abi/ERC20.abi", "r") as file:
        erc20_abi = json.load(file)
    token = w3.eth.contract(address=Web3.toChecksumAddress(config.token), abi=erc20_abi)
    nonce = config.current_nonce

    recipients = Recipient.select(Recipient, Tx).join(Tx).where(Tx.status == 'NEW')
    for recipient in recipients:
        tx = recipient.txes[0]
        try:
            raw_tx = token.functions.transfer(
                                recipient.address,
                                int(float(recipient.amount) * 10**18),
                                ).buildTransaction({
                                                    "from": config.address,
                                                    "nonce": nonce,
                                                    "gasPrice": config.gas_price,
                                                    })
        except ValueError:
            print('Not enough ETH or Token balance. Fill your balance and try again.')
            return
        tx.raw_tx = raw_tx

        signed_tx = w3.eth.account.sign_transaction(raw_tx, config.private_key).rawTransaction
        tx.signed_tx = signed_tx
        tx.nonce = nonce
        tx.status = 'SIGNED'
        tx.save()

        nonce += 1
    print('TXs have been signed.')


def send():
    config = Config.get(1)
    w3 = Web3(Web3.HTTPProvider(config.web3_node, request_kwargs={"timeout": 20}))

    sending_tx = Tx.select().where(Tx.status == 'SIGNED').order_by(Tx.nonce, Tx.id).first()

    try:
        w3.eth.call(json.loads(sending_tx.raw_tx.replace("\'", "\"")))
    except ContractLogicError:
        print("""Contract logic error (probably insufficient token balance). Sending aborted.""")
        return
    except AttributeError:
        print("Nothing to send.")
        return

    try:
        tx_hash = send_raw_tx(config.web3_node, sending_tx.signed_tx)
    except ValueError as e:
        if str(e) == "{'code': -32000, 'message': 'insufficient funds for gas * price + value'}":
            print('Not enough ETH Balance. Fill your balance and try again.')
        elif str(e) == "{'code': -32000, 'message': 'nonce too low'}":
            print("Needs to update account nonce. Use command 'update'.")
        return
    except AttributeError as e:
        print(e)
        print("Nothing to send.")
        return
    sending_tx.tx_hash = tx_hash
    sending_tx.status = 'SENT'
    sending_tx.save()
    print(f"Tx with {sending_tx.nonce} nonce was sent. Waiting for receipt...")

    config.current_nonce += 1
    config.save()

    sending_tx.tx_receipt = get_tx_receipt(config.web3_node, tx_hash)
    sending_tx.status = "MINED"
    sending_tx.save()
    print('Tx was successfully mined!')


def get_receipt():
    config = Config.get(1)
    w3 = Web3(Web3.HTTPProvider(config.web3_node, request_kwargs={"timeout": 20}))

    tx = Tx.select().where(Tx.status == "SENT").order_by(Tx.id).first()
    tx.tx_receipt= w3.eth.wait_for_transaction_receipt(tx.tx_hash)
    tx.status = "MINED"
    tx.save()
    print(f"Tx with nonce {tx.nonce} was successfully mined!")


def help():
    print("""
    init                    Starts project, calls at once.
    import                  Import admin private key, returns user address.
    token <address>         Set token address for airdrop.
    web3 <web_address>      Specify web3 node address.
    update                  Retrievs latest balances and user nonce. Also updates nonce for 'SIGNED' tx, if necceessary.
    show                    Shows current status.
    add <address> <amount>  Adds recipient with amount.
    gasprice <amount>       Set new <amount> gasprice value for tx in Wei.
    sign                    Signs all transactions.
    send                    Sedns first signed tx.
    receipt                 Queries receipt for transaction with status 'SENT'
    help                    Returns this info
          """)


command_dict = {
    "init": initialize,
    'import': import_key,
    'token': set_token,
    "web3": set_node_address,
    "update": update_data,
    "show": show,
    "add": add_recepient,
    "gasprice": set_gas_price,
    "sign": sign,
    "send": send,
    "receipt": get_receipt,
    "help": help,
}


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Command reqired. Input 'help' for additional info.")
    else:
        # parse command
        try:
            command = sys.argv[1]
            args = sys.argv[2:]
        except IndexError:
            print("Invalid command. Try again or input 'help' for help.")

        # execute command
        try:
            command_dict[command](*args)
        except TypeError:
            print(f'Please specify all neccessary argument(s) for command "{command}"')
        except KeyError:
            print("Invalid command. Try again or input 'help' for help.")
        except OperationalError:
            print("Invalid command. Try again or input 'help' for help.")
