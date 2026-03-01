import pandas as pd

# Dataset'i oku
df = pd.read_csv('data/raw/icsi_meeting_dataset.csv')

print("=" * 80)
print("ICSI MEETING DATASET - TEXT METİNLERİ")
print("=" * 80)
print(f"\nToplam kayıt sayısı: {len(df)}")
print(f"Boş olmayan text sayısı: {df['text'].notna().sum()}")
print(f"Boş text sayısı: {df['text'].isna().sum()}")

# Text uzunluk istatistikleri
df['text_length'] = df['text'].fillna('').str.len()
df['word_count'] = df['text'].fillna('').str.split().str.len()

print("\n" + "=" * 80)
print("TEXT UZUNLUK İSTATİSTİKLERİ")
print("=" * 80)
print(f"Ortalama karakter sayısı: {df['text_length'].mean():.2f}")
print(f"Ortalama kelime sayısı: {df['word_count'].mean():.2f}")
print(f"Maksimum karakter sayısı: {df['text_length'].max()}")
print(f"Maksimum kelime sayısı: {df['word_count'].max()}")

print("\n" + "=" * 80)
print("İLK 30 TEXT METNİ ÖRNEKLERİ")
print("=" * 80)
for idx, row in df[df['text'].notna()].head(30).iterrows():
    print(f"\n[{idx}] Toplantı: {row['meeting_id']} | Katılımcı: {row['participant']} | Tür: {row['dialogue_act_type']}")
    print(f"    Zaman: {row['starttime']:.2f}s - {row['endtime']:.2f}s")
    print(f"    Metin: \"{row['text']}\"")

print("\n" + "=" * 80)
print("EN UZUN 15 TEXT METNİ")
print("=" * 80)
# En uzun metinleri bul
longest_texts = df.nlargest(15, 'text_length')
for idx, row in longest_texts.iterrows():
    print(f"\n[{idx}] {row['word_count']} kelime | {row['text_length']} karakter")
    print(f"    Toplantı: {row['meeting_id']} | Katılımcı: {row['participant']}")
    print(f"    Tür: {row['dialogue_act_type']}")
    print(f"    Metin: \"{row['text']}\"")

print("\n" + "=" * 80)
print("RASTGELE 20 TEXT ÖRNEĞİ")
print("=" * 80)
random_samples = df[df['text'].notna()].sample(20, random_state=42)
for idx, row in random_samples.iterrows():
    print(f"\n[{idx}] {row['meeting_id']} - {row['participant']} ({row['dialogue_act_type']})")
    print(f"    \"{row['text']}\"")

# Toplantı başına örnek metinler
print("\n" + "=" * 80)
print("HER TOPLANTIDAN BİR ÖRNEK METIN (İlk 10 Toplantı)")
print("=" * 80)
for meeting in df['meeting_id'].unique()[:10]:
    meeting_data = df[df['meeting_id'] == meeting]
    # En uzun metni al
    longest_in_meeting = meeting_data.nlargest(1, 'text_length')
    if not longest_in_meeting.empty:
        row = longest_in_meeting.iloc[0]
        print(f"\nToplantı: {meeting} | Katılımcı: {row['participant']}")
        print(f"  En uzun metin ({row['word_count']} kelime): \"{row['text']}\"")

print("\n" + "=" * 80)
