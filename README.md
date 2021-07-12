[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Build Status - GitHub](https://github.com/OnGridSystems/erc20_airdrop_cli/workflows/airdrop_pytest/badge.svg)](https://github.com/OnGridSystems/erc20_airdrop_cli/actions?query=workflow%3Aairdrop_pytest)


# Simple CLI app for ERC-20 Airdrops on Ethereum

Allows controllable ERC-20/BEP-20 token airdrops by the given list of recipients and amounts. Simplifies control of sending and eliminates human mistakes. The process of airdrop looks like this:

* fill in the list of recipients and amounts for each
* verify the list, number of recepients and total sum
* generate and sign transactions
* top up sending account with tokens and ETH/BNB
* execute (send) them


## Installation

Clone repositiry. 
Create venv:

```sh
python -m venv venv
```

Install dependencies:
```sh
pip install -r requirements.txt
```


## Using app

At any time run ```./airdrop.py help``` to call help menu.
To show current status ```./airdrop.py show```.

1. ```./airdrop.py init``` to initialize database - creates SQLite fine in the directory
2. ```./airdrop.py import``` to set sender's private key
3. ```./airdrop.py token <token-address> ``` to set token address for airdrop.
4. ```./airdrop.py update``` to update balances and current account's nonce. You can run it anytime.

5. Add recipietns for airdrop, one recipient per command. Amounts are in decimal format. If you specify 1.49, it means you'll send 1490000000000000000 of token units (decimals=18 assumed).

```./airdrop.py add <address> <amount>```  


6. Sign **all** your transactions ```./airdrop.py sign```  

7. Send transactions on the wire, one at a time ```./airdrop.py sign``` - sends **first** SIGNED transaction and it becomes SENT. And now you can check transaction hash in show menu.

8. If the execution was interrupted and the receipt was not received. You can request it:
```./airdrop.py receipt```


#### Testing

```sh
pip install pytest
pytest
```
