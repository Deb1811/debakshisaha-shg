import pandas as pd
import numpy as np
import google.generativeai as genai
import cv2
from PIL import Image
import re
from datetime import datetime
import json
import os
import time
from typing import Dict, List, Tuple, Optional
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

import pickle
from scipy import stats

class DynamicSHGLedgerAnalyzer:
    def __init__(self, gemini_api_key: str = None, model_path: str = 'shg_ridge_credit_model.pkl'):
        """Initialize the SHG Ledger Analyzer"""
        self.setup_apis(gemini_api_key)
        self.load_credit_model(model_path)
        self.detected_language = 'english'
        
        # Enhanced language patterns with weights
        self.language_patterns = {
            'hindi': {
                'keywords': ['रुपये', 'नाम', 'राशि', 'तारीख', 'सदस्य', 'बचत', 'लोन', 'जमा', 'ऋण', 'कर्ज', 'भुगतान'],
                'script_range': (0x0900, 0x097F),  # Devanagari script range
                'weight': 1.5
            },
            'english': {
                'keywords': ['rupees', 'name', 'amount', 'date', 'member', 'savings', 'loan', 'deposit', 'repayment'],
                'script_range': (0x0041, 0x007A),  # Latin script
                'weight': 1.0
            },
            'tamil': {
                'keywords': ['ரூபாய்', 'பெயர்', 'தொகை', 'தேதி', 'உறுப்பினர்', 'சேமிப்பு', 'கடன்'],
                'script_range': (0x0B80, 0x0BFF),
                'weight': 1.5
            },
            'telugu': {
                'keywords': ['రూపాయలు', 'పేరు', 'మొత్తం', 'తేదీ', 'సభ్యుడు', 'పొదుపు', 'రుణం'],
                'script_range': (0x0C00, 0x0C7F),
                'weight': 1.5
            },
            'kannada': {
                'keywords': ['ರೂಪಾಯಿ', 'ಹೆಸರು', 'ಮೊತ್ತ', 'ದಿನಾಂಕ', 'ಸದಸ್ಯ', 'ಉಳಿತಾಯ', 'ಸಾಲ'],
                'script_range': (0x0C80, 0x0CFF),
                'weight': 1.5
            },
            'bengali': {
                'keywords': ['টাকা', 'নাম', 'পরিমাণ', 'তারিখ', 'সদস্য', 'সঞ্চয়', 'ঋণ'],
                'script_range': (0x0980, 0x09FF),
                'weight': 1.5
            },
            'gujarati': {
                'keywords': ['રૂપિયા', 'નામ', 'રકમ', 'તારીખ', 'સભ્ય', 'બચત', 'લોન'],
                'script_range': (0x0A80, 0x0AFF),
                'weight': 1.5
            }
        }
        
        # Comprehensive translations for all output text
        self.translations = {
            'hindi': {
                # Table headers
                'Member': 'सदस्य',
                'SHG': 'एसएचजी स्कोर',
                'Credit': 'क्रेडिट स्कोर',
                'Behavioral': 'व्यवहार स्कोर',
                'Inclusion': 'समावेशन स्कोर',
                'Eligibility': 'पात्रता',
                'MaxLoan': 'अधिकतम ऋण',
                'Ratio': 'अनुपात',
                
                # Eligibility categories
                'High': 'उच्च',
                'Good': 'अच्छा',
                'Medium': 'मध्यम',
                'Low': 'कम',
                'Very Low': 'बहुत कम',
                'Excellent': 'उत्कृष्ट',
                'Fair': 'ठीक',
                'Poor': 'खराब',
                
                # Labels
                'Language': 'भाषा',
                'Confidence': 'विश्वास स्तर',
                'Total Members': 'कुल सदस्य',
                'Total Transactions': 'कुल लेनदेन',
                'Total Amount': 'कुल राशि',
                'Avg SHG Score': 'औसत एसएचजी स्कोर',
                'Avg Credit Score': 'औसत क्रेडिट स्कोर',
                'Analysis Time': 'विश्लेषण समय',
                
                # Titles
                'SHG LEDGER ANALYSIS RESULTS': 'एसएचजी खाता विश्लेषण परिणाम',
                'MEMBER ANALYSIS': 'सदस्य विश्लेषण',
                'SHG Ledger Analyzer': 'एसएचजी खाता विश्लेषक',
                'Upload your ledger image for AI-powered analysis': 'एआई-संचालित विश्लेषण के लिए अपनी खाता छवि अपलोड करें',
                'Upload and Analyze': 'अपलोड करें और विश्लेषण करें',
                'Analyzing...': 'विश्लेषण हो रहा है...',
                'History': 'इतिहास',
                'members': 'सदस्य',
                
                # Transaction types
                'Deposit': 'जमा',
                'Loan': 'ऋण',
                'Repayment': 'भुगतान',
                
                # Additional UI elements
                'No analysis history yet': 'अभी तक कोई विश्लेषण इतिहास नहीं है',
                'Click to upload': 'अपलोड करने के लिए क्लिक करें',
                'or drag and drop': 'या ड्रैग और ड्रॉप करें',
                'PNG, JPG or JPEG (Max 10MB)': 'पीएनजी, जेपीजी या जेपीईजी (अधिकतम 10एमबी)',
                'Error analyzing ledger': 'खाता विश्लेषण में त्रुटि',
                'Please select a file first!': 'कृपया पहले एक फ़ाइल चुनें!',
                'No valid member data could be extracted from the ledger image. Please ensure the image is clear and contains transaction data.': 'खाता छवि से कोई वैध सदस्य डेटा निकाला नहीं जा सका। कृपया सुनिश्चित करें कि छवि स्पष्ट है और लेनदेन डेटा है।',
            },
            'tamil': {
                'Member': 'உறுப்பினர்',
                'SHG': 'எஸ்.எச்.ஜி மதிப்பெண்',
                'Credit': 'கடன் மதிப்பெண்',
                'Behavioral': 'நடத்தை மதிப்பெண்',
                'Inclusion': 'உள்ளடக்க மதிப்பெண்',
                'Eligibility': 'தகுதி',
                'MaxLoan': 'அதிகபட்ச கடன்',
                'Ratio': 'விகிதம்',
                'High': 'உயர்',
                'Good': 'நல்ல',
                'Medium': 'நடுத்தர',
                'Low': 'குறைந்த',
                'Very Low': 'மிகக் குறைந்த',
                'Language': 'மொழி',
                'Confidence': 'நம்பிக்கை',
                'Total Members': 'மொத்த உறுப்பினர்கள்',
                'Total Transactions': 'மொத்த பரிவர்த்தனைகள்',
                'Total Amount': 'மொத்த தொகை',
                'SHG Ledger Analyzer': 'எஸ்.எச்.ஜி கணக்கு பகுப்பாய்வி',
                'Deposit': 'வைப்பு',
                'Loan': 'கடன்',
                'Repayment': 'திருப்பிச் செலுத்துதல்'
            },
            'telugu': {
                'Member': 'సభ్యుడు',
                'SHG': 'ఎస్.హెచ్.జి స్కోర్',
                'Credit': 'క్రెడిట్ స్కోర్',
                'Behavioral': 'ప్రవర్తన స్కోర్',
                'Inclusion': 'చేర్పు స్కోర్',
                'Eligibility': 'అర్హత',
                'MaxLoan': 'గరిష్ట రుణం',
                'Ratio': 'నిష్పత్తి',
                'High': 'అధిక',
                'Good': 'మంచి',
                'Medium': 'మధ్యస్థ',
                'Low': 'తక్కువ',
                'Language': 'భాష',
                'Total Members': 'మొత్తం సభ్యులు',
                'Total Transactions': 'మొత్తం లావాదేవీలు',
                'SHG Ledger Analyzer': 'ఎస్.హెచ్.జి ఖాతా విశ్లేషణ',
                'Deposit': 'డిపాజిట్',
                'Loan': 'రుణం',
                'Repayment': 'తిరిగి చెల్లింపు'
            },
            'kannada': {
                'Member': 'ಸದಸ್ಯ',
                'SHG': 'ಎಸ್.ಹೆಚ್.ಜಿ ಸ್ಕೋರ್',
                'Credit': 'ಕ್ರೆಡಿಟ್ ಸ್ಕೋರ್',
                'Behavioral': 'ವರ್ತನೆ ಸ್ಕೋರ್',
                'Eligibility': 'ಅರ್ಹತೆ',
                'MaxLoan': 'ಗರಿಷ್ಠ ಸಾಲ',
                'High': 'ಹೆಚ್ಚು',
                'Good': 'ಉತ್ತಮ',
                'Medium': 'ಮಧ್ಯಮ',
                'Low': 'ಕಡಿಮೆ',
                'Language': 'ಭಾಷೆ',
                'Total Members': 'ಒಟ್ಟು ಸದಸ್ಯರು',
                'SHG Ledger Analyzer': 'ಎಸ್.ಹೆಚ್.ಜಿ ಖಾತೆ ವಿಶ್ಲೇಷಕ',
                'Deposit': 'ಠೇವಣಿ',
                'Loan': 'ಸಾಲ',
                'Repayment': 'ಮರುಪಾವತಿ'
            },
            'bengali': {
                'Member': 'সদস্য',
                'SHG': 'এসএইচজি স্কোর',
                'Credit': 'ক্রেডিট স্কোর',
                'Eligibility': 'যোগ্যতা',
                'High': 'উচ্চ',
                'Good': 'ভাল',
                'Medium': 'মাঝারি',
                'Low': 'কম',
                'Language': 'ভাষা',
                'Total Members': 'মোট সদস্য',
                'SHG Ledger Analyzer': 'এসএইচজি খাতা বিশ্লেষক',
                'Deposit': 'জমা',
                'Loan': 'ঋণ',
                'Repayment': 'পরিশোধ'
            },
            'gujarati': {
                'Member': 'સભ્ય',
                'SHG': 'એસએચજી સ્કોર',
                'Credit': 'ક્રેડિટ સ્કોર',
                'Eligibility': 'યોગ્યતા',
                'High': 'ઉચ્ચ',
                'Good': 'સારું',
                'Medium': 'મધ્યમ',
                'Low': 'નીચું',
                'Language': 'ભાષા',
                'Total Members': 'કુલ સભ્યો',
                'SHG Ledger Analyzer': 'એસએચજી ખાતા વિશ્લેષક',
                'Deposit': 'થાપણ',
                'Loan': 'લોન',
                'Repayment': 'ચુકવણી'
            },
            'english': {}  # No translation needed
        }
        
        self.risk_weights = {
            'repayment_history': 0.35,
            'transaction_regularity': 0.20,
            'amount_consistency': 0.15,
            'social_metrics': 0.15,
            'temporal_patterns': 0.10,
            'behavioral_score': 0.05
        }

    def setup_apis(self, gemini_key):
        self.use_gemini = False
        if gemini_key:
            try:
                genai.configure(api_key=gemini_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
                self.use_gemini = True
                print("✅ Gemini API configured")
            except Exception as e:
                print(f"⚠ Gemini setup failed: {e}")
                self.use_gemini = False

    def load_credit_model(self, model_path: str):
        try:
            if os.path.exists(model_path):
                with open(model_path, 'rb') as f:
                    self.credit_model = pickle.load(f)
                print(f"✅ Credit model loaded from {model_path}")
            else:
                print(f"⚠ Model file not found: {model_path}")
                self.credit_model = None
        except Exception as e:
            print(f"⚠ Model loading failed: {e}")
            self.credit_model = None

    def detect_language(self, text: str) -> Tuple[str, float]:
        """Enhanced language detection using multiple methods"""
        language_scores = {}
        text_lower = text.lower()
        
        # Initialize scores
        for lang in self.language_patterns.keys():
            language_scores[lang] = 0
        
        # Method 1: Unicode script detection (MOST IMPORTANT - weighted heavily)
        total_chars = max(len([c for c in text if not c.isspace() and not c.isdigit()]), 1)
        
        for lang, config in self.language_patterns.items():
            script_start, script_end = config['script_range']
            script_chars = sum(1 for char in text if script_start <= ord(char) <= script_end)
            script_percentage = script_chars / total_chars
            
            # Heavy weight for script detection
            language_scores[lang] += script_percentage * 100 * config['weight']
        
        # Method 2: Keyword matching
        for lang, config in self.language_patterns.items():
            keyword_count = sum(1 for keyword in config['keywords'] if keyword in text_lower)
            language_scores[lang] += keyword_count * 5 * config['weight']
        
        # Method 3: Specific Hindi patterns (boost Hindi detection)
        hindi_indicators = ['दिनांक', 'सदस्य', 'लेनदेन', 'प्रकार', 'राशि', 'शेष', 'देवी', 'सिंह', 
                           'जमा', 'ऋण', 'कर्ज', 'भुगतान', 'चुकौती', 'बचत', 'उमा', 'रमा', 'मोहन']
        hindi_pattern_count = sum(1 for indicator in hindi_indicators if indicator in text)
        if hindi_pattern_count > 0:
            language_scores['hindi'] += hindi_pattern_count * 10
        
        # Method 4: Check for Devanagari numerals and characters
        devanagari_chars = sum(1 for char in text if '\u0900' <= char <= '\u097F')
        if devanagari_chars > 10:  # Significant Hindi content
            language_scores['hindi'] += 50
        
        # Method 5: English patterns (only boost if significant English content)
        english_words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
        if len(english_words) > 5:
            language_scores['english'] += len(english_words) * 2
        
        print(f"🔍 Language Detection Scores: {language_scores}")
        print(f"📊 Total non-space chars: {total_chars}, Devanagari chars: {devanagari_chars}")
        
        if not any(language_scores.values()) or max(language_scores.values()) == 0:
            detected_lang = 'english'
            confidence = 0.5
        else:
            detected_lang = max(language_scores, key=language_scores.get)
            max_score = language_scores[detected_lang]
            total_score = sum(language_scores.values())
            confidence = min(max_score / max(total_score, 1), 0.99)
            
            # Boost confidence if clear Hindi script
            if detected_lang == 'hindi' and devanagari_chars > 20:
                confidence = max(confidence, 0.85)
        
        # Store detected language for translation
        self.detected_language = detected_lang
        
        print(f"✅ Detected Language: {detected_lang.upper()} (confidence: {confidence:.2f})")
        
        return detected_lang, confidence

    def translate(self, text: str, lang: str = None) -> str:
        """Translate text to detected language"""
        if lang is None:
            lang = self.detected_language
        
        if lang == 'english' or lang not in self.translations:
            return text
        
        return self.translations[lang].get(text, text)

    def preprocess_image(self, image_path: str) -> Image.Image:
        """Preprocess image for better OCR"""
        try:
            img = cv2.imread(image_path)
            if img is None:
                return Image.open(image_path)
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            denoised = cv2.fastNlMeansDenoising(gray)
            thresh = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                         cv2.THRESH_BINARY, 11, 2)
            pil_image = Image.fromarray(thresh)
            
            if max(pil_image.size) > 1024:
                pil_image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            
            return pil_image
        except Exception as e:
            print(f"Image preprocessing error: {e}")
            return Image.open(image_path)

    def process_ledger_image(self, image_path: str) -> str:
        """Extract text from ledger image using OCR - Multi-language support"""
        try:
            if self.use_gemini:
                processed_image = self.preprocess_image(image_path)
                prompt = """Extract ALL transaction data from this SHG (Self Help Group) ledger image. 

CRITICAL: Preserve the ORIGINAL script/language of member names. DO NOT transliterate.

For HINDI ledgers (देवनागरी script):
- Extract: दिनांक (Date), सदस्य नाम (Member Name - KEEP IN HINDI), लेनदेन प्रकार (Transaction Type), राशि (Amount)
- IMPORTANT: Keep names exactly as written: रमा देवी, मोहन सिंह, सीता देवी (do NOT convert to Rama Devi, Mohan Singh, etc.)
- Common Hindi terms: जमा/बचत=Deposit, ऋण/कर्ज/लोन=Loan, भुगतान/वापसी/चुकौती=Repayment

For ENGLISH ledgers:
- Extract: Date, Member Name, Transaction Type, Amount
- Keep names as written in English

OUTPUT FORMAT (pipe-separated):
Date | Member Name (ORIGINAL SCRIPT) | Transaction Type (English) | Amount

Examples for HINDI ledger:
Hindi Input: 2024-01 | रमा देवी | जमा | 800
Output: 2024-01-01 | रमा देवी | Deposit | 800

Hindi Input: 2024-03 | मोहन सिंह | ऋण | 5000  
Output: 2024-03-01 | मोहन सिंह | Loan | 5000

For TAMIL ledger:
Tamil Input: 2024-01 | சீதா தேவி | வைப்பு | 500
Output: 2024-01-01 | சீதா தேவி | Deposit | 500

CRITICAL RULES:
1. DO NOT transliterate names - keep original script (रमा देवी NOT Rama Devi)
2. Convert dates to YYYY-MM-DD format
3. Translate transaction types to English: Deposit, Loan, or Repayment
4. Extract numeric amounts only"""
                
                time.sleep(1)
                response = self.model.generate_content([prompt, processed_image])
                extracted_text = response.text if response.text else ""
                
                # Also get raw OCR text for language detection
                processed_image_pil = self.preprocess_image(image_path)
                config = r'--oem 3 --psm 6 -l hin+eng+tel+tam+kan+ben+guj'
                raw_ocr_text = pytesseract.image_to_string(processed_image_pil, config=config)
                
                # Combine both for better language detection
                combined_text = raw_ocr_text + "\n" + extracted_text
                print(f"📝 Raw OCR sample: {raw_ocr_text[:200]}")
                
                return combined_text
            else:
                processed_image = self.preprocess_image(image_path)
                config = r'--oem 3 --psm 6 -l hin+eng+tel+tam+kan+ben+guj'
                return pytesseract.image_to_string(processed_image, config=config)
                
        except Exception as e:
            print(f"Error processing image: {e}")
            return ""

    def parse_ledger_data(self, extracted_text: str) -> pd.DataFrame:
        """Parse extracted text into structured data"""
        if not extracted_text.strip():
            raise ValueError("No text extracted from image. Please provide a valid ledger image.")
        
        print(f"📄 Extracted text sample:\n{extracted_text[:500]}\n")
        
        df = self.manual_parse_text(extracted_text)
        
        if not df.empty:
            return df
            
        if self.use_gemini:
            try:
                print("🤖 Trying Gemini structured parsing...")
                parsing_prompt = f"""
                Parse this ledger data and return ONLY a JSON array:
                {extracted_text[:2000]}
                
                Format: [{{"date":"YYYY-MM-DD","member":"name","type":"Deposit|Loan|Repayment","amount":number}}]
                """
                
                response = self.model.generate_content(parsing_prompt)
                if response.text:
                    json_text = response.text.strip()
                    json_text = re.sub(r'^```json\s*', '', json_text)
                    json_text = re.sub(r'^```\s*', '', json_text)
                    json_text = re.sub(r'\s*```$', '', json_text)
                    json_text = json_text.strip()
                    
                    data = json.loads(json_text)
                    if isinstance(data, dict):
                        data = data.get('transactions', data.get('data', []))
                    
                    if data:
                        df = pd.DataFrame(data)
                        return self.clean_parsed_data(df)
            except Exception as e:
                print(f"Gemini parsing failed: {e}")
        
        raise ValueError("Could not parse any valid transactions from the ledger image")

    def manual_parse_text(self, extracted_text):
        """Enhanced manual parser with multi-language support - PRESERVES ORIGINAL NAMES"""
        lines = extracted_text.split("\n")
        transactions = []

        # Multi-language transaction type mappings
        type_mappings = {
            # Hindi
            'जमा': 'Deposit', 'बचत': 'Deposit', 'जमाराशि': 'Deposit',
            'ऋण': 'Loan', 'कर्ज': 'Loan', 'लोन': 'Loan', 'उधार': 'Loan',
            'भुगतान': 'Repayment', 'वापसी': 'Repayment', 'चुकौती': 'Repayment',
            # Tamil
            'வைப்பு': 'Deposit', 'சேமிப்பு': 'Deposit',
            'கடன்': 'Loan',
            'திருப்பிச்': 'Repayment', 'செலுத்துதல்': 'Repayment',
            # Telugu
            'డిపాజిట్': 'Deposit', 'పొదుపు': 'Deposit',
            'రుణం': 'Loan',
            'తిరిగి': 'Repayment', 'చెల్లింపు': 'Repayment',
            # Kannada
            'ಠೇವಣಿ': 'Deposit', 'ಉಳಿತಾಯ': 'Deposit',
            'ಸಾಲ': 'Loan',
            'ಮರುಪಾವತಿ': 'Repayment',
            # Bengali
            'জমা': 'Deposit', 'সঞ্চয়': 'Deposit',
            'ঋণ': 'Loan',
            'পরিশোধ': 'Repayment',
            # Gujarati
            'થાપણ': 'Deposit', 'બચત': 'Deposit',
            'લોન': 'Loan',
            'ચુકવણી': 'Repayment',
            # English
            'deposit': 'Deposit', 'save': 'Deposit', 'saving': 'Deposit', 'credit': 'Deposit',
            'loan': 'Loan', 'advance': 'Loan', 'borrow': 'Loan',
            'repayment': 'Repayment', 'payment': 'Repayment', 'repay': 'Repayment'
        }

        for line in lines:
            line = line.strip()
            if not line or len(line) < 5:
                continue

            # Pattern 1: Pipe-separated format (PRESERVES ORIGINAL NAMES)
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 4:
                    try:
                        date_str = parts[0]
                        if re.match(r'\d{2,4}[-/]\d{2}[-/]\d{2,4}', date_str):
                            date_str = self.normalize_date(date_str)
                            
                            # KEEP ORIGINAL NAME - don't transliterate
                            member_name = parts[1].strip()
                            
                            trans_type = parts[2].strip()
                            trans_type_normalized = type_mappings.get(trans_type.lower(), trans_type)
                            
                            transactions.append({
                                "Date": date_str,
                                "Member": member_name,  # Original script preserved
                                "TransactionType": trans_type_normalized,
                                "Amount": float(parts[3].replace(',', '').replace('₹', '').replace('/-', '').strip())
                            })
                            continue
                    except:
                        pass

            # Pattern 2: Extract with native script names preserved
            for keyword, trans_type in type_mappings.items():
                if keyword in line.lower():
                    try:
                        date_match = re.search(r'(\d{2,4}[-/]\d{2}[-/]\d{2,4})', line)
                        amount_match = re.search(r'(\d{1,3}(?:,\d{3})*|\d+)(?:\s*(?:रुपये|₹|/-|RS|రూపాయలు|ரூபாய்|ರೂಪಾಯಿ|টাকা|રૂપિયા))?', line)
                        
                        if date_match and amount_match:
                            date_pos = date_match.end()
                            type_pos = line.lower().find(keyword)
                            
                            if type_pos > date_pos:
                                # Extract name in ORIGINAL SCRIPT (Hindi, Tamil, etc.)
                                name_text = line[date_pos:type_pos].strip()
                                
                                # Only remove these specific label words, keep actual names
                                name_text = re.sub(r'\b(नाम|सदस्य|name|member|:)\b', '', name_text, flags=re.IGNORECASE).strip()
                                
                                # Keep names in original script (रमा देवी, மோகன், etc.)
                                if name_text and len(name_text) > 1:
                                    transactions.append({
                                        "Date": self.normalize_date(date_match.group(1)),
                                        "Member": name_text,  # ORIGINAL SCRIPT
                                        "TransactionType": trans_type,
                                        "Amount": float(amount_match.group(1).replace(',', ''))
                                    })
                                    break
                    except:
                        pass

        if transactions:
            print(f"✅ Parsed {len(transactions)} transactions (names in original script)")
            return pd.DataFrame(transactions)
        else:
            print("⚠ No transactions parsed")
            return pd.DataFrame(columns=["Date", "Member", "TransactionType", "Amount"])

    def normalize_date(self, date_str: str) -> str:
        """Normalize date format to YYYY-MM-DD"""
        try:
            date_str = date_str.strip()
            for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d', '%d.%m.%Y']:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    return date_obj.strftime('%Y-%m-%d')
                except:
                    continue
            return date_str
        except:
            return date_str

    def clean_parsed_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize parsed data - PRESERVES ORIGINAL SCRIPT NAMES"""
        if df.empty:
            raise ValueError("No data to process")
        
        print(f"🧹 Cleaning {len(df)} rows. Columns: {df.columns.tolist()}")
        
        column_map = {
            'member_name': 'Member', 'member name': 'Member', 'member': 'Member', 
            'name': 'Member', 'नाम': 'Member', 'सदस्य': 'Member', 'పేరు': 'Member',
            'பெயர்': 'Member', 'ಹೆಸರು': 'Member', 'নাম': 'Member', 'નામ': 'Member',
            'transaction_type': 'TransactionType', 'transaction type': 'TransactionType', 
            'type': 'TransactionType', 'trans_type': 'TransactionType',
            'amount': 'Amount', 'amt': 'Amount', 'राशि': 'Amount', 'రకం': 'Amount',
            'தொகை': 'Amount', 'ಮೊತ್ತ': 'Amount', 'পরিমাণ': 'Amount', 'રકમ': 'Amount',
            'date': 'Date', 'transaction_date': 'Date', 'तारीख': 'Date'
        }
        
        df.columns = df.columns.str.strip()
        df_lower = df.rename(columns=lambda x: x.lower().strip())
        for old_col, new_col in column_map.items():
            if old_col in df_lower.columns:
                df = df.rename(columns={df.columns[df_lower.columns.get_loc(old_col)]: new_col})
        
        required_cols = ['Member', 'TransactionType', 'Amount']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # PRESERVE ORIGINAL NAMES - only strip whitespace, don't change case or script
        df['Member'] = df['Member'].astype(str).str.strip()
        
        # Only remove specific label words, keep names in original script
        df['Member'] = df['Member'].str.replace(r'\b(नाम|सदस्य|name|member|:)\b', '', regex=True, flags=re.IGNORECASE).str.strip()
        
        # Filter invalid entries
        df = df[df['Member'].notna() & (df['Member'] != 'Nan') & (df['Member'] != '') & (df['Member'].str.len() > 1)]
        
        if 'Amount' in df.columns:
            df['Amount'] = df['Amount'].astype(str).str.replace(',', '').str.replace('₹', '').str.replace('/-', '').str.strip()
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
            df = df.dropna(subset=['Amount'])
            df = df[df['Amount'] > 0]
        
        if 'TransactionType' in df.columns:
            type_map = {
                'deposit': 'Repayment', 'credit': 'Repayment', 'save': 'Repayment',
                'payment': 'Repayment', 'repay': 'Repayment', 'repayment': 'Repayment',
                'loan': 'Loan', 'borrow': 'Loan', 'advance': 'Loan',
            }
            df['TransactionType'] = df['TransactionType'].astype(str).str.lower().str.strip()
            df['TransactionType'] = df['TransactionType'].map(type_map).fillna(df['TransactionType'])
            df['TransactionType'] = df['TransactionType'].str.title()
        
        valid_types = ['Loan', 'Repayment', 'Deposit']
        df = df[df['TransactionType'].isin(valid_types)]
        
        if df.empty:
            raise ValueError("No valid transactions after cleaning")
        
        print(f"✅ Cleaned data: {len(df)} valid transactions")
        print(f"📋 Sample members: {df['Member'].unique()[:3].tolist()}")
        return df

    def extract_temporal_patterns(self, ledger_df: pd.DataFrame) -> Dict:
        """Analyze temporal patterns"""
        if 'Date' not in ledger_df.columns or ledger_df.empty:
            return {}
        
        ledger_df['Date'] = pd.to_datetime(ledger_df['Date'], errors='coerce')
        valid_dates = ledger_df.dropna(subset=['Date'])
        
        if len(valid_dates) < 2:
            return {}
        
        patterns = {}
        date_range = (valid_dates['Date'].max() - valid_dates['Date'].min()).days
        patterns['avg_transaction_interval'] = date_range / len(valid_dates)
        
        valid_dates['weekday'] = valid_dates['Date'].dt.day_name()
        patterns['preferred_days'] = valid_dates['weekday'].mode().tolist()
        
        valid_dates['month'] = valid_dates['Date'].dt.month
        patterns['active_months'] = valid_dates['month'].unique().tolist()
        
        monthly_counts = valid_dates.groupby('month').size()
        patterns['seasonality_score'] = monthly_counts.std() / monthly_counts.mean() if monthly_counts.mean() > 0 else 0
        
        return patterns

    def calculate_behavioral_score(self, ledger_df: pd.DataFrame) -> Dict:
        """Calculate behavioral financial scores"""
        behavioral_scores = {}
        
        for member in ledger_df['Member'].unique():
            member_data = ledger_df[ledger_df['Member'] == member]
            score_components = {}
            
            transaction_frequency = len(member_data)
            score_components['regularity'] = min(transaction_frequency / 10, 1.0)
            
            amounts = member_data['Amount']
            if len(amounts) > 1:
                cv = amounts.std() / amounts.mean() if amounts.mean() > 0 else 1
                score_components['consistency'] = max(0, 1 - cv)
            else:
                score_components['consistency'] = 0.5
            
            transaction_types = member_data['TransactionType'].nunique()
            score_components['diversity'] = min(transaction_types / 3, 1.0)
            
            loans = member_data[member_data['TransactionType'] == 'Loan']['Amount'].sum()
            repayments = member_data[member_data['TransactionType'] == 'Repayment']['Amount'].sum()
            score_components['repayment_discipline'] = min(repayments / max(loans, 1), 1.0)
            
            behavioral_score = (
                score_components['regularity'] * 0.3 +
                score_components['consistency'] * 0.2 +
                score_components['diversity'] * 0.2 +
                score_components['repayment_discipline'] * 0.3
            ) * 100
            
            behavioral_scores[member] = {
                'score': behavioral_score,
                'components': score_components
            }
        
        return behavioral_scores

    def calculate_credit_score_with_model(self, member_name: str, ledger_data: pd.DataFrame, 
                                        behavioral_score: float) -> Dict:
        """Calculate credit score using pre-trained model"""
        member_data = ledger_data[ledger_data['Member'] == member_name]
        
        if len(member_data) == 0:
            return self.get_default_credit_data()
        
        loans = member_data[member_data['TransactionType'] == 'Loan']['Amount'].sum()
        repayments = member_data[member_data['TransactionType'] == 'Repayment']['Amount'].sum()
        repayment_ratio = repayments / max(loans, 1)
        
        transaction_freq = len(member_data)
        amounts = member_data['Amount']
        amount_consistency = 1 - (amounts.std() / amounts.mean()) if len(amounts) > 1 and amounts.mean() > 0 else 0.5
        
        account_age_months = max(12, transaction_freq * 2)
        diversification = member_data['TransactionType'].nunique() / 3
        
        features = np.array([[repayment_ratio, transaction_freq, amount_consistency, 
                            account_age_months, diversification]])
        
        if self.credit_model:
            try:
                credit_score = self.credit_model.predict(features)[0]
                credit_score = int(max(300, min(900, credit_score)))
                
                if credit_score >= 750:
                    category = "Excellent"
                    loan_approval_chance = 0.95
                elif credit_score >= 700:
                    category = "Good" 
                    loan_approval_chance = 0.80
                elif credit_score >= 650:
                    category = "Fair"
                    loan_approval_chance = 0.60
                else:
                    category = "Poor"
                    loan_approval_chance = 0.25
                
                return {
                    'credit_score': credit_score,
                    'category': category,
                    'loan_approval_chance': loan_approval_chance,
                    'factors_affecting': self.generate_credit_factors(credit_score, repayment_ratio),
                    'model_confidence': 0.85,
                    'source': 'Pre-trained ML Model'
                }
            except Exception as e:
                print(f"Model prediction error: {e}")
                return self.get_default_credit_data()
        else:
            return self.get_default_credit_data()

    def generate_credit_factors(self, score: int, repayment_ratio: float) -> List[str]:
        """Generate factors affecting credit score"""
        factors = []
        
        if score < 650:
            factors.extend([
                "Irregular repayment history in SHG",
                "Low transaction consistency",
                "Limited credit history"
            ])
            if repayment_ratio < 0.7:
                factors.append("Poor repayment ratio")
        elif score < 750:
            factors.extend([
                "Good SHG participation",
                "Moderate credit utilization",
                "Improving payment history"
            ])
        else:
            factors.extend([
                "Excellent SHG track record",
                "Consistent payment pattern", 
                "Strong financial discipline"
            ])
        
        return factors

    def get_default_credit_data(self) -> Dict:
        """Default credit data when model is not available"""
        return {
            'credit_score': 650,
            'category': 'Fair',
            'loan_approval_chance': 0.60,
            'factors_affecting': ['Limited credit history', 'New to formal financial system'],
            'model_confidence': 0.50,
            'source': 'Default Scoring'
        }

    def calculate_loan_eligibility(self, shg_score: float, credit_score: int, 
                                 behavioral_score: float) -> Dict:
        """Calculate loan eligibility"""
        composite_score = (
            shg_score * 0.4 +
            (credit_score - 300) / 6 * 0.4 +
            behavioral_score * 0.2
        )
        
        if composite_score >= 80:
            eligibility = "High"
            max_loan_amount = 100000
            interest_rate = 8.5
        elif composite_score >= 65:
            eligibility = "Good"
            max_loan_amount = 50000
            interest_rate = 10.0
        elif composite_score >= 50:
            eligibility = "Medium"
            max_loan_amount = 25000
            interest_rate = 12.0
        elif composite_score >= 35:
            eligibility = "Low"
            max_loan_amount = 10000
            interest_rate = 15.0
        else:
            eligibility = "Very Low"
            max_loan_amount = 5000
            interest_rate = 18.0
        
        return {
            'eligibility_category': eligibility,
            'composite_score': composite_score,
            'max_loan_amount': max_loan_amount,
            'estimated_interest_rate': interest_rate,
            'approval_probability': min(0.95, composite_score / 100)
        }

    def create_financial_inclusion_score(self, ledger_df: pd.DataFrame, 
                                       behavioral_scores: Dict) -> Dict:
        """Calculate financial inclusion scores"""
        inclusion_metrics = {}
        
        for member in ledger_df['Member'].unique():
            member_data = ledger_df[ledger_df['Member'] == member]
            
            digital_score = min(member_data['TransactionType'].nunique() / 3 * 100, 100)
            total_amount = member_data['Amount'].sum()
            access_score = min(total_amount / 50000, 1.0) * 100
            participation_score = min(len(member_data) / ledger_df.groupby('Member').size().max() * 100, 100)
            
            savings = member_data[member_data['TransactionType'] == 'Repayment']['Amount'].sum()
            loans = member_data[member_data['TransactionType'] == 'Loan']['Amount'].sum()
            resilience_score = min((savings / loans) * 100, 100) if loans > 0 else 50
            
            inclusion_score = (
                digital_score * 0.25 +
                access_score * 0.25 +
                participation_score * 0.25 +
                resilience_score * 0.25
            )
            
            inclusion_metrics[member] = {
                'overall_inclusion_score': inclusion_score,
                'digital_literacy_proxy': digital_score,
                'financial_access': access_score,
                'social_integration': participation_score,
                'financial_resilience': resilience_score
            }
        
        return inclusion_metrics

    def comprehensive_analysis(self, image_path: str) -> Dict:
        """Main analysis pipeline"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        print("🚀 Starting SHG Analysis...")
        print("-" * 70)
        
        extracted_text = self.process_ledger_image(image_path)
        if not extracted_text:
            raise ValueError("Could not extract text from image")
        
        print(f"✅ Extracted {len(extracted_text)} characters")
        
        detected_lang, confidence = self.detect_language(extracted_text)
        
        ledger_df = self.parse_ledger_data(extracted_text)
        print(f"📊 Parsed {len(ledger_df)} transactions for {ledger_df['Member'].nunique()} members")
        
        print("🔍 Performing analysis...")
        temporal_patterns = self.extract_temporal_patterns(ledger_df)
        behavioral_scores = self.calculate_behavioral_score(ledger_df)
        inclusion_scores = self.create_financial_inclusion_score(ledger_df, behavioral_scores)
        
        print("👥 Analyzing members...")
        member_analysis = {}
        for member in ledger_df['Member'].unique():
            member_data = ledger_df[ledger_df['Member'] == member]
            
            loans = member_data[member_data['TransactionType'] == 'Loan']['Amount'].sum()
            repayments = member_data[member_data['TransactionType'] == 'Repayment']['Amount'].sum()
            deposits = member_data[member_data['TransactionType'] == 'Deposit']['Amount'].sum()
            
            repayment_rate = (repayments + deposits) / max(loans, 1)
            transaction_count = len(member_data)
            amount_consistency = 1 - (member_data['Amount'].std() / member_data['Amount'].mean()) if member_data['Amount'].std() > 0 and member_data['Amount'].mean() > 0 else 1
            
            shg_score = min(100, (
                repayment_rate * 60 +
                min(transaction_count / 8, 1) * 25 +
                amount_consistency * 15
            ))
            
            behavioral_score = behavioral_scores.get(member, {}).get('score', 50)
            credit_data = self.calculate_credit_score_with_model(member, ledger_df, behavioral_score)
            loan_eligibility = self.calculate_loan_eligibility(shg_score, credit_data['credit_score'], behavioral_score)
            
            member_analysis[member] = {
                'shg_score': shg_score,
                'credit_data': credit_data,
                'behavioral_score': behavioral_score,
                'inclusion_score': inclusion_scores.get(member, {}).get('overall_inclusion_score', 0),
                'loan_eligibility': loan_eligibility,
                'transaction_count': transaction_count,
                'total_amount': member_data['Amount'].sum(),
                'repayment_ratio': repayment_rate
            }
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'detected_language': detected_lang,
            'language_confidence': confidence,
            'total_members': ledger_df['Member'].nunique(),
            'total_transactions': len(ledger_df),
            'total_amount_processed': ledger_df['Amount'].sum(),
            'avg_shg_score': np.mean([data['shg_score'] for data in member_analysis.values()]),
            'avg_credit_score': np.mean([data['credit_data']['credit_score'] for data in member_analysis.values()]),
            'high_performers': len([m for m, data in member_analysis.items() if data['shg_score'] >= 80]),
            'member_analysis': member_analysis,
            'temporal_patterns': temporal_patterns,
            'behavioral_scores': behavioral_scores,
            'inclusion_scores': inclusion_scores,
            'ledger_data': ledger_df.to_dict('records')
        }
        
        print("✅ Analysis completed!")
        return results

    def display_results(self, results: Dict):
        """Display analysis results in detected language"""
        lang = self.detected_language
        
        print("\n" + "="*100)
        print(f"🏦 {self.translate('SHG LEDGER ANALYSIS RESULTS', lang)}")
        print("="*100)
        
        print(f"📅 {self.translate('Analysis Time', lang)}: {results['timestamp']}")
        print(f"🗣 {self.translate('Language', lang)}: {results['detected_language']} ({self.translate('Confidence', lang)}: {results['language_confidence']:.2f})")
        print(f"👥 {self.translate('Total Members', lang)}: {results['total_members']}")
        print(f"📊 {self.translate('Total Transactions', lang)}: {results['total_transactions']}")
        print(f"💰 {self.translate('Total Amount', lang)}: ₹{results['total_amount_processed']:,.2f}")
        print(f"📈 {self.translate('Avg SHG Score', lang)}: {results['avg_shg_score']:.1f}/100")
        print(f"💳 {self.translate('Avg Credit Score', lang)}: {results['avg_credit_score']:.0f}")
        
        print(f"\n🎯 {self.translate('MEMBER ANALYSIS', lang)}:")
        print("-" * 130)
        print(f"{self.translate('Member', lang):<16} "
              f"{self.translate('SHG', lang):<8} "
              f"{self.translate('Credit', lang):<8} "
              f"{self.translate('Behavioral', lang):<11} "
              f"{self.translate('Inclusion', lang):<10} "
              f"{self.translate('Eligibility', lang):<12} "
              f"{self.translate('MaxLoan', lang):<12} "
              f"{self.translate('Ratio', lang):<8}")
        print("-" * 130)
        
        sorted_members = sorted(results['member_analysis'].items(), 
                              key=lambda x: x[1]['shg_score'], reverse=True)
        
        for member, data in sorted_members:
            eligibility = self.translate(data['loan_eligibility']['eligibility_category'], lang)
            print(f"{member[:15]:<16} "
                  f"{data['shg_score']:<8.1f} "
                  f"{data['credit_data']['credit_score']:<8} "
                  f"{data['behavioral_score']:<11.1f} "
                  f"{data['inclusion_score']:<10.1f} "
                  f"{eligibility:<12} "
                  f"₹{data['loan_eligibility']['max_loan_amount']:<11,} "
                  f"{data['repayment_ratio']:<8.2f}")
        
        print("="*100)


def main():
    """Main execution"""
    print("="*70)
    print("🏦 DYNAMIC MULTI-LANGUAGE SHG LEDGER ANALYZER")
    print("="*70)
    
    analyzer = DynamicSHGLedgerAnalyzer(gemini_api_key="AIzaSyDMxyAuav0BJSTNLUdfVRabUTK19uLXr2g")
    
    image_path = "ledgerenglishsubhamoy.jpeg"
    try:
        results = analyzer.comprehensive_analysis(image_path)
        analyzer.display_results(results)
        
        output_file = 'shg_analysis_results.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str, ensure_ascii=False)
        print(f"\n✅ Results saved to {output_file}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()