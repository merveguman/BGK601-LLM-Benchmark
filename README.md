# BGK601 — LLM Benchmark: Ağ Anomali Tespiti ve MITRE ATT&CK Eşleştirmesi

**Öğrenci:** Mervenur Güman  
**Ders:** BGK601 — Bilgi Güvenliği Alanında Makine Öğrenmesi Yöntemleri  
**Dönem:** Bahar 2025–2026

## Proje Özeti

Bu çalışmada 6 LLM konfigürasyonu, CICIDS2017 veri seti üzerinde ağ trafiği anomali tespiti ve MITRE ATT&CK eşleştirmesi görevlerinde karşılaştırmalı olarak değerlendirilmiştir.

## Klasör Yapısı

├── benchmark/          # 360 örneklik benchmark veri seti
├── scripts/            # Değerlendirme scriptleri
├── results/            # Model sonuçları (JSON)
├── report/             # Final raporu (PDF)
└── data/               # Veri (CICIDS2017 aşağıdaki linkten indirilebilir)
## Veri Seti

CICIDS2017: https://www.unb.ca/cic/datasets/ids-2017.html

## Kullanım

```bash
pip install anthropic openai langchain chromadb sentence-transformers pandas

# Claude ile değerlendirme
python scripts/eval_claude_full.py

# Llama + RAG ile değerlendirme  
python scripts/eval_rag_llama_full.py

# Sonuç analizi
python scripts/analyze_results.py
```

## Sonuçlar

| Model | Attack Detection | Ağırlıklı Skor |
|-------|----------------|----------------|
| Claude Sonnet 4.5 | %84.0 | 34.0 |
| Mistral 7B + RAG | %57.5 | 25.1 |
| GPT-5.4-mini | %45.2 | 23.9 |
| Llama 3.2 + RAG | %38.3 | 18.5 |
| Mistral 7B (base) | %15.3 | 13.8 |
| Llama 3.2 (base) | %11.1 | 12.8 |
