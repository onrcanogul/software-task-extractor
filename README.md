# Part of the Thesis — Meeting Transcript Software Task Extraction

Bu proje, ICSI ve AMI toplantı korpuslarından yazılım geliştirme task'larını otomatik olarak çıkarmak ve çok ajanlı bir prompt sistemiyle değerlendirmek amacıyla geliştirilmiştir.

---

## 📁 Proje Yapısı

```
thesis/
│
├── data/
│   ├── raw/                        # Ham CSV/XLSX veri dosyaları
│   │   ├── icsi_meeting_dataset.csv/.xlsx
│   │   ├── ami_meeting_dataset.csv/.xlsx
│   │   ├── icsi_merged_meetings.xlsx
│   │   ├── icsi_action_items.csv/.xlsx
│   │   ├── icsi_software_tasks.csv/.xlsx/.txt
│   │   └── ami_merged_meetings.xlsx
│   │
│   └── transcripts/                # İşlenmiş toplantı transkriptleri (TXT)
│       ├── icsi/                   # 75 ICSI toplantısı (Bdb, Bed, Bmr, Bns, Bro, ...)
│       └── ami/                    # 43 AMI toplantısı (ES, IS, TS, ...)
│
├── corpus/                         # Ham korpus dosyaları (orijinal veri setleri)
│   ├── ICSIplus/                   # ICSI Meeting Corpus (XML, Words, Segments...)
│   └── ami_public_auto_1.5.1/      # AMI Meeting Corpus (ASR, dialogueActs...)
│
├── docs/                           # Ek dokümantasyon
│   └── README_ACTION_ITEMS.md      # Action item extraction hakkında notlar
│
├── results/                        # Çıkarılan yazılım task'ları (çıktılar)
│   ├── icsi_software_tasks.json    # 108 task, 43 toplantı
│   ├── ami_software_tasks.json     # 92 task, 28 toplantı
│   ├── ami_software_tasks.csv
│   └── ami_software_tasks.xlsx
│
├── scripts/                        # Python scriptleri
│   ├── extract_icsi_dataset.py     # ICSI korpusundan CSV dataset oluşturur
│   ├── extract_ami_dataset.py      # AMI korpusundan CSV dataset oluşturur
│   ├── merge_meeting_transcripts.py# ICSI CSV → TXT transcript dönüştürür
│   ├── merge_ami_transcripts.py    # AMI CSV → TXT transcript dönüştürür
│   ├── extract_action_items.py     # Transkriptlerden OpenAI ile task çıkarır
│   ├── extract_ami_software_tasks.py # AMI için tam pipeline (CSV→TXT→OpenAI→JSON)
│   ├── convert_to_excel.py         # JSON/CSV sonuçlarını Excel'e çevirir
│   ├── view_ami_data.py            # AMI verisini görüntüler
│   ├── view_icsi_texts.py          # ICSI verisini görüntüler
│   ├── view_merged_meetings.py     # Birleştirilmiş toplantıları görüntüler
│   └── show_dataset_samples.py     # Dataset örneklerini gösterir
│
├── prompts/                        # Prompt şablonları
│   ├── base-prompt.txt             # Çok ajanlı sistem promptu (Analyst + Developer + PO)
│   └── base-tasks.json             # 10 referans kalibrasyon task'ı (ICSI + AMI seçkisi)
│
├── logs/                           # Log dosyaları
│   └── software_tasks_extraction.log
│
└── README.md                       # Bu dosya
```

---

## 🚀 Pipeline

### 1. Dataset Oluşturma
```bash
# ICSI korpusundan CSV oluştur
python scripts/extract_icsi_dataset.py

# AMI korpusundan CSV oluştur
python scripts/extract_ami_dataset.py
```

### 2. Transcript Oluşturma
```bash
# ICSI CSV → TXT transcriptler (data/transcripts/icsi/)
python scripts/merge_meeting_transcripts.py

# AMI CSV → TXT transcriptler (data/transcripts/ami/)
python scripts/merge_ami_transcripts.py
```

### 3. Software Task Çıkarımı (OpenAI)
```bash
# AMI için tam pipeline (CSV → TXT → OpenAI → JSON)
python scripts/extract_ami_software_tasks.py

# Veya her iki korpus için birden
python scripts/extract_action_items.py
```

---

## 📊 Sonuçlar

| Korpus | Toplantı | Çıkarılan Task | JSON Dosyası |
|--------|----------|----------------|--------------|
| ICSI   | 43       | 108 task       | `results/icsi_software_tasks.json` |
| AMI    | 43 (28 task içeren) | 92 task | `results/ami_software_tasks.json` |

**Task Türleri:** Feature, Bug, Refactor, Integration, Test, UI/UX, API, Performance, Research, Hardware/Firmware, DevOps  
**Öncelikler:** HIGH, MEDIUM, LOW

---

## 🤖 Çok Ajanlı Prompt Sistemi

`prompts/base-prompt.txt` — Üç ajan rolü içeren sistem promptu:

| Ajan | Rol | Sorumluluk |
|------|-----|------------|
| **Analyst** | İş Analisti | Transkripti okur, aksiyon alınabilir noktaları tespit eder |
| **Developer** | Kıdemli Geliştirici | Task türü ve önceliği belirler, teknik detayları ekler |
| **Product Owner** | Ürün Sahibi | İş değerini doğrular, kabul kriterlerini yazar |

`prompts/base-tasks.json` — ICSI ve AMI korpuslarından seçilmiş **10 referans kalibrasyon task'ı**.  
Bu task'lar prompt'a few-shot örnek olarak eklenir.

---

## 🛠️ Gereksinimler

```bash
python -m venv .venv
source .venv/bin/activate
pip install pandas openai openpyxl
```

Python 3.13.0 | OpenAI gpt-4o-mini
