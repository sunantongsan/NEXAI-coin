# nexai_chain.py
import hashlib

DECIMALS = 8
UNIT = 10 ** DECIMALS
FEE = int(0.00001 * UNIT)   # ค่าธรรมเนียม 0.00001 NXI

class Chain:
    def __init__(self):
        self.balances = {}
        self.ledger = []

    def mint(self, address, amount):
        amount_units = int(amount * UNIT)
        self.balances[address] = self.balances.get(address, 0) + amount_units

    def balance_of(self, address):
        return self.balances.get(address, 0) / UNIT

    def transfer(self, sender, recipient, amount):
        amount_units = int(amount * UNIT)

        # ตรวจยอด
        if self.balances.get(sender, 0) < amount_units + FEE:
            raise ValueError("ยอดเงินไม่พอ")

        # ทำธุรกรรม
        self.balances[sender] -= amount_units + FEE
        self.balances[recipient] = self.balances.get(recipient, 0) + amount_units

        txid = hashlib.sha256(f"{sender}->{recipient}:{amount}".encode()).hexdigest()
        self.ledger.append(txid)
        return txid
