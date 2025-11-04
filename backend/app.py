from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import math
from analyzer import DynamicSHGLedgerAnalyzer

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "ledgeruploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize analyzer once with your Gemini key
analyzer = DynamicSHGLedgerAnalyzer(gemini_api_key="AIzaSyDMxyAuav0BJSTNLUdfVRabUTK19uLXr2g")

@app.route("/analyze-ledger", methods=["POST"])
def analyze_ledger():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    try:
        results = analyzer.comprehensive_analysis(file_path)
        detected_lang = results.get('detected_language', 'english')

        # Check if we have valid results
        if not results.get('member_analysis') or len(results.get('member_analysis', {})) == 0:
            error_msg = "No valid member data could be extracted from the ledger image. Please ensure the image is clear and contains transaction data."
            if detected_lang != 'english':
                error_msg = analyzer.translate(error_msg, detected_lang)
            return jsonify({"error": error_msg}), 400

        # Helper function to translate text
        def t(text):
            return analyzer.translate(text, detected_lang)

        # Format member analysis as array for table display
        member_analysis_array = []
        for member_name, data in results.get('member_analysis', {}).items():
            # Handle potential NaN values
            shg_score = data.get('shg_score', 0)
            behavioral_score = data.get('behavioral_score', 0)
            inclusion_score = data.get('inclusion_score', 0)
            repayment_ratio = data.get('repayment_ratio', 0)
            
            # Replace NaN with 0
            if math.isnan(shg_score): shg_score = 0
            if math.isnan(behavioral_score): behavioral_score = 0
            if math.isnan(inclusion_score): inclusion_score = 0
            if math.isnan(repayment_ratio): repayment_ratio = 0
            
            eligibility = data.get('loan_eligibility', {}).get('eligibility_category', 'Unknown')
            
            # Translate eligibility
            eligibility_translated = t(eligibility)
            
            member_analysis_array.append({
                "Member": member_name,
                "SHG": round(shg_score, 1),
                "Credit": data.get('credit_data', {}).get('credit_score', 650),
                "Behavioral": round(behavioral_score, 1),
                "Inclusion": round(inclusion_score, 1),
                "Eligibility": eligibility_translated,
                "MaxLoan": data.get('loan_eligibility', {}).get('max_loan_amount', 0),
                "Ratio": round(repayment_ratio, 2)
            })

        # Sort by SHG score descending
        member_analysis_array.sort(key=lambda x: x['SHG'], reverse=True)

        # Handle potential NaN in summary stats
        avg_shg = results.get("avg_shg_score", 0)
        avg_credit = results.get("avg_credit_score", 0)
        total_amount = results.get("total_amount_processed", 0)
        
        if math.isnan(avg_shg): avg_shg = 0
        if math.isnan(avg_credit): avg_credit = 0
        if math.isnan(total_amount): total_amount = 0

        # Prepare translated headers
        headers = {
            'Member': t('Member'),
            'SHG': t('SHG'),
            'Credit': t('Credit'),
            'Behavioral': t('Behavioral'),
            'Inclusion': t('Inclusion'),
            'Eligibility': t('Eligibility'),
            'MaxLoan': t('MaxLoan'),
            'Ratio': t('Ratio')
        }

        # Prepare response with translations
        response = {
            "language": detected_lang,
            "confidence": round(results.get("language_confidence", 0.0), 2),
            "total_members": results.get("total_members", 0),
            "total_transactions": results.get("total_transactions", 0),
            "total_amount": round(total_amount, 2),
            "avg_shg_score": round(avg_shg, 1),
            "avg_credit_score": int(avg_credit),
            "member_analysis": member_analysis_array,
            "labels": {
                "language": t("Language"),
                "confidence": t("Confidence"),
                "total_members": t("Total Members"),
                "total_transactions": t("Total Transactions"),
                "total_amount": t("Total Amount"),
                "avg_shg_score": t("Avg SHG Score"),
                "avg_credit_score": t("Avg Credit Score"),
                "title": t("SHG Ledger Analyzer"),
                "subtitle": t("Upload your ledger image for AI-powered analysis"),
                "member_analysis_title": t("MEMBER ANALYSIS"),
                "upload_button": t("Upload and Analyze"),
                "analyzing": t("Analyzing..."),
                "history": t("History"),
                "headers": headers
            }
        }

        return jsonify(response)
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print(traceback.format_exc())
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)