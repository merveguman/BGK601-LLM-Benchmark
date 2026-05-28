import json
import os
import time
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"

BENCHMARK_PATH = os.path.expanduser("~/Desktop/BGK601_Proje/benchmark/benchmark_dataset.json")
OUTPUT_PATH = os.path.expanduser("~/Desktop/BGK601_Proje/results/llama_results.json")

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
    benchmark = json.load(f)

# Pilot için sadece ilk 20 örnek
benchmark = benchmark[:20]

SYSTEM_PROMPT = """You are a SOC analyst. Analyze the given network traffic flow statistics.
Respond ONLY with this JSON format, nothing else:
{
  "attack_detected": true/false,
  "mitre_tactic": "...",
  "mitre_technique_id": "T...",
  "mitre_technique_name": "...",
  "severity": "Low/Medium/High/Critical",
  "explanation": "brief explanation"
}"""

def analyze_flow(girdi):
    user_msg = "Analyze the following network traffic flow statistics:\n\n"
    for k, v in girdi.items():
        user_msg += f"{k}: {v}\n"

    prompt = f"{SYSTEM_PROMPT}\n\nUser: {user_msg}\nAssistant:"

    start = time.time()
    response = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0}
    })
    latency = (time.time() - start) * 1000
    raw = response.json().get("response", "").strip()

    try:
        clean = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean)
    except:
        parsed = {"parse_error": True, "raw": raw}

    return parsed, latency

results = []
for i, sample in enumerate(benchmark):
    print(f"[{i+1}/{len(benchmark)}] ID:{sample['id']} | {sample['kategori']} | {sample['zorluk']}")

    predicted, latency = analyze_flow(sample["girdi"])

    expected = sample["beklenen_cevap"]

    technique_match = predicted.get("mitre_technique_id", "") == expected["mitre_technique_id"]
    tactic_match = predicted.get("mitre_tactic", "").lower() == expected["mitre_tactic"].lower()
    attack_match = predicted.get("attack_detected") == expected["attack_detected"]

    result = {
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
    print(f"    Technique: {'✅' if technique_match else '❌'} | Tactic: {'✅' if tactic_match else '❌'} | Latency: {latency:.0f}ms")

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

correct_technique = sum(1 for r in results if r["scores"]["technique_correct"])
correct_tactic = sum(1 for r in results if r["scores"]["tactic_correct"])
correct_attack = sum(1 for r in results if r["scores"]["attack_detected_correct"])
avg_latency = sum(r["latency_ms"] for r in results) / len(results)

print(f"\n{'='*40}")
print(f"SONUÇLAR ({len(results)} örnek)")
print(f"Attack Detection: {correct_attack}/{len(results)} ({correct_attack/len(results)*100:.1f}%)")
print(f"Tactic Accuracy:  {correct_tactic}/{len(results)} ({correct_tactic/len(results)*100:.1f}%)")
print(f"Technique Accuracy: {correct_technique}/{len(results)} ({correct_technique/len(results)*100:.1f}%)")
print(f"Avg Latency: {avg_latency:.0f}ms")
print(f"Sonuçlar kaydedildi: {OUTPUT_PATH}")
