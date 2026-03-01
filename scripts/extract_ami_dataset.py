import os
import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path
import re

class AMIMeetingDatasetExtractor:
    def __init__(self, ami_path):
        self.ami_path = Path(ami_path)
        self.dialogue_acts_path = self.ami_path / "dialogueActs" / "automaticAD" / "ASR_AS_CTM_v1.0_feb07"
        self.words_path = self.ami_path / "ASR" / "ASR_AS_CTM_v1.0_feb07"
        
    def extract_meeting_id(self, filename):
        """Dosya adından toplantı ID'sini çıkar (örn: ES2003a)"""
        match = re.match(r'([A-Z]{2}\d{4}[a-z])', filename)
        return match.group(1) if match else None
    
    def extract_participant_id(self, filename):
        """Dosya adından katılımcı ID'sini çıkar (örn: A, B, C, D)"""
        match = re.search(r'\.([A-D])\.', filename)
        return match.group(1) if match else None
    
    def parse_words_file(self, words_file):
        """Words XML dosyasını parse et"""
        words_dict = {}
        try:
            tree = ET.parse(words_file)
            root = tree.getroot()
            
            # ASR words'leri bul (nite:id="*.A.aw*" formatında)
            for word in root.findall('.//w'):
                word_id = word.get('{http://nite.sourceforge.net/}id')
                if word_id:
                    words_dict[word_id] = {
                        'text': word.text or '',
                        'starttime': word.get('starttime', ''),
                        'endtime': word.get('endtime', '')
                    }
        except Exception as e:
            print(f"Kelime dosyası okunamadı {words_file}: {e}")
        
        return words_dict
    
    def parse_da_type(self, da_pointer):
        """Dialogue act type'ı pointer'dan çıkar"""
        if da_pointer is not None:
            href = da_pointer.get('href', '')
            # Format: "da-types.xml#id(ami_da_4)"
            match = re.search(r'ami_da_(\d+)', href)
            if match:
                return f"ami_da_{match.group(1)}"
        return 'unknown'
    
    def extract_word_ids_from_children(self, dact_element):
        """dact elementinden child word ID'lerini çıkar"""
        word_ids = []
        children = dact_element.findall('.//{http://nite.sourceforge.net/}child')
        for child in children:
            href = child.get('href', '')
            # Format: "ES2003a.A.words.xml#id(ES2003a.A.aw1)"
            match = re.search(r'#id\(([^)]+)\)', href)
            if match:
                word_ids.append(match.group(1))
        return word_ids
    
    def get_text_from_word_ids(self, word_ids, words_dict):
        """Word ID'lerinden metni oluştur"""
        text_parts = []
        for word_id in word_ids:
            if word_id in words_dict:
                word_text = words_dict[word_id]['text']
                if word_text:
                    text_parts.append(word_text)
        return ' '.join(text_parts)
    
    def get_time_range(self, word_ids, words_dict):
        """Word ID'lerinden zaman aralığını bul"""
        start_times = []
        end_times = []
        
        for word_id in word_ids:
            if word_id in words_dict:
                st = words_dict[word_id]['starttime']
                et = words_dict[word_id]['endtime']
                if st:
                    try:
                        start_times.append(float(st))
                    except:
                        pass
                if et:
                    try:
                        end_times.append(float(et))
                    except:
                        pass
        
        if start_times and end_times:
            return min(start_times), max(end_times)
        return None, None
    
    def extract_meeting_data(self):
        """Tüm toplantı verilerini çıkar"""
        all_data = []
        
        # DialogueActs dosyalarını işle
        if not self.dialogue_acts_path.exists():
            print(f"Dialogue acts klasörü bulunamadı: {self.dialogue_acts_path}")
            return pd.DataFrame()
        
        dialogue_files = sorted(self.dialogue_acts_path.glob("*.xml"))
        
        print(f"{len(dialogue_files)} dialogue-act dosyası bulundu.")
        
        for idx, dialogue_file in enumerate(dialogue_files, 1):
            try:
                meeting_id = self.extract_meeting_id(dialogue_file.name)
                participant_id = self.extract_participant_id(dialogue_file.name)
                
                if not meeting_id or not participant_id:
                    continue
                
                # İlgili words dosyasını bul
                words_file = self.words_path / f"{meeting_id}.{participant_id}.words.xml"
                if not words_file.exists():
                    print(f"Words dosyası bulunamadı: {words_file}")
                    continue
                
                # Words dosyasını parse et
                words_dict = self.parse_words_file(words_file)
                
                # DialogueActs dosyasını parse et
                tree = ET.parse(dialogue_file)
                root = tree.getroot()
                
                # dact elementlerini bul
                for dact in root.findall('.//dact'):
                    dact_id = dact.get('{http://nite.sourceforge.net/}id')
                    
                    # DA type'ı al
                    da_pointer = dact.find('.//{http://nite.sourceforge.net/}pointer[@role="da-aspect"]')
                    da_type = self.parse_da_type(da_pointer)
                    
                    # Word ID'lerini çıkar
                    word_ids = self.extract_word_ids_from_children(dact)
                    
                    # Metni oluştur
                    text = self.get_text_from_word_ids(word_ids, words_dict)
                    
                    # Zaman aralığını bul
                    starttime, endtime = self.get_time_range(word_ids, words_dict)
                    
                    all_data.append({
                        'meeting_id': meeting_id,
                        'participant_id': participant_id,
                        'dialogue_act_id': dact_id,
                        'starttime': starttime,
                        'endtime': endtime,
                        'duration': endtime - starttime if starttime and endtime else None,
                        'dialogue_act_type': da_type,
                        'word_count': len(word_ids),
                        'text': text.strip()
                    })
                
                if idx % 50 == 0:
                    print(f"İşlenen dosya: {idx}/{len(dialogue_files)}")
                    
            except Exception as e:
                print(f"Hata oluştu {dialogue_file.name}: {e}")
                continue
        
        return pd.DataFrame(all_data)
    
    def save_to_excel(self, df, output_path="ami_meeting_dataset.xlsx"):
        """DataFrame'i Excel'e kaydet"""
        df.to_excel(output_path, index=False, engine='openpyxl')
        print(f"\nDataset kaydedildi: {output_path}")
        print(f"Toplam kayıt sayısı: {len(df)}")
        print(f"Toplantı sayısı: {df['meeting_id'].nunique()}")
        print(f"\nSütunlar: {list(df.columns)}")
        print(f"\nİlk 5 kayıt:")
        print(df.head())
        
    def save_to_csv(self, df, output_path="ami_meeting_dataset.csv"):
        """DataFrame'i CSV'ye kaydet"""
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"\nCSV kaydedildi: {output_path}")

