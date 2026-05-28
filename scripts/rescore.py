import json
import os
import glob

RESULTS_DIR = os.path.expanduser("~/Desktop/BGK601_Proje/results/")

result_files = glob.glob(RESULTS_DIR + "*.json")

for filepath in result_files:
    filename = os.path.basename(filepath)
    with open(filepath) as f:
        results = json.load(f)

    # Skorları yeniden hesapla
    for r in results:
        expected = r["expected"]
        predicted = r["predicted"]
        
        if "parse_error" in predicted:
            continue

        # Esnek karşılaştırma — küçük harf, boşluk temizle
        r["scores"]["attack_detected_correct"] = (
            predicted.get("attack_detected") == expected["attack_detected"]
        )
        r["scores"]["tactic_correct"] = (
            predicted.get("mitre_tactic", "").lower().strip() == 
            expected["mitre_tactic"].lower().strip()
        )
        r["scores"]["technique_correct"] = (
            predicted.get("mitre_technique_id", "").strip() == 
            expected["mitre_technique_id"].strip()
        )

    # Kaydet
    with open(filepath, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Özet
    total = len(set(r["id"] for r in results))
    run_ids = sorted(set(r.get("run", 1) for r in results))
    
    print(f"\n{filename}")
    for run_id in run_ids:
        run_results = [r for r in results if r.get("run", 1) == run_id]
        if not run_results:
            continue
        attack = sum(1 for r in run_results if r["scores"]["attack_detected_correct"])
        tactic = sum(1 for r in run_results if r["scores"]["tactic_correct"])
        technique = sum(1 for r in run_results if r["scores"]["technique_correct"])
        n = len(run_results)
        print(f"  RUN {run_id}: Attack={attack}/{n} ({attack/n*100:.1f}%) Tactic={tactic}/{n} ({tactic/n*100:.1f}%) Technique={technique}/{n} ({technique/n*100:.1f}%)")
