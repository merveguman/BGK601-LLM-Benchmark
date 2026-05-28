import pandas as pd
import json
import random
import glob
import os

random.seed(42)

DATA_DIR = os.path.expanduser("~/Desktop/BGK601_Proje/data/cicids2017/")
OUTPUT = os.path.expanduser("~/Desktop/BGK601_Proje/benchmark/benchmark_dataset.json")

ATTCK = {
    "PortScan":                    {"tactic": "Reconnaissance",   "technique_id": "T1046",    "technique_name": "Network Service Discovery"},
    "FTP-Patator":                 {"tactic": "Credential Access","technique_id": "T1110.001","technique_name": "Brute Force: Password Guessing"},
    "SSH-Patator":                 {"tactic": "Credential Access","technique_id": "T1110.001","technique_name": "Brute Force: Password Guessing"},
    "DDoS":                        {"tactic": "Impact",           "technique_id": "T1498",    "technique_name": "Network Denial of Service"},
    "DoS Hulk":                    {"tactic": "Impact",           "technique_id": "T1499",    "technique_name": "Endpoint Denial of Service"},
    "DoS GoldenEye":               {"tactic": "Impact",           "technique_id": "T1499",    "technique_name": "Endpoint Denial of Service"},
    "DoS slowloris":               {"tactic": "Impact",           "technique_id": "T1499",    "technique_name": "Endpoint Denial of Service"},
    "DoS Slowhttptest":            {"tactic": "Impact",           "technique_id": "T1499",    "technique_name": "Endpoint Denial of Service"},
    "Web Attack  Brute Force":     {"tactic": "Credential Access","technique_id": "T1110.001","technique_name": "Brute Force: Password Guessing"},
    "Web Attack  Sql Injection":   {"tactic": "Initial Access",   "technique_id": "T1190",    "technique_name": "Exploit Public-Facing Application"},
    "Web Attack  XSS":             {"tactic": "Initial Access",   "technique_id": "T1059.007","technique_name": "Cross-Site Scripting"},
    "BENIGN":                      {"tactic": "None",             "technique_id": "None",     "technique_name": "None"},
}

FIELDS = [
    "Destination Port", "Flow Duration", "Total Fwd Packets",
    "Total Backward Packets", "Flow Bytes/s", "Flow Packets/s",
    "SYN Flag Count", "RST Flag Count", "FIN Flag Count",
    "Fwd Packet Length Mean", "Bwd Packet Length Mean"
]

# Tüm CSV'leri oku
csv_files = glob.glob(DATA_DIR + "*.csv")
dfs = []
for f in csv_files:
    print(f"Okunuyor: {os.path.basename(f)}")
    df = pd.read_csv(f, encoding="utf-8", low_memory=False)
    df.columns = df.columns.str.strip()
    dfs.append(df)

full_df = pd.concat(dfs, ignore_index=True)
full_df["Label"] = full_df["Label"].str.strip()
print(f"\nToplam kayıt: {len(full_df)}")
print("Kategoriler:", full_df["Label"].unique())

all_samples = []
sample_id = 1

for label, attck in ATTCK.items():
    subset = full_df[full_df["Label"] == label]
    if len(subset) == 0:
        print(f"UYARI: {label} bulunamadı, atlanıyor")
        continue
    
    n = min(40, len(subset))
    subset = subset.sample(n=n, random_state=42)
    
    for i, (_, row) in enumerate(subset.iterrows()):
        difficulty = "easy" if i < 14 else ("medium" if i < 27 else "hard")
        girdi = {}
        for f in FIELDS:
            if f in row:
                val = row[f]
                girdi[f] = float(val) if pd.notna(val) else 0.0
            else:
                girdi[f] = 0.0

        sample = {
            "id": sample_id,
            "kategori": label,
            "zorluk": difficulty,
            "girdi": girdi,
            "beklenen_cevap": {
                "attack_detected": label != "BENIGN",
                "mitre_tactic": attck["tactic"],
                "mitre_technique_id": attck["technique_id"],
                "mitre_technique_name": attck["technique_name"],
                "label": label
            },
            "aciklama": ""
        }
        all_samples.append(sample)
        sample_id += 1
    
    print(f"{label}: {n} örnek eklendi")

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(all_samples, f, ensure_ascii=False, indent=2)

print(f"\nToplam {len(all_samples)} örnek kaydedildi: {OUTPUT}")
