import os
import pandas as pd
from openai import OpenAI
import json
from pathlib import Path
import time
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# OpenAI API Key — .env dosyasından okunur
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

def extract_action_items_from_transcript(transcript_text, meeting_id, client):
    """
    Bir toplantı transkriptinden SOFTWARE DEVELOPMENT task'larını çıkarır.
    """
    
    prompt = f"""Aşağıdaki toplantı transkriptini analiz et ve SADECE SOFTWARE DEVELOPMENT ile ilgili teknik task'ları çıkar.

⚠️ ÖNEMLİ KURALLAR:
- SADECE yazılım geliştirme, kodlama, sistem tasarımı ile ilgili işleri çıkar
- Toplantı organizasyonu, döküman yazma, genel araştırma gibi işleri ALMA
- Task board'a (Jira/Scrum) yazılabilecek SOMUT teknik işleri çıkar
- Eğer transkriptte software task yoksa boş array dön

✅ KABUL EDİLEN TASK TÜRLERİ:
- Yeni feature geliştirme (örn: "Parser'a yeni format desteği ekle")
- Bug fix (örn: "XML parsing hatasını düzelt")
- Refactoring (örn: "Bayes-net modulünü optimize et")
- API/Interface geliştirme (örn: "REST API endpoint'i ekle")
- Database/data işleme (örn: "Transcript veritabanı şeması oluştur")
- Test yazma (örn: "Unit test coverage'ı artır")
- Deployment/DevOps (örn: "Docker container'ı hazırla")
- Sistem entegrasyonu (örn: "Ontology service'i entegre et")
- Performance optimizasyonu (örn: "Query performance'ını iyileştir")
- Library/tool geliştirme (örn: "Yeni Python modülü yaz")

❌ KABUL EDİLMEYEN:
- Toplantı organize etme
- Genel dokümantasyon yazma (code comment hariç)
- Kullanıcı testleri yapma
- Bütçe/idari işler
- Genel araştırma (teknik POC/spike hariç)

Her task için:
1. **Title**: Jira ticket başlığı gibi kısa ve net (örn: "Implement XML parser for dialogue acts")
2. **Description**: Technical acceptance criteria (örn: "Parse XML files from DialogueActs folder, extract nite:child elements, return structured data")
3. **Assignee**: Kod yazacak kişi (belirtilmişse)
4. **Priority**: High/Medium/Low
5. **Task Type**: Feature/Bug/Refactor/Test/DevOps/Integration/Performance/Research
6. **Tech Stack**: Python/Java/JavaScript/XML/SQL/etc. (eğer belli ise)

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
            model="gpt-4o-mini",  # Daha ekonomik model, gpt-4o da kullanılabilir
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
            temperature=0.2,  # Çok düşük - sadece net teknik task'lar için
            response_format={"type": "json_object"}  # JSON formatında yanıt al
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        print(f"❌ Hata ({meeting_id}): {str(e)}")
        return None


def process_icsi_transcripts(transcripts_folder, output_file, api_key):
    """
    ICSI toplantı transkriptlerini işler ve action item'ları çıkarır.
    """
    
    # OpenAI client oluştur
    client = OpenAI(api_key=api_key)
    
    # Tüm transcript dosyalarını bul
    transcript_files = sorted(Path(transcripts_folder).glob("*_transcript.txt"))
    
    if not transcript_files:
        print(f"❌ {transcripts_folder} klasöründe transcript bulunamadı!")
        return
    
    print(f"📁 {len(transcript_files)} toplantı transkripti bulundu")
    print("🚀 Action item çıkarma işlemi başlıyor...\n")
    
    all_action_items = []
    processed_count = 0
    error_count = 0
    
    for i, file_path in enumerate(transcript_files, 1):
        meeting_id = file_path.stem.replace("_transcript", "")
        
        print(f"[{i}/{len(transcript_files)}] İşleniyor: {meeting_id}...", end=" ")
        
        try:
            # Transcript dosyasını oku
            with open(file_path, 'r', encoding='utf-8') as f:
                transcript_text = f.read()
            
            # Eğer transcript çok uzunsa, sadece transcript kısmını al
            # (başlıktaki metadata'yı çıkar)
            if "TRANSCRIPT" in transcript_text:
                transcript_text = transcript_text.split("TRANSCRIPT")[1]
            
            # İlk 15000 karakteri al (token limiti için)
            # GPT-4o-mini için ~16K token limit var
            if len(transcript_text) > 15000:
                transcript_text = transcript_text[:15000] + "\n\n[Transcript kesildi...]"
            
            # OpenAI'a istek at
            result = extract_action_items_from_transcript(
                transcript_text, 
                meeting_id, 
                client
            )
            
            if result and "software_tasks" in result:
                # Her task'a meeting bilgisini ekle
                for item in result["software_tasks"]:
                    item["meeting_id"] = meeting_id
                    all_action_items.append(item)
                
                task_count = len(result['software_tasks'])
                if task_count > 0:
                    print(f"✅ {task_count} software task bulundu")
                else:
                    print(f"⚪ Software task yok")
                processed_count += 1
            else:
                print("⚠️  Sonuç alınamadı")
                error_count += 1
            
            # API rate limit'e takılmamak için kısa bekleme
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ Hata: {str(e)}")
            error_count += 1
    
    # Sonuçları DataFrame'e çevir ve kaydet
    if all_action_items:
        df = pd.DataFrame(all_action_items)
        
        # Sütun sırası
        columns = ["meeting_id", "title", "description", "assignee", "priority", "task_type", "tech_stack"]
        df = df[columns]
        
        # Excel'e kaydet
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Tüm software task'lar
            df.to_excel(writer, sheet_name='All_Software_Tasks', index=False)
            
            # Önceliğe göre grupla
            for priority in ['High', 'Medium', 'Low']:
                df_priority = df[df['priority'] == priority]
                if not df_priority.empty:
                    df_priority.to_excel(
                        writer, 
                        sheet_name=f'Priority_{priority}', 
                        index=False
                    )
            
            # Task type'a göre grupla
            for task_type in df['task_type'].unique():
                df_type = df[df['task_type'] == task_type]
                if not df_type.empty and len(df_type) >= 3:  # En az 3 task olanları göster
                    sheet_name = f'Type_{task_type[:20]}'  # Max 31 karakter
                    df_type.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Tech stack'e göre özet
            df_by_tech = df.groupby('tech_stack').size().reset_index(name='count')
            df_by_tech = df_by_tech.sort_values('count', ascending=False)
            df_by_tech.to_excel(writer, sheet_name='Summary_by_TechStack', index=False)
            
            # Task type'a göre özet
            df_by_type = df.groupby('task_type').size().reset_index(name='count')
            df_by_type = df_by_type.sort_values('count', ascending=False)
            df_by_type.to_excel(writer, sheet_name='Summary_by_TaskType', index=False)
            
            # Toplantıya göre özet
            df_by_meeting = df.groupby('meeting_id').size().reset_index(name='task_count')
            df_by_meeting = df_by_meeting.sort_values('task_count', ascending=False)
            df_by_meeting.to_excel(writer, sheet_name='Summary_by_Meeting', index=False)
        
        print(f"\n{'='*60}")
        print("✅ İşlem tamamlandı!")
        print(f"📊 Toplam: {processed_count} toplantı işlendi")
        print(f"� Toplam: {len(all_action_items)} SOFTWARE TASK çıkarıldı")
        print(f"⚪ Software task olmayan: {error_count} toplantı")
        print(f"💾 Sonuçlar kaydedildi: {output_file}")
        print(f"{'='*60}\n")
        
        # Öncelik dağılımı
        print("📊 Öncelik Dağılımı:")
        priority_dist = df['priority'].value_counts()
        for priority, count in priority_dist.items():
            print(f"   {priority}: {count}")
        
        print("\n📊 Task Type Dağılımı:")
        type_dist = df['task_type'].value_counts()
        for task_type, count in type_dist.items():
            print(f"   {task_type}: {count}")
        
        print("\n💻 Tech Stack Dağılımı:")
        tech_dist = df['tech_stack'].value_counts().head(10)
        for tech, count in tech_dist.items():
            print(f"   {tech}: {count}")
        
        # CSV de kaydet
        csv_file = output_file.replace('.xlsx', '.csv')
        df.to_csv(csv_file, index=False, encoding='utf-8')
        print(f"\n💾 CSV formatında da kaydedildi: {csv_file}")
        
        # JSON formatında kaydet
        json_file = output_file.replace('.xlsx', '.json')
        # Her task'ı güzel formatlı JSON olarak kaydet
        tasks_json = df.to_dict('records')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                "total_tasks": len(tasks_json),
                "total_meetings": df['meeting_id'].nunique(),
                "summary": {
                    "by_priority": df['priority'].value_counts().to_dict(),
                    "by_task_type": df['task_type'].value_counts().to_dict(),
                    "by_tech_stack": df['tech_stack'].value_counts().to_dict()
                },
                "tasks": tasks_json
            }, f, ensure_ascii=False, indent=2)
        print(f"💾 JSON formatında da kaydedildi: {json_file}")
        
        # TXT formatında kaydet (okunabilir format)
        txt_file = output_file.replace('.xlsx', '.txt')
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("SOFTWARE DEVELOPMENT TASKS - ICSI MEETING CORPUS\n")
            f.write("="*80 + "\n\n")
            f.write(f"Total Tasks: {len(df)}\n")
            f.write(f"Total Meetings: {df['meeting_id'].nunique()}\n")
            f.write(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("\n" + "="*80 + "\n\n")
            
            # Her toplantı için task'ları grupla
            for meeting_id in df['meeting_id'].unique():
                meeting_tasks = df[df['meeting_id'] == meeting_id]
                f.write(f"\n{'='*80}\n")
                f.write(f"Meeting: {meeting_id}\n")
                f.write(f"Tasks: {len(meeting_tasks)}\n")
                f.write(f"{'='*80}\n\n")
                
                for idx, task in meeting_tasks.iterrows():
                    f.write(f"[TASK #{idx+1}]\n")
                    f.write(f"Title: {task['title']}\n")
                    f.write(f"Description: {task['description']}\n")
                    f.write(f"Assignee: {task['assignee']}\n")
                    f.write(f"Priority: {task['priority']}\n")
                    f.write(f"Task Type: {task['task_type']}\n")
                    f.write(f"Tech Stack: {task['tech_stack']}\n")
                    f.write(f"{'-'*80}\n\n")
        
        print(f"💾 TXT formatında da kaydedildi: {txt_file}")
        
    else:
        print("\n❌ Hiç software task çıkarılamadı!")


def process_ami_transcripts(transcripts_folder, output_file, api_key):
    """
    AMI toplantı transkriptlerini işler.
    """
    # AMI için de aynı fonksiyon kullanılabilir
    process_icsi_transcripts(transcripts_folder, output_file, api_key)


if __name__ == "__main__":
    # API Key kontrolü
    if OPENAI_API_KEY == "YOUR_API_KEY_HERE":
        print("❌ HATA: Lütfen önce OPENAI_API_KEY değişkenine API key'inizi yazın!")
        print("\nKullanım:")
        print("1. Script dosyasını açın")
        print("2. OPENAI_API_KEY = 'sk-...' satırına API key'inizi yazın")
        print("3. Scripti tekrar çalıştırın")
        exit(1)
    
    print("🤖 OpenAI Action Item Extractor")
    print("="*60)
    
    # ICSI transcriptlerini işle
    if os.path.exists("data/transcripts/icsi"):
        print("\n📂 ICSI Transcriptler İşleniyor...")
        process_icsi_transcripts(
            transcripts_folder="data/transcripts/icsi",
            output_file="results/icsi_software_tasks.xlsx",
            api_key=OPENAI_API_KEY
        )
    
    # AMI transcriptlerini işle (eğer varsa)
    if os.path.exists("data/transcripts/ami"):
        print("\n📂 AMI Transcriptler İşleniyor...")
        process_ami_transcripts(
            transcripts_folder="data/transcripts/ami",
            output_file="results/ami_software_tasks.xlsx",
            api_key=OPENAI_API_KEY
        )
    
    print("\n✨ Tüm işlemler tamamlandı!")
