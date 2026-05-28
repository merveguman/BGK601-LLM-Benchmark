import json
import os
import glob
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

RESULTS_DIR = os.path.expanduser("~/Desktop/BGK601_Proje/results/")
OUTPUT_DIR = os.path.expanduser("~/Desktop/BGK601_Proje/report/")

# Ağırlıklar (Bölüm 2.2.3)
WEIGHTS = {
    "attack": 0.25,
    "tactic": 0.25,
    "technique": 0.20,
    "parse": 0.10,
    "explanation": 0.10,
    "latency": 0.05,
    "cost": 0.05
}

# Model maliyetleri ($/1K token)
COSTS = {
    "claude_results.json": 0.003,
    "gpt4o_results.json": 0.00060,
    "llama_results.json": 0.0,
    "mistral_results.json": 0.0,
    "rag_llama_results.json": 0.0,
    "rag_mistral_results.json": 0.0,
}

MODEL_NAMES = {
    "claude_results.json": "Claude Sonnet 4.5",
    "gpt4o_results.json": "GPT-5.4-mini",
    "llama_results.json": "Llama 3.2 (base)",
    "mistral_results.json": "Mistral 7B (base)",
    "rag_llama_results.json": "Llama 3.2 + RAG",
    "rag_mistral_results.json": "Mistral 7B + RAG",
}

def load_results(filepath):
    with open(filepath) as f:
        return json.load(f)

def get_run_scores(results, run_id):
    run_results = [r for r in results if r.get("run", 1) == run_id]
    n = len(run_results)
    attack = [1 if r["scores"]["attack_detected_correct"] else 0 for r in run_results]
    tactic = [1 if r["scores"]["tactic_correct"] else 0 for r in run_results]
    technique = [1 if r["scores"]["technique_correct"] else 0 for r in run_results]
    parse = [0 if "parse_error" in r["predicted"] else 1 for r in run_results]
    return {
        "attack": np.mean(attack),
        "tactic": np.mean(tactic),
        "technique": np.mean(technique),
        "parse": np.mean(parse),
        "attack_arr": attack,
        "n": n
    }

def weighted_score(scores):
    return (scores["attack"] * WEIGHTS["attack"] +
            scores["tactic"] * WEIGHTS["tactic"] +
            scores["technique"] * WEIGHTS["technique"] +
            scores["parse"] * WEIGHTS["parse"])

def bootstrap_ci(arr, n_bootstrap=1000, ci=95):
    arr = np.array(arr)
    bootstrap_means = [np.mean(np.random.choice(arr, len(arr))) 
                       for _ in range(n_bootstrap)]
    lower = np.percentile(bootstrap_means, (100-ci)/2)
    upper = np.percentile(bootstrap_means, 100-(100-ci)/2)
    return lower, upper

# === 1. AĞIRLIKLI SKOR VE BOOTSTRAP CI ===
print("\n" + "="*60)
print("AĞIRLIKLI GENEL SKOR VE %95 BOOTSTRAP GÜVEN ARALIĞI")
print("="*60)

all_stats = {}
for filename, model_name in MODEL_NAMES.items():
    filepath = os.path.join(RESULTS_DIR, filename)
    if not os.path.exists(filepath):
        continue
    results = load_results(filepath)
    run_ids = sorted(set(r.get("run", 1) for r in results))
    
    run_scores_list = []
    all_attack = []
    
    for run_id in run_ids:
        s = get_run_scores(results, run_id)
        run_scores_list.append(s)
        all_attack.extend(s["attack_arr"])
    
    avg_attack = np.mean([s["attack"] for s in run_scores_list])
    avg_tactic = np.mean([s["tactic"] for s in run_scores_list])
    avg_technique = np.mean([s["technique"] for s in run_scores_list])
    avg_parse = np.mean([s["parse"] for s in run_scores_list])
    avg_latency = np.mean([r["latency_ms"] for r in results]) / 1000
    
    w_score = (avg_attack * WEIGHTS["attack"] +
               avg_tactic * WEIGHTS["tactic"] +
               avg_technique * WEIGHTS["technique"] +
               avg_parse * WEIGHTS["parse"])
    
    ci_low, ci_high = bootstrap_ci(all_attack)
    
    all_stats[model_name] = {
        "attack": avg_attack,
        "tactic": avg_tactic,
        "technique": avg_technique,
        "parse": avg_parse,
        "weighted": w_score,
        "latency": avg_latency,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "filename": filename
    }
    
    print(f"\n{model_name}")
    print(f"  Attack: {avg_attack*100:.1f}% | Tactic: {avg_tactic*100:.1f}% | Technique: {avg_technique*100:.1f}%")
    print(f"  Ağırlıklı Skor: {w_score*100:.1f}%")
    print(f"  %95 Bootstrap CI: [{ci_low*100:.1f}%, {ci_high*100:.1f}%]")

