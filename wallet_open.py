# wallet_open.py
import json

filename = input("ใส่ชื่อไฟล์กระเป๋า (.json): ")

with open(filename, "r") as f:
    w = json.load(f)

print("\n=== ข้อมูลกระเป๋า ===")
print("Network :", w["network"])
print("Address :", w["address"])
print("Seed    :", w["seed"])
print("Balance :", w["balance_units"] / 10**w["decimals"], "NXI")
