import pandas as pd
from pathlib import Path

class MeetingTranscriptMerger:
    def __init__(self, input_file="ami_meeting_dataset.csv"):
        self.input_file = input_file
        self.df = None
        
    def load_data(self):
        """Dataset'i yükle"""
        print(f"Dataset yükleniyor: {self.input_file}")
        self.df = pd.read_csv(self.input_file)
        print(f"✓ {len(self.df):,} kayıt yüklendi")
        return self
    
    def create_merged_transcripts(self):
        """Her toplantının tüm konuşmalarını birleştir"""
        print("\nToplantı transkriptleri birleştiriliyor...")
        
        merged_data = []
        
        # Her toplantı için
        for meeting_id in sorted(self.df['meeting_id'].unique()):
            meeting_df = self.df[self.df['meeting_id'] == meeting_id].copy()
            
            # Zamana göre sırala
            meeting_df = meeting_df.sort_values('starttime')
            
            # Toplantı metni oluştur (tüm konuşmaları birleştir)
            full_transcript = []
            for _, row in meeting_df.iterrows():
                if pd.notna(row['text']) and row['text'].strip():
                    # Konuşmacı bilgisi ile birlikte ekle
                    speaker_text = f"[{row['participant']}]: {row['text']}"
                    full_transcript.append(speaker_text)
            
            # Sadece metin (konuşmacı bilgisi olmadan)
            plain_transcript = []
            for _, row in meeting_df.iterrows():
                if pd.notna(row['text']) and row['text'].strip():
                    plain_transcript.append(row['text'])
            
            # İstatistikler
            total_utterances = len(meeting_df)
            total_words = meeting_df['text'].fillna('').str.split().str.len().sum()
            unique_speakers = meeting_df['participant'].nunique()
            duration = meeting_df['endtime'].max() - meeting_df['starttime'].min()
            
            # Konuşmacı dağılımı
            speaker_counts = meeting_df['participant'].value_counts().to_dict()
            speaker_distribution = ', '.join([f"{k}:{v}" for k, v in sorted(speaker_counts.items())])
            
            merged_data.append({
                'meeting_id': meeting_id,
                'total_utterances': total_utterances,
                'total_words': int(total_words),
                'unique_speakers': unique_speakers,
                'duration_seconds': round(duration, 2) if pd.notna(duration) else 0,
                'duration_minutes': round(duration / 60, 2) if pd.notna(duration) else 0,
                'speaker_distribution': speaker_distribution,
                'full_transcript_with_speakers': '\n'.join(full_transcript),
                'plain_transcript': ' '.join(plain_transcript),
                'first_utterance_time': meeting_df['starttime'].min(),
                'last_utterance_time': meeting_df['endtime'].max()
            })
        
        merged_df = pd.DataFrame(merged_data)
        print(f"✓ {len(merged_df)} toplantı birleştirildi")
        
        return merged_df
    
    def create_detailed_transcript(self):
        """Her toplantı için detaylı transkript (zaman damgalı, konuşmacılı)"""
        print("\nDetaylı transkriptler oluşturuluyor...")
        
        detailed_data = []
        
        for meeting_id in sorted(self.df['meeting_id'].unique()):
            meeting_df = self.df[self.df['meeting_id'] == meeting_id].copy()
            meeting_df = meeting_df.sort_values('starttime')
            
            for idx, row in meeting_df.iterrows():
                if pd.notna(row['text']) and row['text'].strip():
                    detailed_data.append({
                        'meeting_id': meeting_id,
                        'utterance_number': idx,
                        'speaker': row['participant'],
                        'participant_id': row['participant_id'],
                        'starttime': row['starttime'],
                        'endtime': row['endtime'],
                        'duration': row['endtime'] - row['starttime'] if pd.notna(row['endtime']) and pd.notna(row['starttime']) else 0,
                        'dialogue_act_type': row['dialogue_act_type'],
                        'text': row['text'],
                        'word_count': len(str(row['text']).split()),
                        'formatted_time': f"{int(row['starttime']//60):02d}:{int(row['starttime']%60):02d}",
                        'formatted_text': f"[{int(row['starttime']//60):02d}:{int(row['starttime']%60):02d}] {row['participant']}: {row['text']}"
                    })
        
        detailed_df = pd.DataFrame(detailed_data)
        print(f"✓ {len(detailed_df)} utterance detaylandırıldı")
        
        return detailed_df
    
    def create_conversation_flow(self):
        """Konuşma akışı - her toplantı için sıralı konuşmalar"""
        print("\nKonuşma akışları oluşturuluyor...")
        
        flow_data = []
        
        for meeting_id in sorted(self.df['meeting_id'].unique()):
            meeting_df = self.df[self.df['meeting_id'] == meeting_id].copy()
            meeting_df = meeting_df.sort_values('starttime')
            
            conversation_lines = []
            for idx, row in enumerate(meeting_df.itertuples(), 1):
                if pd.notna(row.text) and row.text.strip():
                    time_str = f"{int(row.starttime//60):02d}:{int(row.starttime%60):02d}"
                    line = f"{idx}. [{time_str}] {row.participant}: {row.text}"
                    conversation_lines.append(line)
            
            flow_data.append({
                'meeting_id': meeting_id,
                'conversation_flow': '\n'.join(conversation_lines)
            })
        
        flow_df = pd.DataFrame(flow_data)
        print(f"✓ {len(flow_df)} konuşma akışı oluşturuldu")
        
        return flow_df
    
    def save_to_excel(self, merged_df, detailed_df, flow_df, output_file="icsi_merged_meetings.xlsx"):
        """Birleştirilmiş dataları Excel'e kaydet (çoklu sheet)"""
        print(f"\nExcel dosyası oluşturuluyor: {output_file}")
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Sheet 1: Özet bilgiler
            merged_df.to_excel(writer, sheet_name='Meeting_Summary', index=False)
            
            # Sheet 2: Detaylı transkriptler
            detailed_df.to_excel(writer, sheet_name='Detailed_Transcripts', index=False)
            
            # Sheet 3: Konuşma akışları
            flow_df.to_excel(writer, sheet_name='Conversation_Flow', index=False)
            
            # Sheet 4: Toplantı metinleri (sadece metin)
            text_only = merged_df[['meeting_id', 'plain_transcript']].copy()
            text_only.to_excel(writer, sheet_name='Text_Only', index=False)
        
        print(f"✓ Excel dosyası kaydedildi: {output_file}")
        
    def save_individual_transcripts(self, output_dir="meeting_transcripts"):
        """Her toplantı için ayrı metin dosyası oluştur"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print(f"\nBireysel transkript dosyaları oluşturuluyor: {output_dir}/")
        
        for meeting_id in sorted(self.df['meeting_id'].unique()):
            meeting_df = self.df[self.df['meeting_id'] == meeting_id].copy()
            meeting_df = meeting_df.sort_values('starttime')
            
            # Dosya adı
            filename = output_path / f"{meeting_id}_transcript.txt"
            
            # Metin oluştur
            lines = [
                "=" * 80,
                f"AMI Meeting Transcript: {meeting_id}",
                "=" * 80,
                "",
                f"Total Utterances: {len(meeting_df)}",
                f"Unique Speakers: {meeting_df['participant'].nunique()}",
                f"Duration: {(meeting_df['endtime'].max() - meeting_df['starttime'].min()) / 60:.2f} minutes",
                "",
                "=" * 80,
                "TRANSCRIPT",
                "=" * 80,
                ""
            ]
            
            for idx, row in enumerate(meeting_df.itertuples(), 1):
                if pd.notna(row.text) and row.text.strip():
                    time_str = f"{int(row.starttime//60):02d}:{int(row.starttime%60):02d}"
                    lines.append(f"[{idx:04d}] [{time_str}] {row.participant}: {row.text}")
            
            # Dosyaya yaz
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
        
        print(f"✓ {len(self.df['meeting_id'].unique())} transkript dosyası oluşturuldu")
    
    def print_statistics(self, merged_df):
        """İstatistikleri yazdır"""
        print("\n" + "=" * 80)
        print("TOPLANTI İSTATİSTİKLERİ")
        print("=" * 80)
        
        print(f"\nToplam Toplantı Sayısı: {len(merged_df)}")
        print(f"Toplam Utterance Sayısı: {merged_df['total_utterances'].sum():,}")
        print(f"Toplam Kelime Sayısı: {merged_df['total_words'].sum():,}")
        
        print(f"\nOrtalama İstatistikler:")
        print(f"  • Toplantı başına utterance: {merged_df['total_utterances'].mean():.1f}")
        print(f"  • Toplantı başına kelime: {merged_df['total_words'].mean():.1f}")
        print(f"  • Toplantı başına konuşmacı: {merged_df['unique_speakers'].mean():.1f}")
        print(f"  • Ortalama toplantı süresi: {merged_df['duration_minutes'].mean():.1f} dakika")
        
        print(f"\nEn uzun toplantılar (kelime sayısına göre):")
        top5 = merged_df.nlargest(5, 'total_words')[['meeting_id', 'total_words', 'total_utterances', 'duration_minutes']]
        for idx, row in top5.iterrows():
            print(f"  • {row['meeting_id']}: {row['total_words']:,} kelime, {row['total_utterances']} utterance, {row['duration_minutes']:.1f} dk")
        
        print(f"\nEn fazla konuşmacılı toplantılar:")
        top5_speakers = merged_df.nlargest(5, 'unique_speakers')[['meeting_id', 'unique_speakers', 'total_utterances']]
        for idx, row in top5_speakers.iterrows():
            print(f"  • {row['meeting_id']}: {row['unique_speakers']} konuşmacı, {row['total_utterances']} utterance")
        
        print("\n" + "=" * 80)

def main():
    print("=" * 80)
    print(" " * 25 + "AMI MEETING TRANSCRIPT MERGER")
    print("=" * 80)
    
    # Merger oluştur
    merger = MeetingTranscriptMerger("data/raw/ami_meeting_dataset.csv")
    
    # Veriyi yükle
    merger.load_data()
    
    # Birleştirilmiş transkriptler oluştur
    merged_df = merger.create_merged_transcripts()
    
    # Detaylı transkript
    detailed_df = merger.create_detailed_transcript()
    
    # Konuşma akışı
    flow_df = merger.create_conversation_flow()
    
    # Excel'e kaydet
    merger.save_to_excel(merged_df, detailed_df, flow_df, "data/raw/ami_merged_meetings.xlsx")
    
    # Bireysel transkript dosyaları oluştur
    merger.save_individual_transcripts("data/transcripts/ami")
    
    # İstatistikleri yazdır
    merger.print_statistics(merged_df)
    
    # Örnek toplantı göster
    print("\n" + "=" * 80)
    print("ÖRNEK TOPLANTI TRANSKRİPTİ (İlk 20 satır)")
    print("=" * 80)
    
    sample_meeting = merged_df.iloc[0]
    print(f"\nToplantı: {sample_meeting['meeting_id']}")
    print(f"Utterance: {sample_meeting['total_utterances']}")
    print(f"Kelime: {sample_meeting['total_words']}")
    print(f"Konuşmacı: {sample_meeting['unique_speakers']}")
    print(f"Süre: {sample_meeting['duration_minutes']:.1f} dakika")
    print(f"\nİlk 20 satır:")
    print("-" * 80)
    
    transcript_lines = sample_meeting['full_transcript_with_speakers'].split('\n')[:20]
    for line in transcript_lines:
        print(line)
    
    print("\n" + "=" * 80)
    print("✅ İşlem tamamlandı!")
    print("=" * 80)
    print(f"\n📁 Oluşturulan dosyalar:")
    print(f"  • ami_merged_meetings.xlsx (4 sheet: Summary, Detailed, Flow, Text Only)")
    print(f"  • ami_meeting_transcripts/ klasöründe {len(merged_df)} adet .txt dosyası")
    print("=" * 80)

if __name__ == "__main__":
    main()