# === 2. McNEMAR TESTİ (Claude vs GPT) ===
print("\n" + "="*60)
print("McNEMAR TESTİ — Claude Sonnet 4.5 vs GPT-5.4-mini")
print("="*60)

claude_file = os.path.join(RESULTS_DIR, "claude_results.json")
gpt_file = os.path.join(RESULTS_DIR, "gpt4o_results.json")

if os.path.exists(claude_file) and os.path.exists(gpt_file):
    claude_results = load_results(claude_file)
    gpt_results = load_results(gpt_file)
    
    claude_run1 = {r["id"]: r["scores"]["attack_detected_correct"] 
                   for r in claude_results if r.get("run",1) == 1}
    gpt_run1 = {r["id"]: r["scores"]["attack_detected_correct"] 
                for r in gpt_results if r.get("run",1) == 1}
    
    common_ids = set(claude_run1.keys()) & set(gpt_run1.keys())
    
    b = sum(1 for i in common_ids if claude_run1[i] and not gpt_run1[i])
    c = sum(1 for i in common_ids if not claude_run1[i] and gpt_run1[i])
    
    if b + c > 0:
        chi2 = (abs(b - c) - 1)**2 / (b + c)
        p_value = 1 - stats.chi2.cdf(chi2, df=1)
        print(f"  b={b}, c={c}, χ²={chi2:.3f}, p={p_value:.4f}")
        if p_value < 0.05:
            print("  Sonuç: İstatistiksel olarak ANLAMLI fark (p<0.05)")
        else:
            print("  Sonuç: Anlamlı fark YOK (p≥0.05)")

# === 3. KATEGORİ BAZLI HATA ANALİZİ ===
print("\n" + "="*60)
print("KATEGORİ BAZLI HATA ANALİZİ — Claude Sonnet 4.5")
print("="*60)

if os.path.exists(claude_file):
    claude_results = load_results(claude_file)
    run1 = [r for r in claude_results if r.get("run",1) == 1]
    
    categories = {}
    for r in run1:
        cat = r["kategori"]
        if cat not in categories:
            categories[cat] = {"correct": 0, "total": 0}
        categories[cat]["total"] += 1
        if r["scores"]["attack_detected_correct"]:
            categories[cat]["correct"] += 1
    
    print(f"  {'Kategori':<25} {'Doğru/Toplam':<15} {'Başarı %'}")
    for cat, vals in sorted(categories.items(), key=lambda x: x[1]["correct"]/x[1]["total"]):
        pct = vals["correct"]/vals["total"]*100
        print(f"  {cat:<25} {vals['correct']}/{vals['total']:<12} %{pct:.1f}")

# === 4. MALİYET-BAŞARIM GRAFİĞİ ===
fig, ax = plt.subplots(figsize=(10, 6))

for filename, model_name in MODEL_NAMES.items():
    if model_name not in all_stats:
        continue
    stats_data = all_stats[model_name]
    cost = COSTS.get(filename, 0.0)
    attack_pct = stats_data["attack"] * 100
    latency = stats_data["latency"]
    
    ax.scatter(cost, attack_pct, s=200, zorder=5)
    ax.annotate(model_name, (cost, attack_pct),
                textcoords="offset points", xytext=(8, 4), fontsize=9)

ax.set_xlabel("Maliyet ($/token)", fontsize=12)
ax.set_ylabel("Attack Detection Accuracy (%)", fontsize=12)
ax.set_title("Maliyet-Başarım Dengesi", fontsize=14, fontweight="bold")
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "graph_cost_performance.png"), dpi=150, bbox_inches="tight")
plt.close()
print("\ngraph_cost_performance.png kaydedildi")

# === 5. NİTEL ANALİZ — 5 ÖRNEK ===
print("\n" + "="*60)
print("NİTEL ANALİZ — 5 İlginç Örnek (Claude)")
print("="*60)

if os.path.exists(claude_file):
    claude_results = load_results(claude_file)
    run1 = [r for r in claude_results if r.get("run",1) == 1]
    
    # 2 doğru, 3 yanlış seç
    correct = [r for r in run1 if r["scores"]["attack_detected_correct"]][:2]
    wrong = [r for r in run1 if not r["scores"]["attack_detected_correct"]][:3]
    
    for i, r in enumerate(correct + wrong, 1):
        status = "✅ DOĞRU" if r["scores"]["attack_detected_correct"] else "❌ YANLIŞ"
        print(f"\nÖrnek {i} [{status}] — {r['kategori']} ({r['zorluk']})")
        print(f"  Beklenen: attack={r['expected']['attack_detected']} | {r['expected']['mitre_technique_id']}")
        print(f"  Tahmin:   attack={r['predicted'].get('attack_detected')} | {r['predicted'].get('mitre_technique_id','?')}")
        print(f"  Açıklama: {r['predicted'].get('explanation','')[:100]}...")

print("\nTüm analizler tamamlandı.")
