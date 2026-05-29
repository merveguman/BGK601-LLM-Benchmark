import pandas as pd
import json
import random
import glob
import os

random.seed(123)  # Farklı seed — benchmark'tan farklı örnekler

DATA_DIR = os.path.expanduser("~/Desktop/BGK601_Proje/data/cicids2017/")
OUTPUT = os.path.expanduser("~/Desktop/BGK601_Proje/data/finetune_train.jsonl")

# Benchmark'taki örnek ID'lerini yükle (bunları dışla)
BENCHMARK_PATH = os.path.expanduser("~/Desktop/BGK601_Proje/benchmark/benchmark_dataset.json")
with open(BENCHMARK_PATH) as f:
    benchmark = json.load(f)

ATTCK = {
    "PortScan":                  {"tactic": "Discovery",          "technique_id": "T1046",    "technique_name": "Network Service Discovery"},
    "FTP-Patator":               {"tactic": "Credential Access",  "technique_id": "T1110.001","technique_name": "Brute Force: Password Guessing"},
    "SSH-Patator":               {"tactic": "Credential Access",  "technique_id": "T1110.001","technique_name": "Brute Force: Password Guessing"},
    "DDoS":                      {"tactic": "Impact",             "technique_id": "T1498",    "technique_name": "Network Denial of Service"},
    "DoS Hulk":                  {"tactic": "Impact",             "technique_id": "T1499",    "technique_name": "Endpoint Denial of Service"},
    "DoS GoldenEye":             {"tactic": "Impact",             "technique_id": "T1499",    "technique_name": "Endpoint Denial of Service"},
    "DoS slowloris":             {"tactic": "Impact",             "technique_id": "T1499",    "technique_name": "Endpoint Denial of Service"},
    "DoS Slowhttptest":          {"tactic": "Impact",             "technique_id": "T1499",    "technique_name": "Endpoint Denial of Service"},
    "Web Attack  Brute Force":   {"tactic": "Credential Access",  "technique_id": "T1110.001","technique_name": "Brute Force: Password Guessing"},
    "Web Attack  Sql Injection": {"tactic": "Initial Access",     "technique_id": "T1190",    "technique_name": "Exploit Public-Facing Application"},
    "Web Attack  XSS":           {"tactic": "Initial Access",     "technique_id": "T1059.007","technique_name": "Cross-Site Scripting"},
    "BENIGN":                    {"tactic": "None",               "technique_id": "None",     "technique_name": "None"},
}

FIELDS = [
    "Destination Port", "Flow Duration", "Total Fwd Packets",
    "Total Backward Packets", "Flow Bytes/s", "Flow Packets/s",
    "SYN Flag Count", "RST Flag Count", "FIN Flag Count",
    "Fwd Packet Length Mean", "Bwd Packet Length Mean"
]

# CSV'leri oku
csv_files = glob.glob(DATA_DIR + "*.csv")
dfs = []
for f in csv_files:
    print(f"Okunuyor: {os.path.basename(f)}")
    df = pd.read_csv(f, encoding="utf-8", low_memory=False)
    df.columns = df.columns.str.strip()
    dfs.append(df)

full_df = pd.concat(dfs, ignore_index=True)
full_df["Label"] = full_df["Label"].str.strip()

# Her kategoriden 60 örnek seç (benchmark'takinden farklı)
# Benchmark random.seed(42) kullandı, biz seed(123) kullanıyoruz
all_samples = []

for label, attck in ATTCK.items():
    subset = full_df[full_df["Label"] == label]
    if len(subset) == 0:
        continue
    
    n = min(60, len(subset))
    subset = subset.sample(n=n, random_state=123)
    
    for _, row in subset.iterrows():
        girdi = {}
        for field in FIELDS:
            if field in row:
                val = row[field]
                girdi[field] = float(val) if pd.notna(val) else 0.0
            else:
                girdi[field] = 0.0
        
        user_msg = "Analyze the following network traffic flow statistics:\n\n"
        for k, v in girdi.items():
            user_msg += f"{k}: {v}\n"
        
        assistant_msg = json.dumps({
            "attack_detected": label != "BENIGN",
            "mitre_tactic": attck["tactic"],
            "mitre_technique_id": attck["technique_id"],
            "mitre_technique_name": attck["technique_name"],
            "severity": "High" if label != "BENIGN" else "Low",
            "explanation": f"Traffic analysis indicates {label} activity."
        })
        
        record = {
            "messages": [
                {"role": "system", "content": "You are a SOC analyst. Analyze network traffic and respond ONLY in JSON format."},
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": assistant_msg}
            ]
        }
        all_samples.append(record)
    
    print(f"{label}: {n} örnek eklendi")

random.shuffle(all_samples)

with open(OUTPUT, "w") as f:
    for record in all_samples:
        f.write(json.dumps(record) + "\n")

print(f"\nToplam {len(all_samples)} eğitim örneği: {OUTPUT}")
