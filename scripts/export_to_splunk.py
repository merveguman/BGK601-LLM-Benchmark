import json
import os
import glob
import csv

RESULTS_DIR = os.path.expanduser("~/Desktop/BGK601_Proje/results/")
OUTPUT_CSV = os.path.expanduser("~/Desktop/BGK601_Proje/data/benchmark_results.csv")

MODEL_NAMES = {
    "claude_results.json": "Claude Sonnet 4.5",
    "gpt4o_results.json": "GPT-5.4-mini",
    "llama_results.json": "Llama 3.2 (base)",
    "mistral_results.json": "Mistral 7B (base)",
    "rag_llama_results.json": "Llama 3.2 + RAG",
    "rag_mistral_results.json": "Mistral 7B + RAG",
}

rows = []
for filename, model_name in MODEL_NAMES.items():
    filepath = os.path.join(RESULTS_DIR, filename)
    if not os.path.exists(filepath):
        continue
    with open(filepath) as f:
        results = json.load(f)
    for r in results:
        rows.append({
            "model": model_name,
            "run": r.get("run", 1),
            "id": r["id"],
            "kategori": r["kategori"],
            "zorluk": r["zorluk"],
            "attack_correct": int(r["scores"]["attack_detected_correct"]),
            "tactic_correct": int(r["scores"]["tactic_correct"]),
            "technique_correct": int(r["scores"]["technique_correct"]),
            "latency_ms": r["latency_ms"],
            "predicted_attack": r["predicted"].get("attack_detected", ""),
            "predicted_tactic": r["predicted"].get("mitre_tactic", ""),
            "predicted_technique": r["predicted"].get("mitre_technique_id", ""),
            "expected_tactic": r["expected"]["mitre_tactic"],
            "expected_technique": r["expected"]["mitre_technique_id"],
        })

with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"{len(rows)} satır kaydedildi: {OUTPUT_CSV}")
