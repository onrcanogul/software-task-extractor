import pandas as pd

print("=" * 100)
print(" " * 30 + "ICSI MERGED MEETINGS - ÖZET RAPOR")
print("=" * 100)

# Excel dosyasını oku
xl_file = pd.ExcelFile('icsi_merged_meetings.xlsx')

print("\n📊 EXCEL DOSYASI İÇERİĞİ:")
print(f"  Dosya: icsi_merged_meetings.xlsx")
print(f"  Sheet sayısı: {len(xl_file.sheet_names)}")
print(f"  Sheet isimleri: {', '.join(xl_file.sheet_names)}")

# Her sheet'i oku
print("\n" + "=" * 100)
print("SHEET DETAYLARI")
print("=" * 100)

for sheet_name in xl_file.sheet_names:
    df = pd.read_excel('icsi_merged_meetings.xlsx', sheet_name=sheet_name)
    print(f"\n📄 {sheet_name}")
    print(f"  • Satır sayısı: {len(df):,}")
    print(f"  • Sütun sayısı: {len(df.columns)}")
    print(f"  • Sütunlar: {', '.join(df.columns[:10])}")
    if len(df.columns) > 10:
        print(f"    ... ve {len(df.columns) - 10} sütun daha")

# Summary sheet'i detaylı incele
summary_df = pd.read_excel('icsi_merged_meetings.xlsx', sheet_name='Meeting_Summary')

print("\n" + "=" * 100)
print("TOPLANTI ÖZETLERİ (Meeting_Summary Sheet)")
print("=" * 100)

print(f"\nİlk 10 toplantı:")
print("-" * 100)
display_cols = ['meeting_id', 'total_utterances', 'total_words', 'unique_speakers', 'duration_minutes']
print(summary_df[display_cols].head(10).to_string(index=False))

print(f"\n\nEn uzun 10 toplantı (kelime sayısına göre):")
print("-" * 100)
print(summary_df.nlargest(10, 'total_words')[display_cols].to_string(index=False))

print(f"\n\nEn kısa 10 toplantı (kelime sayısına göre):")
print("-" * 100)
print(summary_df.nsmallest(10, 'total_words')[display_cols].to_string(index=False))

# Örnek bir toplantının full transcript'ini göster
print("\n" + "=" * 100)
print("ÖRNEK TAM TRANSKRİPT (İlk toplantının ilk 30 satırı)")
print("=" * 100)

sample = summary_df.iloc[0]
print(f"\n📂 Toplantı: {sample['meeting_id']}")
print(f"   Utterance: {sample['total_utterances']}")
print(f"   Kelime: {sample['total_words']}")
print(f"   Konuşmacı: {sample['unique_speakers']}")
print(f"   Süre: {sample['duration_minutes']:.1f} dakika")
print(f"   Konuşmacı dağılımı: {sample['speaker_distribution']}")

print(f"\n" + "-" * 100)
transcript_lines = sample['full_transcript_with_speakers'].split('\n')[:30]
for i, line in enumerate(transcript_lines, 1):
    print(f"{i:3d}. {line}")

# Detaylı transkript sheet'inden örnek
detailed_df = pd.read_excel('icsi_merged_meetings.xlsx', sheet_name='Detailed_Transcripts')

print("\n" + "=" * 100)
print("DETAYLI TRANSKRİPT ÖRNEKLERİ (Detailed_Transcripts Sheet)")
print("=" * 100)

print("\nİlk 20 kayıt:")
print("-" * 100)
detail_cols = ['meeting_id', 'speaker', 'formatted_time', 'word_count', 'text']
print(detailed_df[detail_cols].head(20).to_string(index=False))

# Conversation Flow sheet'inden örnek
flow_df = pd.read_excel('icsi_merged_meetings.xlsx', sheet_name='Conversation_Flow')

print("\n" + "=" * 100)
print("KONUŞMA AKIŞI ÖRNEĞİ (İlk toplantının ilk 25 satırı)")
print("=" * 100)

sample_flow = flow_df.iloc[0]['conversation_flow'].split('\n')[:25]
for line in sample_flow:
    print(line)

# İstatistiksel analiz
print("\n" + "=" * 100)
print("İSTATİSTİKSEL ANALİZ")
print("=" * 100)

print("\n📊 Toplantı Süreleri:")
print(f"  • Minimum: {summary_df['duration_minutes'].min():.1f} dakika")
print(f"  • Maksimum: {summary_df['duration_minutes'].max():.1f} dakika")
print(f"  • Ortalama: {summary_df['duration_minutes'].mean():.1f} dakika")
print(f"  • Medyan: {summary_df['duration_minutes'].median():.1f} dakika")

print("\n📊 Utterance Sayıları:")
print(f"  • Minimum: {summary_df['total_utterances'].min():,}")
print(f"  • Maksimum: {summary_df['total_utterances'].max():,}")
print(f"  • Ortalama: {summary_df['total_utterances'].mean():.1f}")
print(f"  • Medyan: {summary_df['total_utterances'].median():.0f}")

print("\n📊 Kelime Sayıları:")
print(f"  • Minimum: {summary_df['total_words'].min():,}")
print(f"  • Maksimum: {summary_df['total_words'].max():,}")
print(f"  • Ortalama: {summary_df['total_words'].mean():.1f}")
print(f"  • Medyan: {summary_df['total_words'].median():.0f}")

print("\n📊 Konuşmacı Sayıları:")
print(f"  • Minimum: {summary_df['unique_speakers'].min()}")
print(f"  • Maksimum: {summary_df['unique_speakers'].max()}")
print(f"  • Ortalama: {summary_df['unique_speakers'].mean():.1f}")
print(f"  • Medyan: {summary_df['unique_speakers'].median():.0f}")

# Konuşmacı sayısına göre dağılım
print("\n📊 Konuşmacı Sayısına Göre Toplantı Dağılımı:")
speaker_dist = summary_df['unique_speakers'].value_counts().sort_index()
for speakers, count in speaker_dist.items():
    print(f"  • {speakers} konuşmacı: {count} toplantı")

print("\n" + "=" * 100)
print("✅ Rapor tamamlandı!")
print("=" * 100)
