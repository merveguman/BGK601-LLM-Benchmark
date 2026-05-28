import json
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

ATTCK_PATH = os.path.expanduser("~/Desktop/BGK601_Proje/data/enterprise-attack.json")
CHROMA_PATH = os.path.expanduser("~/Desktop/BGK601_Proje/data/chroma_db")

print("ATT&CK JSON yükleniyor...")
with open(ATTCK_PATH, "r", encoding="utf-8") as f:
    attck = json.load(f)

# Sadece technique'leri çıkar
techniques = []
for obj in attck.get("objects", []):
    if obj.get("type") == "attack-pattern":
        name = obj.get("name", "")
        desc = obj.get("description", "")
        
        # Tactic bilgisi
        tactics = []
        for phase in obj.get("kill_chain_phases", []):
            if phase.get("kill_chain_name") == "mitre-attack":
                tactics.append(phase.get("phase_name", ""))
        
        # External ID (T1046 gibi)
        ext_id = ""
        for ref in obj.get("external_references", []):
            if ref.get("source_name") == "mitre-attack":
                ext_id = ref.get("external_id", "")
        
        if ext_id and desc:
            text = f"Technique: {ext_id} - {name}\nTactics: {', '.join(tactics)}\nDescription: {desc[:500]}"
            techniques.append(text)

print(f"{len(techniques)} teknik bulundu.")

# Chunk'lara böl
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
docs = splitter.create_documents(techniques)
print(f"{len(docs)} chunk oluşturuldu.")

# Embedding ve ChromaDB
print("Embedding modeli yükleniyor...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

print("ChromaDB'ye kaydediliyor...")
vectordb = Chroma.from_documents(docs, embeddings, persist_directory=CHROMA_PATH)
vectordb.persist()

print(f"RAG veritabanı hazır: {CHROMA_PATH}")
print(f"Toplam {vectordb._collection.count()} chunk indekslendi.")
