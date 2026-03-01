import pandas as pd
import random

# Dataset'i oku
df = pd.read_csv('data/raw/icsi_meeting_dataset.csv')

print("=" * 100)
print(" " * 30 + "ICSI MEETING DATASET - TEXT METİNLERİ")
print("=" * 100)

# Kelime sayısını hesapla
df['word_count'] = df['text'].fillna('').str.split().str.len()

print(f"\n📊 GENEL İSTATİSTİKLER:")
print(f"  • Toplam utterance sayısı: {len(df):,}")
print(f"  • Boş olmayan metin sayısı: {df['text'].notna().sum():,}")
print(f"  • Ortalama kelime sayısı: {df['word_count'].mean():.2f}")
print(f"  • Medyan kelime sayısı: {df['word_count'].median():.0f}")
print(f"  • Maksimum kelime sayısı: {df['word_count'].max()}")

# Kelime sayısına göre dağılım
print(f"\n📈 KELİME SAYISI DAĞILIMI:")
print(f"  • 1-5 kelime: {len(df[df['word_count'] <= 5]):,} ({len(df[df['word_count'] <= 5])/len(df)*100:.1f}%)")
print(f"  • 6-10 kelime: {len(df[(df['word_count'] > 5) & (df['word_count'] <= 10)]):,} ({len(df[(df['word_count'] > 5) & (df['word_count'] <= 10)])/len(df)*100:.1f}%)")
print(f"  • 11-20 kelime: {len(df[(df['word_count'] > 10) & (df['word_count'] <= 20)]):,} ({len(df[(df['word_count'] > 10) & (df['word_count'] <= 20)])/len(df)*100:.1f}%)")
print(f"  • 20+ kelime: {len(df[df['word_count'] > 20]):,} ({len(df[df['word_count'] > 20])/len(df)*100:.1f}%)")

print("\n" + "=" * 100)
print("💬 ÖRNEK KONUŞMALAR (Rastgele 30 metin - farklı uzunluklarda)")
print("=" * 100)

# Farklı uzunluklarda örnekler
short = df[df['word_count'] <= 5].sample(5, random_state=42)
medium = df[(df['word_count'] > 5) & (df['word_count'] <= 15)].sample(10, random_state=42)
long = df[df['word_count'] > 15].sample(15, random_state=42)

all_samples = pd.concat([short, medium, long]).sample(frac=1, random_state=42)

for idx, (i, row) in enumerate(all_samples.iterrows(), 1):
    print(f"\n[{idx}] 📝 {row['word_count']:.0f} kelime | {row['meeting_id']} - {row['participant']}")
    print(f"    ⏱️  {row['starttime']:.1f}s - {row['endtime']:.1f}s | 🏷️  {row['dialogue_act_type']}")
    text = row['text'][:150] + '...' if len(row['text']) > 150 else row['text']
    print(f"    💬 \"{text}\"")

print("\n" + "=" * 100)
print("🔝 EN UZUN 10 KONUŞMA")
print("=" * 100)

longest = df.nlargest(10, 'word_count')
for idx, (i, row) in enumerate(longest.iterrows(), 1):
    print(f"\n[{idx}] 📏 {row['word_count']:.0f} kelime | {row['meeting_id']} - {row['participant']}")
    print(f"    ⏱️  {row['starttime']:.1f}s - {row['endtime']:.1f}s | 🏷️  {row['dialogue_act_type']}")
    print(f"    💬 \"{row['text'][:200]}...\"")

print("\n" + "=" * 100)
print("🎯 TOPLANTI BAZINDA ÖRNEKLER (Her toplantıdan birer örnek)")
print("=" * 100)

for meeting in sorted(df['meeting_id'].unique())[:15]:
    meeting_df = df[df['meeting_id'] == meeting]
    # Orta uzunlukta bir metin seç (5-20 kelime arası)
    sample = meeting_df[(meeting_df['word_count'] >= 5) & (meeting_df['word_count'] <= 20)]
    if len(sample) > 0:
        row = sample.sample(1, random_state=42).iloc[0]
        print(f"\n📂 {meeting} | {row['participant']} ({row['word_count']:.0f} kelime)")
        text = row['text'][:120] + '...' if len(row['text']) > 120 else row['text']
        print(f"   💬 \"{text}\"")

print("\n" + "=" * 100)
print("📊 DIALOGUE ACT TİPİNE GÖRE ÖRNEKLER")
print("=" * 100)

top_types = df['dialogue_act_type'].value_counts().head(10).index
for da_type in top_types:
    type_df = df[df['dialogue_act_type'] == da_type]
    count = len(type_df)
    avg_words = type_df['word_count'].mean()
    
    # Ortalama uzunlukta bir örnek seç
    sample = type_df[(type_df['word_count'] >= 5) & (type_df['word_count'] <= 15)]
    if len(sample) > 0:
        row = sample.sample(1, random_state=42).iloc[0]
        text = row['text'][:100] + '...' if len(row['text']) > 100 else row['text']
        print(f"\n🏷️  [{da_type}] - {count:,} adet | Ort: {avg_words:.1f} kelime")
        print(f"   Örnek: \"{text}\"")

print("\n" + "=" * 100)
print("✅ Dataset başarıyla analiz edildi!")
print("=" * 100)
