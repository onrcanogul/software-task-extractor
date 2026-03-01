"""
AMI Meeting Corpus - Software Task Extraction Pipeline
=======================================================
1. CSV'den her toplantıyı TXT transcript olarak çıkar (data/transcripts/ami/ altına)
2. Her transcript'i OpenAI'a gönder ve software task'ları çıkar
3. Sonucu results/ami_software_tasks.json formatında kaydet
"""

import os
import pandas as pd
from openai import OpenAI
import json
from pathlib import Path
import time
import sys
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# ============================================================================
# AYARLAR
# ============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent
CSV_FILE = BASE_DIR / "data" / "raw" / "ami_meeting_dataset.csv"
TRANSCRIPTS_DIR = BASE_DIR / "data" / "transcripts" / "ami"
RESULTS_DIR = BASE_DIR / "results"
OUTPUT_JSON = RESULTS_DIR / "ami_software_tasks.json"
OUTPUT_CSV = RESULTS_DIR / "ami_software_tasks.csv"
OUTPUT_XLSX = RESULTS_DIR / "ami_software_tasks.xlsx"

# OpenAI API Key — .env dosyasından okunur
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Kaç toplantı işleneceği (yaklaşık 60 meeting isteniyor, AMI'da 43 var, hepsini işle)
MAX_MEETINGS = 60


# ============================================================================
# ADIM 1: CSV'den Transcript TXT Dosyaları Oluştur
# ============================================================================
def create_transcripts_from_csv():
    """AMI CSV'den her toplantıyı ayrı TXT dosyası olarak kaydet."""
    print("=" * 80)
    print("ADIM 1: CSV'den Transcript TXT Dosyaları Oluşturuluyor")
    print("=" * 80)

    # CSV'yi yükle
    print(f"\n📂 CSV yükleniyor: {CSV_FILE}")
    df = pd.read_csv(CSV_FILE)
    print(f"✅ {len(df):,} satır yüklendi")

    # Unique meeting'leri al
    meeting_ids = sorted(df['meeting_id'].unique())
    print(f"📊 {len(meeting_ids)} unique toplantı bulundu")

    # Çıktı klasörünü oluştur
    TRANSCRIPTS_DIR.mkdir(exist_ok=True)

    created_files = []

    for meeting_id in meeting_ids:
        meeting_df = df[df['meeting_id'] == meeting_id].copy()

        # Zamana göre sırala
        meeting_df = meeting_df.sort_values('starttime')

        # Dosya adı
        filename = TRANSCRIPTS_DIR / f"{meeting_id}_transcript.txt"

        # İstatistikler
        total_utterances = len(meeting_df)
        unique_speakers = meeting_df['participant_id'].nunique()
        duration_min = 0
        if pd.notna(meeting_df['endtime'].max()) and pd.notna(meeting_df['starttime'].min()):
            duration_min = (meeting_df['endtime'].max() - meeting_df['starttime'].min()) / 60

        # Transcript metni oluştur
        lines = [
            "=" * 80,
            f"AMI Meeting Transcript: {meeting_id}",
            "=" * 80,
            "",
            f"Total Utterances: {total_utterances}",
            f"Unique Speakers: {unique_speakers}",
            f"Duration: {duration_min:.2f} minutes",
            "",
            "=" * 80,
            "TRANSCRIPT",
            "=" * 80,
            ""
        ]

        utterance_num = 0
        for _, row in meeting_df.iterrows():
            text = row.get('text', '')
            if pd.notna(text) and str(text).strip():
                utterance_num += 1
                starttime = row['starttime']
                speaker = row['participant_id']
                time_str = f"{int(starttime // 60):02d}:{int(starttime % 60):02d}"
                lines.append(f"[{utterance_num:04d}] [{time_str}] {speaker}: {text}")

        # Dosyaya yaz
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        created_files.append(filename)

    print(f"\n✅ {len(created_files)} transcript dosyası oluşturuldu: {TRANSCRIPTS_DIR}/")
    return created_files


# ============================================================================
# ADIM 2: OpenAI ile Software Task Çıkarma
# ============================================================================
def extract_software_tasks_from_transcript(transcript_text, meeting_id, client):
    """Bir toplantı transkriptinden software development task'larını çıkarır."""

    prompt = f"""Aşağıdaki toplantı transkriptini analiz et ve SADECE SOFTWARE DEVELOPMENT ile ilgili teknik task'ları çıkar.

⚠️ ÖNEMLİ KURALLAR:
- SADECE yazılım geliştirme, kodlama, sistem tasarımı ile ilgili işleri çıkar
- Toplantı organizasyonu, döküman yazma, genel araştırma gibi işleri ALMA
- Task board'a (Jira/Scrum) yazılabilecek SOMUT teknik işleri çıkar
- Eğer transkriptte software task yoksa boş array dön

✅ KABUL EDİLEN TASK TÜRLERİ:
- Yeni feature geliştirme (örn: "Implement remote control button mapping")
- Bug fix (örn: "Fix speech recognition module error")
- Refactoring (örn: "Optimize UI component rendering")
- API/Interface geliştirme (örn: "Design REST API for device control")
- Database/data işleme (örn: "Create product database schema")
- Test yazma (örn: "Write unit tests for voice interface")
- Deployment/DevOps (örn: "Set up CI/CD pipeline")
- Sistem entegrasyonu (örn: "Integrate speech recognition with UI")
- Performance optimizasyonu (örn: "Reduce remote control response latency")
- Library/tool geliştirme (örn: "Build prototyping toolkit")
- Hardware/Firmware (örn: "Design circuit for remote control")
- UI/UX geliştirme (örn: "Create LCD display interface")

❌ KABUL EDİLMEYEN:
- Toplantı organize etme
- Genel dokümantasyon yazma (code comment hariç)
- Marketing/satış işleri
- Bütçe/idari işler
- Genel araştırma (teknik POC/spike hariç)
- Kullanıcı anketleri (teknik user testing hariç)

Her task için:
1. **Title**: Jira ticket başlığı gibi kısa ve net (örn: "Implement voice command parser for remote control")
2. **Description**: Technical acceptance criteria (örn: "Parse voice commands, map to IR signals, handle error cases")
3. **Assignee**: Kod yazacak kişi (participant ID veya isim, belirtilmişse)
4. **Priority**: High/Medium/Low
5. **Task Type**: Feature/Bug/Refactor/Test/DevOps/Integration/Performance/Research
6. **Tech Stack**: Python/Java/JavaScript/C++/Embedded/Electronics/etc. (eğer belli ise)

Toplantı ID: {meeting_id}

TRANSCRIPT:
{transcript_text}

JSON formatında çıktı ver:
{{
  "meeting_id": "{meeting_id}",
  "software_tasks": [
    {{
      "title": "Implement ... ",
      "description": "Technical details...",
      "assignee": "developer_name or Belirtilmedi",
      "priority": "High/Medium/Low",
      "task_type": "Feature/Bug/Refactor/Test/etc",
      "tech_stack": "Python, XML, etc"
    }}
  ]
}}

Eğer hiç software task yoksa:
{{
  "meeting_id": "{meeting_id}",
  "software_tasks": []
}}

SADECE JSON çıktısı ver."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Sen bir software development toplantı analiz uzmanısın. Toplantı transkriptlerinden SADECE yazılım geliştirme task'larını çıkarırsın. Task board'a yazılabilecek teknik işleri bulursun. Her zaman JSON formatında yanıt veriyorsun."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        return result

    except Exception as e:
        print(f"❌ Hata ({meeting_id}): {str(e)}")
        return None


def process_all_transcripts():
    """Tüm AMI transcript'lerini işle ve software task'ları çıkar."""
    print("\n" + "=" * 80)
    print("ADIM 2: OpenAI ile Software Task Çıkarma")
    print("=" * 80)

    # OpenAI client
    client = OpenAI(api_key=OPENAI_API_KEY)

    # Transcript dosyalarını bul
    transcript_files = sorted(TRANSCRIPTS_DIR.glob("*_transcript.txt"))

    if not transcript_files:
        print(f"❌ {TRANSCRIPTS_DIR} klasöründe transcript bulunamadı!")
        return []

    # MAX_MEETINGS kadarını işle
    transcript_files = transcript_files[:MAX_MEETINGS]

    print(f"📁 {len(transcript_files)} toplantı transkripti işlenecek")
    print("🚀 Software task çıkarma işlemi başlıyor...\n")

    all_tasks = []
    processed_count = 0
    error_count = 0
    empty_count = 0

    # Daha önce işlenmiş sonuçları kontrol et (kaldığımız yerden devam)
    checkpoint_file = RESULTS_DIR / "ami_checkpoint.json"
    processed_meetings = {}
    if checkpoint_file.exists():
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            checkpoint_data = json.load(f)
            processed_meetings = {t['meeting_id']: t for t in checkpoint_data.get('tasks', [])}
            all_tasks = checkpoint_data.get('tasks', [])
            print(f"📌 Checkpoint bulundu: {len(processed_meetings)} toplantı daha önce işlenmiş")

    for i, file_path in enumerate(transcript_files, 1):
        meeting_id = file_path.stem.replace("_transcript", "")

        # Daha önce işlenmiş mi kontrol et
        if meeting_id in processed_meetings:
            print(f"[{i}/{len(transcript_files)}] ⏭️  Atlanıyor (zaten işlenmiş): {meeting_id}")
            continue

        print(f"[{i}/{len(transcript_files)}] İşleniyor: {meeting_id}...", end=" ")

        try:
            # Transcript dosyasını oku
            with open(file_path, 'r', encoding='utf-8') as f:
                transcript_text = f.read()

            # TRANSCRIPT bölümünden sonrasını al
            if "TRANSCRIPT" in transcript_text:
                parts = transcript_text.split("TRANSCRIPT")
                transcript_text = parts[-1] if len(parts) > 1 else transcript_text

            # Token limiti için kes (15000 karakter ≈ ~4000 token)
            if len(transcript_text) > 15000:
                transcript_text = transcript_text[:15000] + "\n\n[Transcript kesildi...]"

            # OpenAI'a istek at
            result = extract_software_tasks_from_transcript(
                transcript_text,
                meeting_id,
                client
            )

            if result and "software_tasks" in result:
                task_count = len(result['software_tasks'])

                for item in result["software_tasks"]:
                    item["meeting_id"] = meeting_id
                    all_tasks.append(item)

                if task_count > 0:
                    print(f"✅ {task_count} software task bulundu")
                else:
                    print(f"⚪ Software task yok")
                    empty_count += 1
                processed_count += 1
            else:
                print("⚠️  Sonuç alınamadı")
                error_count += 1

            # Checkpoint kaydet (her 5 toplantıda bir)
            if i % 5 == 0:
                save_checkpoint(all_tasks, checkpoint_file)

            # API rate limit
            time.sleep(1)

        except Exception as e:
            print(f"❌ Hata: {str(e)}")
            error_count += 1

    # Son checkpoint
    save_checkpoint(all_tasks, checkpoint_file)

    print(f"\n{'=' * 60}")
    print(f"✅ İşlem tamamlandı!")
    print(f"📊 İşlenen toplantı: {processed_count}")
    print(f"🔧 Toplam software task: {len(all_tasks)}")
    print(f"⚪ Task bulunamayan: {empty_count}")
    print(f"❌ Hatalı: {error_count}")
    print(f"{'=' * 60}")

    return all_tasks


def save_checkpoint(tasks, checkpoint_file):
    """Checkpoint kaydet (yarıda kalırsa devam edebilmek için)."""
    checkpoint_file.parent.mkdir(exist_ok=True)
    with open(checkpoint_file, 'w', encoding='utf-8') as f:
        json.dump({"tasks": tasks}, f, ensure_ascii=False, indent=2)


# ============================================================================
# ADIM 3: Sonuçları Kaydet (icsi_software_tasks.json formatında)
# ============================================================================
def save_results(all_tasks):
    """Sonuçları JSON, CSV ve XLSX formatında kaydet."""
    print("\n" + "=" * 80)
    print("ADIM 3: Sonuçlar Kaydediliyor")
    print("=" * 80)

    if not all_tasks:
        print("❌ Kaydedilecek task yok!")
        return

    RESULTS_DIR.mkdir(exist_ok=True)

    df = pd.DataFrame(all_tasks)

    # Sütun sırası
    columns = ["meeting_id", "title", "description", "assignee", "priority", "task_type", "tech_stack"]
    for col in columns:
        if col not in df.columns:
            df[col] = "Belirtilmedi"
    df = df[columns]

    # --- JSON ---
    tasks_json = df.to_dict('records')
    json_output = {
        "total_tasks": len(tasks_json),
        "total_meetings": df['meeting_id'].nunique(),
        "summary": {
            "by_priority": df['priority'].value_counts().to_dict(),
            "by_task_type": df['task_type'].value_counts().to_dict(),
            "by_tech_stack": df['tech_stack'].value_counts().to_dict()
        },
        "tasks": tasks_json
    }

    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(json_output, f, ensure_ascii=False, indent=2)
    print(f"💾 JSON kaydedildi: {OUTPUT_JSON}")

    # --- CSV ---
    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
    print(f"💾 CSV kaydedildi: {OUTPUT_CSV}")

    # --- XLSX ---
    with pd.ExcelWriter(OUTPUT_XLSX, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='All_Software_Tasks', index=False)

        for priority in ['High', 'Medium', 'Low']:
            df_p = df[df['priority'] == priority]
            if not df_p.empty:
                df_p.to_excel(writer, sheet_name=f'Priority_{priority}', index=False)

        for task_type in df['task_type'].unique():
            df_t = df[df['task_type'] == task_type]
            if not df_t.empty and len(df_t) >= 2:
                safe_name = task_type.replace('/', '-').replace('\\', '-')[:20]
                sheet_name = f'Type_{safe_name}'
                df_t.to_excel(writer, sheet_name=sheet_name, index=False)

        # Özet sheet'leri
        df_by_meeting = df.groupby('meeting_id').size().reset_index(name='task_count')
        df_by_meeting = df_by_meeting.sort_values('task_count', ascending=False)
        df_by_meeting.to_excel(writer, sheet_name='Summary_by_Meeting', index=False)

        df_by_type = df.groupby('task_type').size().reset_index(name='count')
        df_by_type = df_by_type.sort_values('count', ascending=False)
        df_by_type.to_excel(writer, sheet_name='Summary_by_TaskType', index=False)

        df_by_tech = df.groupby('tech_stack').size().reset_index(name='count')
        df_by_tech = df_by_tech.sort_values('count', ascending=False)
        df_by_tech.to_excel(writer, sheet_name='Summary_by_TechStack', index=False)

    print(f"💾 XLSX kaydedildi: {OUTPUT_XLSX}")

    # --- Özet Yazdır ---
    print(f"\n{'=' * 60}")
    print("📊 SONUÇ ÖZETİ")
    print(f"{'=' * 60}")
    print(f"Toplam Task: {len(df)}")
    print(f"Toplam Meeting: {df['meeting_id'].nunique()}")

    print(f"\n📊 Öncelik Dağılımı:")
    for p, c in df['priority'].value_counts().items():
        print(f"   {p}: {c}")

    print(f"\n📊 Task Type Dağılımı:")
    for t, c in df['task_type'].value_counts().items():
        print(f"   {t}: {c}")

    print(f"\n💻 Tech Stack Dağılımı (top 10):")
    for t, c in df['tech_stack'].value_counts().head(10).items():
        print(f"   {t}: {c}")

    # Checkpoint temizle
    checkpoint_file = RESULTS_DIR / "ami_checkpoint.json"
    if checkpoint_file.exists():
        checkpoint_file.unlink()
        print("\n🗑️  Checkpoint dosyası temizlendi")


# ============================================================================
# ANA ÇALIŞMA
# ============================================================================
def main():
    print("=" * 80)
    print(" " * 15 + "AMI MEETING CORPUS - SOFTWARE TASK EXTRACTION")
    print("=" * 80)
    print(f"\n📂 Proje dizini: {BASE_DIR}")
    print(f"📄 CSV dosyası: {CSV_FILE}")
    print(f"📁 Transcript dizini: {TRANSCRIPTS_DIR}")
    print(f"📁 Sonuç dizini: {RESULTS_DIR}")
    print()

    # ADIM 1: CSV'den transcript TXT'leri oluştur
    created_files = create_transcripts_from_csv()

    if not created_files:
        print("❌ Transcript dosyaları oluşturulamadı!")
        sys.exit(1)

    # ADIM 2: Her transcript'i OpenAI'a gönder
    all_tasks = process_all_transcripts()

    # ADIM 3: Sonuçları kaydet
    save_results(all_tasks)

    print("\n" + "=" * 80)
    print("✨ Tüm işlemler tamamlandı!")
    print("=" * 80)
    print(f"\n📁 Oluşturulan dosyalar:")
    print(f"   • {TRANSCRIPTS_DIR}/ ({len(created_files)} transcript TXT)")
    print(f"   • {OUTPUT_JSON}")
    print(f"   • {OUTPUT_CSV}")
    print(f"   • {OUTPUT_XLSX}")
    print("=" * 80)


if __name__ == "__main__":
    main()
