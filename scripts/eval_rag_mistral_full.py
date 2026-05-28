import json
import os
import time
import requests
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# --- AYARLAR ---
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "mistral"
CHROMA_PATH = os.path.expanduser("~/Desktop/BGK601_Proje/data/chroma_db")
BENCHMARK_PATH = os.path.expanduser("~/Desktop/BGK601_Proje/benchmark/benchmark_dataset.json")
OUTPUT_PATH = os.path.expanduser("~/Desktop/BGK601_Proje/results/rag_mistral_results.json")

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

# --- VERİ YÜKLE ---
with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
    benchmark = json.load(f)
benchmark = benchmark  # pilot: ilk 20 örnek

# --- RAG VERİTABANINI AÇ ---
print("ChromaDB yükleniyor...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectordb = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
print("RAG hazır.")

def get_attck_context(girdi):
    """Log istatistiklerini metne çevir, ChromaDB'de ara, ATT&CK bilgisi getir"""
    # Log istatistiklerini arama sorgusuna dönüştür
    query = f"network traffic flow: "
    query += f"destination port {girdi.get('Destination Port', '')}, "
    query += f"SYN flags {girdi.get('SYN Flag Count', '')}, "
    query += f"total packets {girdi.get('Total Fwd Packets', '')}, "
    query += f"flow bytes per second {girdi.get('Flow Bytes/s', '')}"
    
    # ChromaDB'de en benzer 3 ATT&CK tekniğini bul
    docs = vectordb.similarity_search(query, k=3)
    
    # Bulunan teknikleri birleştir
    context = "\n\n".join([doc.page_content for doc in docs])
    return context

def analyze_flow(girdi):
    """Log + ATT&CK bağlamıyla Llama'ya sor"""
    
    # Adım 1: ATT&CK bilgisini getir
    attck_context = get_attck_context(girdi)
    
    # Adım 2: Zenginleştirilmiş prompt oluştur
    user_msg = "Analyze the following network traffic flow statistics:\n\n"
    for k, v in girdi.items():
        user_msg += f"{k}: {v}\n"
    
    prompt = f"""You are a SOC analyst with access to MITRE ATT&CK knowledge.

RELEVANT MITRE ATT&CK TECHNIQUES:
{attck_context}

Using the above ATT&CK context, analyze the network traffic and respond ONLY with this JSON:
{{
  "attack_detected": true/false,
  "mitre_tactic": "...",
  "mitre_technique_id": "T...",
  "mitre_technique_name": "...",
  "severity": "Low/Medium/High/Critical",
  "explanation": "brief explanation"
}}

User: {user_msg}
Assistant:"""

    # Adım 3: Llama'ya gönder
    start = time.time()
    response = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0}
    })
    latency = (time.time() - start) * 1000
    raw = response.json().get("response", "").strip()
    
    # Adım 4: JSON parse et
    try:
        clean = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean)
    except:
        parsed = {"parse_error": True, "raw": raw}
    
    return parsed, latency

# --- 3 RUN ---
all_results = []

for run_id in range(1, 4):
    print(f"\n=== RUN {run_id}/3 ===")
    results = []
    for i, sample in enumerate(benchmark):
        print(f"[{i+1}/{len(benchmark)}] ID:{sample['id']} | {sample['kategori']}")
        predicted, latency = analyze_flow(sample["girdi"])
        expected = sample["beklenen_cevap"]
        technique_match = predicted.get("mitre_technique_id", "") == expected["mitre_technique_id"]
        tactic_match = predicted.get("mitre_tactic", "").lower() == expected["mitre_tactic"].lower()
        attack_match = predicted.get("attack_detected") == expected["attack_detected"]
        result = {
            "run": run_id,
            "id": sample["id"],
            "kategori": sample["kategori"],
            "zorluk": sample["zorluk"],
            "expected": expected,
            "predicted": predicted,
            "scores": {
                "attack_detected_correct": attack_match,
                "tactic_correct": tactic_match,
                "technique_correct": technique_match,
            },
            "latency_ms": round(latency, 2)
        }
        results.append(result)
        print(f"    Technique: {'✅' if technique_match else '❌'} | Latency: {latency:.0f}ms")
    all_results.extend(results)

# --- KAYDET ---
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)

# --- ÖZET ---
total = len(benchmark)
print(f"\n{'='*50}")
print("LLAMA 3.2 + RAG SONUÇLARI")
print(f"{'='*50}")
for run_id in range(1, 4):
    run_results = [r for r in all_results if r["run"] == run_id]
    correct_technique = sum(1 for r in run_results if r["scores"]["technique_correct"])
    correct_tactic = sum(1 for r in run_results if r["scores"]["tactic_correct"])
    correct_attack = sum(1 for r in run_results if r["scores"]["attack_detected_correct"])
    avg_latency = sum(r["latency_ms"] for r in run_results) / len(run_results)
    print(f"RUN {run_id}: Attack={correct_attack}/{total} Tactic={correct_tactic}/{total} Technique={correct_technique}/{total} Latency={avg_latency:.0f}ms")
