import airdrop as ad
from decimal import Decimal


def test_add_recepient():
    ad.Recipient.delete().execute()
    ad.add_recipient({"address": "bla", "amount": Decimal('12.34')})
    ad.add_recipient({"address": "bla", "amount": Decimal('234.56')})
    assert ad.Recipient.get_by_id(1).address == "bla"
    assert ad.Recipient.get_by_id(1).amount == Decimal('12.34')
    assert ad.Recipient.get_by_id(2).address == "bla"
    assert ad.Recipient.get_by_id(2).amount == Decimal('234.56')


def test_prepare_txes():
    ad.Recipient.delete().execute()
    rcpt1 = ad.Recipient.create(address="weret", amount=Decimal('234.56'))
    rcpt2 = ad.Recipient.create(address="wereg", amount=Decimal('234.56'))
    rcpt3 = ad.Recipient.create(address="wereu", amount=Decimal('234.56'))
    ad.Tx.create(recipient=rcpt1, nonce=1, status=ad.Tx.TxStatus.OCR)
    ad.Tx.create(recipient=rcpt2, nonce=1, status=ad.Tx.TxStatus.OCR)
    ad.Tx.create(recipient=rcpt3, nonce=1, status=ad.Tx.TxStatus.OCR)
    ad.prepare_txes({})
