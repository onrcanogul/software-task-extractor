import os
import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path
import re

class ICSIMeetingDatasetExtractor:
    def __init__(self, icsi_path):
        self.icsi_path = Path(icsi_path)
        self.dialogue_acts_path = self.icsi_path / "DialogueActs"
        self.words_path = self.icsi_path / "Words"
        self.segments_path = self.icsi_path / "Segments"
        self.speakers_path = self.icsi_path / "speakers.xml"
        
    def parse_speakers(self):
        """speakers.xml dosyasından konuşmacı bilgilerini çıkar"""
        speakers = {}
        try:
            tree = ET.parse(self.speakers_path)
            root = tree.getroot()
            
            # XML namespace'i kaldır
            for speaker in root.findall('.//{http://nite.sourceforge.net/}person'):
                speaker_id = speaker.get('{http://nite.sourceforge.net/}id')
                name = speaker.get('name', '')
                global_name = speaker.get('global_name', '')
                speakers[speaker_id] = {
                    'name': name,
                    'global_name': global_name
                }
        except Exception as e:
            print(f"Konuşmacı bilgileri okunamadı: {e}")
        
        return speakers
    
    def extract_meeting_id(self, filename):
        """Dosya adından toplantı ID'sini çıkar (örn: Bdb001)"""
        match = re.match(r'([A-Z][a-z]{2}\d{3})', filename)
        return match.group(1) if match else None
    
    def extract_participant_id(self, filename):
        """Dosya adından katılımcı ID'sini çıkar (örn: A, B, C)"""
        match = re.search(r'\.([A-Z])\.', filename)
        return match.group(1) if match else None
    
    def parse_words_file(self, words_file):
        """Words XML dosyasını parse et ve kelime-zaman eşleştirmesi yap"""
        words_dict = {}
        try:
            tree = ET.parse(words_file)
            root = tree.getroot()
            
            # Namespace tanımla
            ns = {'nite': 'http://nite.sourceforge.net/'}
            
            # w elementlerini bul (namespace olmadan)
            for word in root.findall('.//w'):
                word_id = word.get('{http://nite.sourceforge.net/}id')
                if word_id:
                    words_dict[word_id] = {
                        'text': word.text or '',
                        'starttime': word.get('starttime', ''),
                        'endtime': word.get('endtime', ''),
                        'type': word.get('c', '')
                    }
        except Exception as e:
            print(f"Kelime dosyası okunamadı {words_file}: {e}")
        
        return words_dict
    
    def extract_word_ids_from_href(self, href):
        """href string'inden word ID'lerini çıkar ve range'i genişlet"""
        # Format: "Bdb001.A.words.xml#id(Bdb001.w.691)..id(Bdb001.w.700)"
        # veya tek ID: "Bdb001.A.words.xml#id(Bdb001.w.691)"
        word_ids = []
        if href and '#id(' in href:
            ids_part = href.split('#')[1]
            # id(...)..id(...) formatını parse et
            id_matches = re.findall(r'id\(([^)]+)\)', ids_part)
            
            if len(id_matches) == 2:
                # Range var, başlangıç ve bitiş ID'leri
                start_id, end_id = id_matches
                # Sadece bu iki ID'yi döndür, words_dict'te tüm kelimeler var
                return [start_id, end_id]
            else:
                # Tek ID
                word_ids = id_matches
        return word_ids
    
    def get_text_from_word_ids(self, word_ids, words_dict):
        """Word ID'lerinden metni oluştur - range desteği ile"""
        if not word_ids:
            return ''
        
        # Eğer 2 ID varsa (range), aradaki tüm kelimeleri al
        if len(word_ids) == 2:
            start_id, end_id = word_ids
            
            # words_dict'teki tüm ID'leri sıralı listele
            all_ids = list(words_dict.keys())
            
            try:
                # Başlangıç ve bitiş indekslerini bul
                if start_id in all_ids and end_id in all_ids:
                    start_idx = all_ids.index(start_id)
                    end_idx = all_ids.index(end_id)
                    
                    # Aradaki tüm kelimeleri al
                    text_parts = []
                    for i in range(start_idx, end_idx + 1):
                        word_id = all_ids[i]
                        word_data = words_dict[word_id]
                        word_text = word_data['text']
                        if word_text and not word_text.startswith('<'):
                            text_parts.append(word_text)
                    
                    return ' '.join(text_parts)
            except (ValueError, KeyError):
                pass
        
        # Tek ID veya hata durumunda
        text_parts = []
        for word_id in word_ids:
            if word_id in words_dict:
                word_text = words_dict[word_id]['text']
                if word_text and not word_text.startswith('<'):
                    text_parts.append(word_text)
        return ' '.join(text_parts)
    
    def extract_meeting_data(self):
        """Tüm toplantı verilerini çıkar"""
        all_data = []
        
        # DialogueActs dosyalarını işle
        dialogue_files = sorted(self.dialogue_acts_path.glob("*.xml"))
        
        print(f"{len(dialogue_files)} dialogue-acts dosyası bulundu.")
        
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
                
                # Namespace tanımla
                ns = {'nite': 'http://nite.sourceforge.net/'}
                
                # dialogueact elementlerini bul (namespace olmadan)
                for da in root.findall('.//dialogueact'):
                    da_id = da.get('{http://nite.sourceforge.net/}id')
                    starttime = da.get('starttime', '')
                    endtime = da.get('endtime', '')
                    da_type = da.get('type', '')
                    adjacency = da.get('adjacency', '')
                    participant = da.get('participant', '')
                    channel = da.get('channel', '')
                    
                    # Child href'ten word ID'lerini çıkar (namespace ile)
                    child = da.find('.//{http://nite.sourceforge.net/}child')
                    text = ''
                    if child is not None:
                        href = child.get('href', '')
                        word_ids = self.extract_word_ids_from_href(href)
                        text = self.get_text_from_word_ids(word_ids, words_dict)
                    
                    all_data.append({
                        'meeting_id': meeting_id,
                        'participant_id': participant_id,
                        'participant': participant,
                        'dialogue_act_id': da_id,
                        'starttime': float(starttime) if starttime else None,
                        'endtime': float(endtime) if endtime else None,
                        'dialogue_act_type': da_type,
                        'adjacency': adjacency,
                        'channel': channel,
                        'text': text.strip()
                    })
                
                if idx % 10 == 0:
                    print(f"İşlenen dosya: {idx}/{len(dialogue_files)}")
                    
            except Exception as e:
                print(f"Hata oluştu {dialogue_file.name}: {e}")
                continue
        
        return pd.DataFrame(all_data)
    
    def save_to_excel(self, df, output_path="icsi_meeting_dataset.xlsx"):
        """DataFrame'i Excel'e kaydet"""
        df.to_excel(output_path, index=False, engine='openpyxl')
        print(f"\nDataset kaydedildi: {output_path}")
        print(f"Toplam kayıt sayısı: {len(df)}")
        print(f"Toplantı sayısı: {df['meeting_id'].nunique()}")
        print(f"\nSütunlar: {list(df.columns)}")
        print(f"\nİlk 5 kayıt:")
        print(df.head())
        
    def save_to_csv(self, df, output_path="icsi_meeting_dataset.csv"):
        """DataFrame'i CSV'ye kaydet"""
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"\nCSV kaydedildi: {output_path}")

