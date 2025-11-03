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
        self.detected_language = 'english'  # Will be set during analysis
        
        self.language_patterns = {
            'hindi': ['रुपये', 'नाम', 'राशि', 'तारीख', 'सदस्य', 'बचत', 'लोन'],
            'english': ['rupees', 'name', 'amount', 'date', 'member', 'savings', 'loan'],
            'tamil': ['ரூபாய்', 'பெயர்', 'தொகை', 'தேதி', 'உறுப்பினர்'],
            'telugu': ['రూపాయలు', 'పేరు', 'మొత్తం', 'తేదీ', 'సభ్యుడు'],
            'kannada': ['ರೂಪಾಯಿ', 'ಹೆಸರು', 'ಮೊತ್ತ', 'ದಿನಾಂಕ', 'ಸದಸ್ಯ'],
            'bengali': ['টাকা', 'নাম', 'পরিমাণ', 'তারিখ', 'সদস্য'],
            'gujarati': ['રૂપિયા', 'નામ', 'રકમ', 'તારીખ', 'સભ્ય']
        }
        
        # Hindi translations for output
        self.translations = {
            'hindi': {
                'Member': 'सदस्य',
                'SHG': 'एसएचजी स्कोर',
                'Credit': 'क्रेडिट स्कोर',
                'Behavioral': 'व्यवहार स्कोर',
                'Inclusion': 'समावेशन स्कोर',
                'Eligibility': 'पात्रता',
                'MaxLoan': 'अधिकतम ऋण',
                'Ratio': 'अनुपात',
                'High': 'उच्च',
                'Good': 'अच्छा',
                'Medium': 'मध्यम',
                'Low': 'कम',
                'Very Low': 'बहुत कम',
                'Excellent': 'उत्कृष्ट',
                'Fair': 'ठीक',
                'Poor': 'खराब',
                'Analysis Time': 'विश्लेषण समय',
                'Language': 'भाषा',
                'Confidence': 'विश्वास',
                'Total Members': 'कुल सदस्य',
                'Total Transactions': 'कुल लेनदेन',
                'Total Amount': 'कुल राशि',
                'Avg SHG Score': 'औसत एसएचजी स्कोर',
                'Avg Credit Score': 'औसत क्रेडिट स्कोर',
                'MEMBER ANALYSIS': 'सदस्य विश्लेषण',
                'SHG LEDGER ANALYSIS RESULTS': 'एसएचजी खाता विश्लेषण परिणाम'
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
        """Detect primary language of the ledger"""
        language_scores = {}
        
        for lang, patterns in self.language_patterns.items():
            score = sum(1 for pattern in patterns if pattern.lower() in text.lower())
            language_scores[lang] = score
        
        if not any(language_scores.values()):
            return 'english', 0.5
        
        detected_lang = max(language_scores, key=language_scores.get)
        confidence = language_scores[detected_lang] / len(self.language_patterns[detected_lang])
        
        return detected_lang, confidence

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
                prompt = """Extract all transaction data from this SHG ledger image. The text may be in Hindi, English, or other Indian languages.

For each transaction, extract and TRANSLATE TO ENGLISH:
- Date (format: YYYY-MM-DD or DD-MM-YYYY)
- Member Name (translate Hindi names to Roman script)
- Transaction Type (translate to: Deposit, Loan, or Repayment)
- Amount (numbers only, no currency symbols)

Common Hindi terms:
- जमा/बचत = Deposit
- ऋण/कर्ज/लोन = Loan  
- भुगतान/वापसी = Repayment
- नाम = Name
- राशि/रकम = Amount
- तारीख = Date

Return as plain text with each transaction on a new line:
Date | Member Name | Transaction Type | Amount

Example:
2023-01-10 | Sita Devi | Deposit | 500
2023-01-15 | Radha Kumari | Loan | 50000"""
                
                time.sleep(1)
                response = self.model.generate_content([prompt, processed_image])
                return response.text if response.text else ""
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
        
        print(f"📄 Extracted text sample:\n{extracted_text[:300]}\n")
        
        # Try manual parsing first (more reliable)
        df = self.manual_parse_text(extracted_text)
        
        if not df.empty:
            return df
            
        # If manual parsing failed and Gemini is available, try structured parsing
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
                    
                    # Remove markdown
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
        """Enhanced manual parser with Hindi support and multiple pattern matching"""
        lines = extracted_text.split("\n")
        transactions = []

        # Hindi to English mappings for transaction types
        hindi_type_map = {
            'जमा': 'Deposit', 'बचत': 'Deposit', 'जमाराशि': 'Deposit',
            'ऋण': 'Loan', 'कर्ज': 'Loan', 'लोन': 'Loan', 'उधार': 'Loan',
            'भुगतान': 'Repayment', 'वापसी': 'Repayment', 'चुकौती': 'Repayment',
            'deposit': 'Deposit', 'save': 'Deposit', 'saving': 'Deposit',
            'loan': 'Loan', 'advance': 'Loan', 'borrow': 'Loan',
            'repayment': 'Repayment', 'payment': 'Repayment', 'repay': 'Repayment'
        }

        for line in lines:
            line = line.strip()
            if not line or len(line) < 5:
                continue

            # Pattern 1: Pipe-separated format (from our Gemini prompt)
            # 2023-01-10 | Sita Devi | Deposit | 500
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 4:
                    try:
                        date_str = parts[0]
                        # Validate date format (YYYY-MM-DD or DD-MM-YYYY or DD/MM/YYYY)
                        if re.match(r'\d{2,4}[-/]\d{2}[-/]\d{2,4}', date_str):
                            # Normalize date format
                            date_str = self.normalize_date(date_str)
                            
                            # Get transaction type and normalize it
                            trans_type = parts[2].strip()
                            trans_type_normalized = hindi_type_map.get(trans_type.lower(), trans_type)
                            
                            transactions.append({
                                "Date": date_str,
                                "Member": parts[1],
                                "TransactionType": trans_type_normalized,
                                "Amount": float(parts[3].replace(',', '').replace('₹', '').replace('/-', '').strip())
                            })
                            continue
                    except Exception as e:
                        pass

            # Pattern 2: Standard space-separated format (English)
            pattern2 = re.compile(
                r'(\d{2,4}[-/]\d{2}[-/]\d{2,4})\s+([A-Za-z\s]+?)\s+(Deposit|Loan|Repayment|Withdraw|Advance|Payment)\s+([\d,]+)',
                re.IGNORECASE
            )
            match = pattern2.search(line)
            if match:
                try:
                    transactions.append({
                        "Date": self.normalize_date(match.group(1).strip()),
                        "Member": match.group(2).strip(),
                        "TransactionType": match.group(3).strip().title(),
                        "Amount": float(match.group(4).replace(",", ""))
                    })
                    continue
                except:
                    pass

            # Pattern 3: Hindi text format
            # Look for Hindi transaction type keywords
            for hindi_word, english_type in hindi_type_map.items():
                if hindi_word in line:
                    try:
                        # Extract date
                        date_match = re.search(r'(\d{2,4}[-/]\d{2}[-/]\d{2,4})', line)
                        # Extract amount (look for numbers)
                        amount_match = re.search(r'(\d{1,3}(?:,\d{3})*|\d+)(?:\s*(?:रुपये|₹|/-|RS))?', line)
                        
                        if date_match and amount_match:
                            # Extract name (text between date and transaction type)
                            date_pos = date_match.end()
                            type_pos = line.find(hindi_word)
                            
                            if type_pos > date_pos:
                                name_text = line[date_pos:type_pos].strip()
                                # Clean name (remove common prefixes/suffixes)
                                name_text = re.sub(r'(नाम|सदस्य|:)', '', name_text).strip()
                                
                                if name_text:
                                    transactions.append({
                                        "Date": self.normalize_date(date_match.group(1)),
                                        "Member": name_text,
                                        "TransactionType": english_type,
                                        "Amount": float(amount_match.group(1).replace(',', ''))
                                    })
                                    break
                    except:
                        pass

            # Pattern 4: JSON-like lines
            if '"date"' in line.lower() or '"member"' in line.lower():
                try:
                    date_match = re.search(r'"date":\s*"([^"]+)"', line, re.IGNORECASE)
                    member_match = re.search(r'"member(?:\s*name)?":\s*"([^"]+)"', line, re.IGNORECASE)
                    type_match = re.search(r'"(?:transaction[\s_]?)?type":\s*"([^"]+)"', line, re.IGNORECASE)
                    amount_match = re.search(r'"amount":\s*(\d+)', line, re.IGNORECASE)
                    
                    if all([date_match, member_match, type_match, amount_match]):
                        trans_type = type_match.group(1)
                        trans_type_normalized = hindi_type_map.get(trans_type.lower(), trans_type)
                        
                        transactions.append({
                            "Date": self.normalize_date(date_match.group(1)),
                            "Member": member_match.group(1),
                            "TransactionType": trans_type_normalized,
                            "Amount": float(amount_match.group(1))
                        })
                except:
                    pass

        if transactions:
            print(f"✅ Parsed {len(transactions)} transactions")
            return pd.DataFrame(transactions)
        else:
            print("⚠ No transactions parsed")
            return pd.DataFrame(columns=["Date", "Member", "TransactionType", "Amount"])

    def normalize_date(self, date_str: str) -> str:
        """Normalize date format to YYYY-MM-DD"""
        try:
            date_str = date_str.strip()
            # Try different date formats
            for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d', '%d.%m.%Y']:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    return date_obj.strftime('%Y-%m-%d')
                except:
                    continue
            # If all fail, return as is
            return date_str
        except:
            return date_str

    def clean_parsed_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize parsed data - Multi-language support"""
        if df.empty:
            raise ValueError("No data to process")
        
        print(f"🧹 Cleaning {len(df)} rows. Columns: {df.columns.tolist()}")
        
        # Flexible column mapping (English + Hindi)
        column_map = {
            'member_name': 'Member', 'member name': 'Member', 'member': 'Member', 
            'name': 'Member', 'नाम': 'Member', 'सदस्य': 'Member',
            'transaction_type': 'TransactionType', 'transaction type': 'TransactionType', 
            'type': 'TransactionType', 'trans_type': 'TransactionType', 'प्रकार': 'TransactionType',
            'amount': 'Amount', 'amt': 'Amount', 'राशि': 'Amount', 'रकम': 'Amount',
            'date': 'Date', 'transaction_date': 'Date', 'तारीख': 'Date'
        }
        
        # Rename columns (case-insensitive)
        df.columns = df.columns.str.strip()
        df_lower = df.rename(columns=lambda x: x.lower().strip())
        for old_col, new_col in column_map.items():
            if old_col in df_lower.columns:
                df = df.rename(columns={df.columns[df_lower.columns.get_loc(old_col)]: new_col})
        
        # Ensure required columns exist
        required_cols = ['Member', 'TransactionType', 'Amount']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Clean Member names
        df['Member'] = df['Member'].astype(str).str.strip().str.title()
        # Remove Hindi common words from names
        df['Member'] = df['Member'].str.replace(r'(नाम|सदस्य|:', '', regex=True).str.strip()
        df = df[df['Member'].notna() & (df['Member'] != 'Nan') & (df['Member'] != '')]
        
        # Clean Amounts
        if 'Amount' in df.columns:
            df['Amount'] = df['Amount'].astype(str).str.replace(',', '').str.replace('₹', '').str.replace('रुपये', '').str.replace('/-', '').str.strip()
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
            df = df.dropna(subset=['Amount'])
            df = df[df['Amount'] > 0]
        
        # Clean Transaction Types (English + Hindi)
        if 'TransactionType' in df.columns:
            type_map = {
                # English
                'deposit': 'Repayment', 'credit': 'Repayment', 'save': 'Repayment',
                'payment': 'Repayment', 'repay': 'Repayment', 'repayment': 'Repayment',
                'loan': 'Loan', 'borrow': 'Loan', 'advance': 'Loan',
                # Hindi
                'जमा': 'Repayment', 'बचत': 'Repayment', 'जमाराशि': 'Repayment',
                'ऋण': 'Loan', 'कर्ज': 'Loan', 'लोन': 'Loan', 'उधार': 'Loan',
                'भुगतान': 'Repayment', 'वापसी': 'Repayment', 'चुकौती': 'Repayment'
            }
            df['TransactionType'] = df['TransactionType'].astype(str).str.lower().str.strip()
            df['TransactionType'] = df['TransactionType'].map(type_map).fillna(df['TransactionType'])
            df['TransactionType'] = df['TransactionType'].str.title()
        
        # Keep only valid transaction types
        valid_types = ['Loan', 'Repayment', 'Deposit']
        df = df[df['TransactionType'].isin(valid_types)]
        
        if df.empty:
            raise ValueError("No valid transactions after cleaning")
        
        print(f"✅ Cleaned data: {len(df)} valid transactions")
        return df

    # Keep all the remaining methods from your original file unchanged:
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
        print(f"📝 Language: {detected_lang} (confidence: {confidence:.2f})")
        
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
        """Display analysis results"""
        print("\n" + "="*100)
        print("🏦 SHG LEDGER ANALYSIS RESULTS")
        print("="*100)
        
        print(f"📅 Analysis Time: {results['timestamp']}")
        print(f"🗣 Language: {results['detected_language']} (Confidence: {results['language_confidence']:.2f})")
        print(f"👥 Total Members: {results['total_members']}")
        print(f"📊 Total Transactions: {results['total_transactions']}")
        print(f"💰 Total Amount: ₹{results['total_amount_processed']:,.2f}")
        print(f"📈 Avg SHG Score: {results['avg_shg_score']:.1f}/100")
        print(f"💳 Avg Credit Score: {results['avg_credit_score']:.0f}")
        
        print(f"\n🎯 MEMBER ANALYSIS:")
        print("-" * 130)
        print(f"{'Member':<16} {'SHG':<8} {'Credit':<8} {'Behavioral':<11} {'Inclusion':<10} {'Eligibility':<12} {'Max Loan':<12} {'Ratio':<8}")
        print("-" * 130)
        
        sorted_members = sorted(results['member_analysis'].items(), 
                              key=lambda x: x[1]['shg_score'], reverse=True)
        
        for member, data in sorted_members:
            print(f"{member[:15]:<16} "
                  f"{data['shg_score']:<8.1f} "
                  f"{data['credit_data']['credit_score']:<8} "
                  f"{data['behavioral_score']:<11.1f} "
                  f"{data['inclusion_score']:<10.1f} "
                  f"{data['loan_eligibility']['eligibility_category']:<12} "
                  f"₹{data['loan_eligibility']['max_loan_amount']:<11,} "
                  f"{data['repayment_ratio']:<8.2f}")
        
        print("="*100)