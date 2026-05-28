import json
import os
import glob
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

RESULTS_DIR = os.path.expanduser("~/Desktop/BGK601_Proje/results/")
OUTPUT_DIR = os.path.expanduser("~/Desktop/BGK601_Proje/report/")

# Model isim eşleştirme
MODEL_NAMES = {
    "claude_results.json": "Claude Sonnet 4.5",
    "gpt4o_results.json": "GPT-5.4-mini",
    "llama_results.json": "Llama 3.2 (base)",
    "mistral_results.json": "Mistral 7B (base)",
    "rag_llama_results.json": "Llama 3.2 + RAG",
    "rag_mistral_results.json": "Mistral 7B + RAG",
}

MODEL_COLORS = {
    "Claude Sonnet 4.5": "#2E86AB",
    "GPT-5.4-mini": "#10A37F",
    "Llama 3.2 (base)": "#E84855",
    "Mistral 7B (base)": "#F46036",
    "Llama 3.2 + RAG": "#9B5DE5",
    "Mistral 7B + RAG": "#F15BB5",
}

def load_results(filepath):
    with open(filepath) as f:
        results = json.load(f)
    
    run_ids = sorted(set(r.get("run", 1) for r in results))
    attack_scores, tactic_scores, technique_scores, latencies = [], [], [], []
    
    for run_id in run_ids:
        run_results = [r for r in results if r.get("run", 1) == run_id]
        n = len(run_results)
        attack_scores.append(sum(1 for r in run_results if r["scores"]["attack_detected_correct"]) / n * 100)
        tactic_scores.append(sum(1 for r in run_results if r["scores"]["tactic_correct"]) / n * 100)
        technique_scores.append(sum(1 for r in run_results if r["scores"]["technique_correct"]) / n * 100)
        latencies.append(sum(r["latency_ms"] for r in run_results) / n)
    
    return {
        "attack": np.mean(attack_scores),
        "tactic": np.mean(tactic_scores),
        "technique": np.mean(technique_scores),
        "latency": np.mean(latencies),
        "attack_std": np.std(attack_scores),
    }

# Sonuçları yükle
all_stats = {}
for filename, model_name in MODEL_NAMES.items():
    filepath = os.path.join(RESULTS_DIR, filename)
    if os.path.exists(filepath):
        all_stats[model_name] = load_results(filepath)
        print(f"{model_name}: Attack={all_stats[model_name]['attack']:.1f}% Tactic={all_stats[model_name]['tactic']:.1f}% Technique={all_stats[model_name]['technique']:.1f}%")

# --- GRAFİK 1: Attack Detection Karşılaştırması ---
fig, ax = plt.subplots(figsize=(10, 6))
models = list(all_stats.keys())
attack_vals = [all_stats[m]["attack"] for m in models]
colors = [MODEL_COLORS.get(m, "#999999") for m in models]
bars = ax.bar(models, attack_vals, color=colors, edgecolor="white", linewidth=0.5)
for bar, val in zip(bars, attack_vals):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
            f"%{val:.1f}", ha="center", va="bottom", fontsize=10, fontweight="bold")
ax.set_ylabel("Attack Detection Accuracy (%)", fontsize=12)
ax.set_title("Model Karşılaştırması — Attack Detection", fontsize=14, fontweight="bold")
ax.set_ylim(0, 100)
ax.tick_params(axis="x", rotation=30)
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "graph_attack_detection.png"), dpi=150, bbox_inches="tight")
plt.close()
print("graph_attack_detection.png kaydedildi")

# --- GRAFİK 2: Tüm Metrikler Grouped Bar ---
fig, ax = plt.subplots(figsize=(12, 6))
x = np.arange(len(models))
width = 0.25
bars1 = ax.bar(x - width, [all_stats[m]["attack"] for m in models], width, label="Attack Detection", color="#2E86AB", alpha=0.85)
bars2 = ax.bar(x, [all_stats[m]["tactic"] for m in models], width, label="Tactic Accuracy", color="#E84855", alpha=0.85)
bars3 = ax.bar(x + width, [all_stats[m]["technique"] for m in models], width, label="Technique Accuracy", color="#F46036", alpha=0.85)
ax.set_ylabel("Accuracy (%)", fontsize=12)
ax.set_title("Model Karşılaştırması — Tüm Metrikler", fontsize=14, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(models, rotation=30, ha="right")
ax.set_ylim(0, 100)
ax.legend(fontsize=10)
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "graph_all_metrics.png"), dpi=150, bbox_inches="tight")
plt.close()
print("graph_all_metrics.png kaydedildi")

# --- GRAFİK 3: RAG Ablasyon ---
fig, ax = plt.subplots(figsize=(8, 5))
rag_models = ["Llama 3.2 (base)", "Llama 3.2 + RAG", "Mistral 7B (base)", "Mistral 7B + RAG"]
rag_vals = [all_stats[m]["attack"] for m in rag_models if m in all_stats]
rag_labels = [m for m in rag_models if m in all_stats]
rag_colors = ["#E84855", "#9B5DE5", "#F46036", "#F15BB5"]
bars = ax.bar(rag_labels, rag_vals, color=rag_colors, edgecolor="white")
for bar, val in zip(bars, rag_vals):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
            f"%{val:.1f}", ha="center", va="bottom", fontsize=11, fontweight="bold")
ax.set_ylabel("Attack Detection Accuracy (%)", fontsize=12)
ax.set_title("RAG Ablasyon Analizi", fontsize=14, fontweight="bold")
ax.set_ylim(0, 100)
ax.tick_params(axis="x", rotation=15)
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "graph_rag_ablation.png"), dpi=150, bbox_inches="tight")
plt.close()
print("graph_rag_ablation.png kaydedildi")

# --- GRAFİK 4: Latency Karşılaştırması ---
fig, ax = plt.subplots(figsize=(10, 5))
latency_vals = [all_stats[m]["latency"]/1000 for m in models]
bars = ax.bar(models, latency_vals, color=colors, edgecolor="white")
for bar, val in zip(bars, latency_vals):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
            f"{val:.1f}s", ha="center", va="bottom", fontsize=10, fontweight="bold")
ax.set_ylabel("Ortalama Yanıt Süresi (saniye)", fontsize=12)
ax.set_title("Model Karşılaştırması — Latency", fontsize=14, fontweight="bold")
ax.tick_params(axis="x", rotation=30)
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "graph_latency.png"), dpi=150, bbox_inches="tight")
plt.close()
print("graph_latency.png kaydedildi")

print("\nTüm grafikler kaydedildi!")