def main():
    # ICSIplus klasör yolu
    icsi_path = "/Users/onurcanogul/Desktop/thesis/ICSIplus"
    
    print("ICSI Meeting Dataset Çıkarılıyor...")
    print("=" * 60)
    
    extractor = ICSIMeetingDatasetExtractor(icsi_path)
    
    # Konuşmacı bilgilerini parse et
    speakers = extractor.parse_speakers()
    print(f"\n{len(speakers)} konuşmacı bilgisi yüklendi.")
    
    # Toplantı verilerini çıkar
    print("\nToplantı verileri çıkarılıyor...")
    df = extractor.extract_meeting_data()
    
    if df.empty:
        print("Hiç veri bulunamadı!")
        return
    
    # Excel ve CSV'ye kaydet
    extractor.save_to_excel(df, "icsi_meeting_dataset.xlsx")
    extractor.save_to_csv(df, "icsi_meeting_dataset.csv")
    
    # İstatistikler
    print("\n" + "=" * 60)
    print("Dataset İstatistikleri:")
    print("=" * 60)
    print(f"Toplam utterance sayısı: {len(df)}")
    print(f"Toplantı sayısı: {df['meeting_id'].nunique()}")
    print(f"Katılımcı sayısı: {df['participant'].nunique()}")
    print(f"\nDialogue Act türleri ({df['dialogue_act_type'].nunique()} farklı tür):")
    print(df['dialogue_act_type'].value_counts().head(10))
    print(f"\nOrtalama utterance uzunluğu: {df['text'].str.split().str.len().mean():.2f} kelime")
    
    # Boş olmayan metinler
    non_empty = df[df['text'] != '']
    print(f"\nBoş olmayan metin sayısı: {len(non_empty)} / {len(df)}")

if __name__ == "__main__":
    main()
