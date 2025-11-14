# wallet_create.py
import json, uuid, hashlib

# ฟังก์ชันสร้าง address จาก seed
def make_address(seed):
    return hashlib.sha256(seed.encode()).hexdigest()[:40]

# เริ่มสร้างกระเป๋าใหม่
seed = uuid.uuid4().hex + uuid.uuid4().hex   # ค่า seed แบบยาว
address = make_address(seed)

wallet = {
    "address": address,
    "seed": seed,
    "balance_units": 0,      # 0 NXI
    "decimals": 8,
    "network": "NEXAI-NXI"
}

filename = f"wallet_{address[:10]}.json"
with open(filename, "w") as f:
    json.dump(wallet, f, indent=2)

print("สร้างกระเป๋าเรียบร้อยแล้ว")
print("ไฟล์:", filename)
print("ที่อยู่กระเป๋า (Address):", address)
print("Seed (ห้ามบอกใคร):", seed)
