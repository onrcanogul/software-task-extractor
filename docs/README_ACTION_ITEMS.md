# Action Items Extraction - Kullanım Kılavuzu

## 🎯 Ne Yapar?

Bu script, toplantı transkriptlerini OpenAI API kullanarak analiz eder ve her toplantıdan:
- **Action Item'ları** (Yapılacak işler)
- **Sorumlular** (Eğer belirtilmişse)
- **Öncelikler** (High/Medium/Low)
- **Kategoriler** (Teknik/Araştırma/Test/Dokümantasyon vb.)

çıkarır.

## 📋 Kullanım Adımları

### 1. OpenAI API Key Alın

https://platform.openai.com/api-keys adresinden API key oluşturun.

### 2. API Key'i Scripte Ekleyin

`extract_action_items.py` dosyasını açın ve 6. satırdaki:

```python
OPENAI_API_KEY = "YOUR_API_KEY_HERE"
```

kısmını şu şekilde değiştirin:

```python
OPENAI_API_KEY = "sk-proj-xxxxxxxxxxxxx"  # Kendi API key'inizi yazın
```

### 3. Scripti Çalıştırın

```bash
python3 extract_action_items.py
```

## 📊 Çıktılar

Script şu dosyaları oluşturur:

### ICSI Dataset için:
- **icsi_action_items.xlsx** - 6 sheet içerir:
  - `All_Action_Items`: Tüm action item'lar
  - `Priority_High`: Yüksek öncelikli işler
  - `Priority_Medium`: Orta öncelikli işler
  - `Priority_Low`: Düşük öncelikli işler
  - `Summary_by_Category`: Kategori bazlı özet
  - `Summary_by_Meeting`: Toplantı bazlı özet

- **icsi_action_items.csv** - CSV formatında tüm veriler

### AMI Dataset için (eğer varsa):
- **ami_action_items.xlsx**
- **ami_action_items.csv**

## 📝 Excel Yapısı

Her action item şu kolonları içerir:

| Kolon | Açıklama | Örnek |
|-------|----------|-------|
| meeting_id | Toplantı ID | Bdb001 |
| title | Kısa başlık | "Belief-net mimarisini optimize et" |
| description | Detaylı açıklama | "Kombinatorik patlamayı önlemek için..." |
| assignee | Sorumlu kişi | "Johno" veya "Belirtilmedi" |
| priority | Öncelik | High / Medium / Low |
| category | Kategori | Teknik / Araştırma / Test / vb. |

## 💰 Maliyet

- **Model**: GPT-4o-mini (en ekonomik model)
- **Tahmini Maliyet**: 
  - 75 ICSI toplantısı ≈ $0.50 - $1.00
  - Her toplantı ~15K karakter = ~4K token
  - Input: $0.15 / 1M token
  - Output: $0.60 / 1M token

Daha detaylı analiz için `gpt-4o` kullanabilirsiniz (daha pahalı ama daha kaliteli).

## ⚙️ Ayarlar

Script içinde değiştirebileceğiniz parametreler:

### Model Seçimi (Satır 46):
```python
model="gpt-4o-mini"  # Ekonomik
# model="gpt-4o"     # Daha kaliteli ama pahalı
```

### Temperature (Satır 52):
```python
temperature=0.3  # Düşük = daha tutarlı, Yüksek = daha yaratıcı
```

### Transcript Uzunluk Limiti (Satır 104):
```python
if len(transcript_text) > 15000:  # Karakter limiti
```

## 🔍 Örnek Çıktı

```json
{
  "meeting_id": "Bdb001",
  "action_items": [
    {
      "title": "Wizard için daha iyi bir giriş hazırla",
      "description": "Sistem kendini tanıtmalı, kullanıcıya nasıl çalıştığını açıklamalı",
      "assignee": "Fey",
      "priority": "High",
      "category": "Geliştirme"
    },
    {
      "title": "Okuma görevini kısalt",
      "description": "5 dakikalık okuma çok uzun, kısaltılması gerekiyor",
      "assignee": "Belirtilmedi",
      "priority": "Medium",
      "category": "Araştırma"
    }
  ]
}
```

## ⚠️ Notlar

1. **Rate Limit**: Her istek arasında 1 saniye bekleme var
2. **Token Limit**: Her transcript max 15K karakter (uzun transkriptler kesiliyor)
3. **Hata Yönetimi**: Hata olursa o toplantı atlanır, diğerleri devam eder
4. **Progress Tracking**: Her toplantı işlenirken ekranda gösterilir

## 🐛 Sorun Giderme

**"API key hatası" alıyorsanız:**
- API key'i doğru kopyaladınız mı?
- OpenAI hesabınızda kredi var mı?

**"Rate limit" hatası:**
- Çok hızlı istek atıyorsunuz
- `time.sleep(1)` değerini artırın (örn: 2 saniye)

**"Token limit" hatası:**
- Transcript çok uzun
- Satır 104'teki limiti düşürün (örn: 10000)

## 📧 İletişim

Sorun yaşarsanız scripti durdurup (Ctrl+C) tekrar başlatabilirsiniz.
İşlenmiş toplantılar tekrar işlenmez (manuel kontrol gerekir).
