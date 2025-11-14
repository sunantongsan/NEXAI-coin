# NEXAI (NXI) minimal prototype
# - total supply: 10_000_000_000 NXI
# - decimals: 8 (internal integer units)
# - fee per tx: 0.00001 NXI
# - self-validation: deterministic stake-weighted validators chosen from holders

import hashlib
import math
from collections import defaultdict, namedtuple

DECIMALS = 8
UNIT = 10 ** DECIMALS
TOTAL_SUPPLY = 10_000_000_000 * UNIT  # 10B NXI in base units
FEE_UNITS = int(0.00001 * UNIT)       # fee per transaction in base units
MAX_VALIDATORS = 5                    # how many validators participate per tx (tunable)

LedgerEntry = namedtuple("LedgerEntry", ["txid", "sender", "recipient", "amount", "fee", "validators"])

def sha256_hex(x: str) -> str:
    return hashlib.sha256(x.encode()).hexdigest()

class NEXAI:
    def __init__(self, name="NEXAI", ticker="NXI"):
        self.name = name
        self.ticker = ticker
        self.balances = defaultdict(int)  # address -> units
        self.ledger = []                  # list of LedgerEntry
        self.total_supply = TOTAL_SUPPLY
        self.nonces = defaultdict(int)    # address -> nonce for deterministic coin-id generation

    # Mint (one-time); for prototype we allow mint to a given address
    def mint(self, to_address: str, amount_nxi: float):
        amount_units = int(amount_nxi * UNIT)
        assert amount_units <= self.total_supply - sum(self.balances.values()), "not enough supply"
        self.balances[to_address] += amount_units

    # Helper: pretty balance
    def balance_of(self, address: str) -> float:
        return self.balances[address] / UNIT

    # Deterministic "coin id" generator for an address (lazy, generates n ids)
    # Does NOT create persistent objects for all coins; it's deterministic from address+index
    def generate_coin_ids(self, address: str, n: int):
        start = self.nonces.get(address, 0)
        ids = []
        for i in range(start, start + n):
            ids.append(sha256_hex(f"{address}:{i}")[:16])
        # do not advance nonce here (ids are deterministic); only advance if you want to "consume" them
        return ids

    # Deterministic stake-weighted selection of validators
    # Use tx_hash as seed to pick up to k validators from current holders
    def select_validators(self, tx_hash: str, k: int = MAX_VALIDATORS):
        # get holders with positive balance
        holders = [(addr, bal) for addr, bal in self.balances.items() if bal > 0]
        if not holders:
            return []

        total_stake = sum(b for _, b in holders)
        # create deterministic pseudo-random stream from tx_hash
        chosen = []
        i = 0
        while len(chosen) < min(k, len(holders)):
            h = sha256_hex(tx_hash + str(i))
            # map hash to a number in [0, total_stake)
            r = int(h, 16) % total_stake
            # pick holder where cumulative stake > r
            cum = 0
            for addr, bal in holders:
                cum += bal
                if r < cum:
                    if addr not in chosen:
                        chosen.append(addr)
                    break
            i += 1
            # safety in case of pathological
            if i > k * 20:
                break
        return chosen

    # Transfer: sender -> recipient amount_nxi (float)
    def transfer(self, sender: str, recipient: str, amount_nxi: float):
        amount_units = int(amount_nxi * UNIT)
        if amount_units <= 0:
            raise ValueError("amount must be positive")
        if self.balances[sender] < amount_units + FEE_UNITS:
            raise ValueError("insufficient balance to cover amount + fee")

        # create txid deterministically
        tx_payload = f"{sender}->{recipient}:{amount_units}:{len(self.ledger)}:{sha256_hex(sender+recipient)}"
        txid = sha256_hex(tx_payload)

        # select validators deterministically
        validators = self.select_validators(txid)

        # apply transfer and fee
        self.balances[sender] -= (amount_units + FEE_UNITS)
        self.balances[recipient] += amount_units

        # distribute fee to validators proportionally to their stake
        if validators:
            total_validator_stake = sum(self.balances[v] for v in validators)
            # if a validator has zero (edge), split equally
            if total_validator_stake == 0:
                per = FEE_UNITS // len(validators)
                for v in validators:
                    self.balances[v] += per
            else:
                distributed = 0
                for v in validators[:-1]:
                    part = (self.balances[v] * FEE_UNITS) // total_validator_stake
                    self.balances[v] += part
                    distributed += part
                # remaining to last
                self.balances[validators[-1]] += (FEE_UNITS - distributed)
        else:
            # if no validators, fee goes to burn (reduce total supply)
            self.total_supply -= FEE_UNITS

        # Record ledger
        entry = LedgerEntry(txid=txid, sender=sender, recipient=recipient,
                            amount=amount_units, fee=FEE_UNITS, validators=validators)
        self.ledger.append(entry)
        return txid, validators

# ---------------- Example usage ----------------
if __name__ == "__main__":
    chain = NEXAI()
    # initial mint: give all supply to a genesis address
    GENESIS = "nexai:genesis"
    chain.mint(GENESIS, 10_000_000_000.0)  # 10B NXI to genesis

    # distribute to two users
    alice = "wallet:alice"
    bob = "wallet:bob"
    # send from genesis
    txid1, val1 = chain.transfer(GENESIS, alice, 1_000_000.0)   # send 1M NXI
    txid2, val2 = chain.transfer(GENESIS, bob, 500_000.0)      # send 500k NXI

    print("Balances:")
    print("genesis", chain.balance_of(GENESIS))
    print("alice", chain.balance_of(alice))
    print("bob", chain.balance_of(bob))

    # Alice sends Bob 12.345 NXI
    txid3, val3 = chain.transfer(alice, bob, 12.345)
    print("tx:", txid3, "validators:", val3)
    print("alice after:", chain.balance_of(alice))
    print("bob after:", chain.balance_of(bob))
    # show ledger sample
    print("recent ledger entries:")
    for e in chain.ledger[-3:]:
        print(e)
