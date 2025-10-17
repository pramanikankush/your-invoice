import google.generativeai as genai
from PIL import Image
import PyPDF2
import json
import logging
import time

logger = logging.getLogger(__name__)

_api_call_cache = {}

def extract_invoice_data(file_path, api_key=None):
    """
    Extract structured invoice data using Google Gemini AI
    API key is used only for this request and never stored
    """
    if not api_key or not isinstance(api_key, str):
        raise ValueError("Valid Gemini API key is required")
    
    if not file_path or not isinstance(file_path, str):
        raise ValueError("Invalid file path")
    
    if len(api_key) < 30 or not api_key.startswith('AIzaSy'):
        raise ValueError("Invalid API key format")
    
    try:
        _rate_limit_check()
        genai.configure(api_key=api_key)
        file_ext = file_path.rsplit('.', 1)[1].lower()
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        prompt = '''Analyze this invoice and extract information in JSON format:
{
    "invoice_number": "invoice number or ID",
    "invoice_date": "date of invoice",
    "vendor_name": "vendor/seller company name",
    "vendor_address": "vendor address",
    "customer_name": "customer/buyer name",
    "customer_address": "customer address",
    "items": [
        {
            "description": "item description",
            "quantity": "quantity",
            "unit_price": "unit price",
            "total": "line total"
        }
    ],
    "subtotal": "subtotal amount",
    "tax_amount": "tax amount",
    "total_amount": "total amount"
}
Extract all available information. If any field is not found, use "N/A".
Return ONLY valid JSON, no additional text.'''
        
        if file_ext == 'pdf':
            with open(file_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text = ''.join(page.extract_text() for page in pdf_reader.pages)
            
            if not text.strip():
                raise ValueError("PDF contains no extractable text")
            
            response = model.generate_content([prompt, f"\n\nInvoice Text:\n{text}"])
        else:
            image = Image.open(file_path)
            response = model.generate_content([prompt, image])
        
        response_text = response.text.strip()
        response_text = response_text.removeprefix('```json').removeprefix('```').removesuffix('```').strip()
        
        extracted_data = json.loads(response_text)
        logger.info("Invoice data extracted successfully")
        
        _sanitize_extracted_data(extracted_data)
        return extracted_data
    
    except json.JSONDecodeError:
        logger.error("JSON parsing error")
        raise ValueError("Failed to parse AI response")
    except FileNotFoundError:
        logger.error("File not found")
        raise FileNotFoundError("Invoice file not found")
    except Exception as e:
        logger.error(f"Extraction error: {type(e).__name__}")
        raise Exception("Failed to process invoice")
    finally:
        api_key = None

def _sanitize_extracted_data(data):
    """Sanitize extracted data to prevent XSS"""
    if not isinstance(data, dict):
        return
    
    for key, value in data.items():
        if isinstance(value, str):
            data[key] = value.replace('<', '&lt;').replace('>', '&gt;')
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    _sanitize_extracted_data(item)

def _rate_limit_check():
    """Simple rate limiting for API calls"""
    global _api_call_cache
    now = time.time()
    _api_call_cache = {k: v for k, v in _api_call_cache.items() if now - v < 60}
    
    if len(_api_call_cache) >= 30:
        raise Exception("Rate limit exceeded. Please wait.")
    
    _api_call_cache[now] = now