def main():
    # AMI klasör yolu
    ami_path = "/Users/onurcanogul/Desktop/thesis/ami_public_auto_1.5.1"
    
    print("AMI Meeting Dataset Çıkarılıyor...")
    print("=" * 60)
    
    extractor = AMIMeetingDatasetExtractor(ami_path)
    
    # Toplantı verilerini çıkar
    print("\nToplantı verileri çıkarılıyor...")
    df = extractor.extract_meeting_data()
    
    if df.empty:
        print("Hiç veri bulunamadı!")
        return
    
    # Excel ve CSV'ye kaydet
    extractor.save_to_excel(df, "ami_meeting_dataset.xlsx")
    extractor.save_to_csv(df, "ami_meeting_dataset.csv")
    
    # İstatistikler
    print("\n" + "=" * 60)
    print("Dataset İstatistikleri:")
    print("=" * 60)
    print(f"Toplam utterance sayısı: {len(df)}")
    print(f"Toplantı sayısı: {df['meeting_id'].nunique()}")
    
    print(f"\nDialogue Act türleri ({df['dialogue_act_type'].nunique()} farklı tür):")
    print(df['dialogue_act_type'].value_counts().head(15))
    
    print(f"\nOrtalama utterance uzunluğu: {df['text'].str.split().str.len().mean():.2f} kelime")
    
    # Boş olmayan metinler
    non_empty = df[df['text'] != '']
    print(f"\nBoş olmayan metin sayısı: {len(non_empty)} / {len(df)}")
    
    # Toplantı bazında istatistikler
    meeting_stats = df.groupby('meeting_id').agg({
        'dialogue_act_id': 'count',
        'participant_id': 'nunique',
        'text': lambda x: x.str.split().str.len().sum()
    }).rename(columns={
        'dialogue_act_id': 'utterance_count',
        'participant_id': 'speaker_count',
        'text': 'total_words'
    })
    
    print(f"\nEn fazla utterance'lı toplantılar:")
    print(meeting_stats.nlargest(10, 'utterance_count'))

if __name__ == "__main__":
    main()
