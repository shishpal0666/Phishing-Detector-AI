import os
import re
import string
import torch
import nltk
from flask import Flask, request, jsonify
from flask_cors import CORS
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from transformers import RobertaTokenizer, RobertaForSequenceClassification

# Initialize App
app = Flask(__name__)
CORS(app)  # Allow the browser extension to talk to this server

# --- 1. Setup Preprocessing (FIXED) ---
print("Setting up NLTK resources...")
try:
    # Check if resources exist
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('tokenizers/punkt_tab') # This is the new requirement
    nltk.data.find('corpora/stopwords')
except LookupError:
    print("Downloading missing NLTK data...")
    nltk.download('stopwords')
    nltk.download('punkt')
    nltk.download('punkt_tab') # <--- ADDED THIS LINE

stop_words = set(stopwords.words('english'))

def clean_text(text):
    text = str(text).lower()
    text = re.sub(r'<.*?>', '', text)               # remove HTML tags
    text = re.sub(r'\S*@\S*\s?', '', text)          # remove email addresses
    text = re.sub(r'http[s]?://\S+', '', text)      # remove URLs
    text = re.sub(r'\d+', '', text)                 # remove digits
    text = text.translate(str.maketrans('', '', string.punctuation))  # remove punctuation

    words = word_tokenize(text)
    words = [word for word in words if word not in stop_words]
    return ' '.join(words)

# --- 2. Load the Saved Model ---
MODEL_DIR = "./model"  # This folder contains your config.json and model.safetensors

print("Loading model resources...")
try:
    # Load the tokenizer from the internet (standard roberta-base)
    # because we only saved model weights, not the tokenizer files
    print("Downloading standard tokenizer...")
    tokenizer = RobertaTokenizer.from_pretrained("roberta-base")

    # Load YOUR custom trained weights from the local folder
    print(f"Loading your custom weights from {MODEL_DIR}...")
    model = RobertaForSequenceClassification.from_pretrained(MODEL_DIR)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()
    print("✅ Model and Tokenizer loaded successfully!")
except Exception as e:
    print(f"❌ CRITICAL ERROR loading model: {e}")
    print("Ensure your 'model' folder contains 'config.json' and 'model.safetensors'")
    exit(1)

# --- 3. Define the API Endpoint ---
@app.route('/analyze', methods=['POST'])
def analyze_email():
    data = request.json
    raw_text = data.get('text', '')

    if not raw_text:
        return jsonify({'error': 'No text provided'}), 400

    try:
        # 1. Preprocess
        processed_text = clean_text(raw_text)

        # 2. Tokenize
        inputs = tokenizer(
            processed_text,
            padding=True,
            truncation=True,
            max_length=256,
            return_tensors="pt"
        ).to(device)

        # 3. Predict
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            probs = torch.nn.functional.softmax(logits, dim=-1)

            # Assuming Label 1 is Phishing
            phishing_probability = probs[0][1].item()
            
            # Threshold 0.5
            is_phishing = phishing_probability > 0.5

        return jsonify({
            'is_phishing': is_phishing,
            'confidence_score': round(phishing_probability * 100, 2)
        })
    except Exception as e:
        print(f"Prediction Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Server starting on http://0.0.0.0:7860")
    app.run(host="0.0.0.0", port=7860)