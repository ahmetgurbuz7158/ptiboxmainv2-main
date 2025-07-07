from flask import Flask, render_template, request, jsonify, session, send_from_directory
from flask_cors import CORS
import os
import time
import random
import threading
import logging
import sys
import vertexai
from vertexai.generative_models import GenerativeModel, SafetySetting
import functions_framework

# Logging yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Flask uygulamasını oluştur
app = Flask(__name__)
app.secret_key = 'patibox_gizli_anahtar'
CORS(app)

# Her kullanıcı için sohbet geçmişlerini tutacak sözlük (session_id: chat)
user_chats = {}
user_chats_lock = threading.Lock()  # user_chats için bir kilit oluştur

# Yanıt konfigürasyonu
generation_config = {
    "max_output_tokens": 8192,
    "temperature": 0.2,
    "top_p": 0.95,
}

# Güvenlik ayarları
safety_settings = [
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
]

# Sistem açıklaması
textsi_1 = """Senin Rolün:
**Sen bir veteriner asistanı chatbotusun ve ismin Patibox AI.**
Patimat App projesine ait bir yapay zeka olarak, hayvan sağlığı ve refahını destekleyen önerilere odaklanırım.

Genel Kurallar:
**Hayvan Refahı Önceliği:**
Her yanıtın, hayvanların sağlığı ve refahını desteklemeye yönelik olmalıdır.

**Nazik ve Empatik Ol:**
Her zaman destekleyici ve anlayışlı bir dil kullan.

**Bilgi Doğruluğu:**
Yalnızca güvenilir, doğrulanmış bilgiler paylaş.

**Anlaşılır Dil Kullanımı:**
Karmaşık tıbbi terimleri basit bir dille açıkla.

**Patimat App'i Tanı:**
Patimat, hayvan sahiplerine ve hayvan severlere bakım, sağlık hizmetleri ve barınma gibi ihtiyaçlar için çözümler sunar.

Önemli Not: Sadece Hayvanlar İle Alakalı Sorulara Yanıt Vereceksin. Diğer sorulara: "Üzgünüm ben Bir Veteriner Asistanı Chatbotuyum Bu Alanda Bilgi Sahibi Değilim Ben Sadece Hayvanlar İle İlgili Sorulara Cevap Veririm."
"""

# Vertex AI modelini başlatan ve yanıt üreten fonksiyon
def multiturn_generate_content(session_id, user_message):
    try:
        vertexai.init(project="the-other-459900-e8", location="us-central1")
        model = GenerativeModel(
            "gemini-2.0-flash-001",
            system_instruction=textsi_1
        )

        # Kullanıcının sohbet geçmişini al
        with user_chats_lock:
            if session_id not in user_chats:
                user_chats[session_id] = []
            chat_history = user_chats[session_id]

        # Sohbet geçmişini modele gönder
        chat = model.start_chat(history=chat_history)
        
        # Kullanıcı mesajını gönder ve yanıt al
        response = chat.send_message(user_message)
        
        # Yanıtı sohbet geçmişine ekle
        with user_chats_lock:
            user_chats[session_id].append({
                "role": "user",
                "parts": [{"text": user_message}]
            })
            user_chats[session_id].append({
                "role": "model",
                "parts": [{"text": response.text}]
            })

        return response.text

    except Exception as e:
        logger.error(f"Model yanıt üretirken hata oluştu: {str(e)}")
        return f"Üzgünüm, şu anda yanıt üretemiyorum. Lütfen daha sonra tekrar deneyin."

# Flask route'ları
@app.route('/')
def home():
    return jsonify({"message": "Patibox AI API - Veteriner Asistanı"})

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/get_response', methods=['POST'])
def get_response():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        session_id = data.get('session_id', str(random.randint(1000, 9999)))
        
        if not user_message.strip():
            return jsonify({'error': 'Mesaj boş olamaz'}), 400
        
        # AI yanıtını al
        ai_response = multiturn_generate_content(session_id, user_message)
        
        return jsonify({
            'response': ai_response,
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f"Yanıt alınırken hata oluştu: {str(e)}")
        return jsonify({'error': 'Bir hata oluştu'}), 500

@app.route('/analysis')
def analysis():
    return render_template('analysis.html')

@app.route('/analyze_image', methods=['POST'])
def analyze_image():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'Resim dosyası bulunamadı'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'Dosya seçilmedi'}), 400
        
        if file and allowed_file(file.filename):
            # Dosyayı geçici olarak kaydet
            filename = f"temp_{int(time.time())}_{file.filename}"
            filepath = os.path.join('/tmp', filename)
            file.save(filepath)
            
            # Barkod ve OCR analizi yap
            barcode_result = process_barcode(filepath)
            ocr_result = process_ocr(filepath)
            
            # Geçici dosyayı sil
            os.remove(filepath)
            
            return jsonify({
                'barcode': barcode_result,
                'ocr': ocr_result
            })
        else:
            return jsonify({'error': 'Geçersiz dosya türü'}), 400
            
    except Exception as e:
        logger.error(f"Resim analizi sırasında hata: {str(e)}")
        return jsonify({'error': 'Resim analizi sırasında hata oluştu'}), 500

@app.route('/search_product', methods=['POST'])
def search_product():
    try:
        data = request.get_json()
        product_name = data.get('product_name', '')
        
        if not product_name.strip():
            return jsonify({'error': 'Ürün adı boş olamaz'}), 400
        
        # Ürün arama işlemi
        search_result = search_product_database(product_name)
        
        return jsonify({'products': search_result})
        
    except Exception as e:
        logger.error(f"Ürün arama sırasında hata: {str(e)}")
        return jsonify({'error': 'Ürün arama sırasında hata oluştu'}), 500

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        rating = data.get('rating')
        comment = data.get('comment', '')
        
        if not product_id or not rating:
            return jsonify({'error': 'Ürün ID ve puan gerekli'}), 400
        
        # Geri bildirimi kaydet
        save_feedback(product_id, rating, comment)
        
        return jsonify({'message': 'Geri bildirim başarıyla kaydedildi'})
        
    except Exception as e:
        logger.error(f"Geri bildirim kaydedilirken hata: {str(e)}")
        return jsonify({'error': 'Geri bildirim kaydedilirken hata oluştu'}), 500

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_barcode(image_path):
    # Barkod okuma işlemi burada yapılacak
    # Örnek yanıt
    return {
        'type': 'EAN-13',
        'value': '1234567890123',
        'confidence': 0.95
    }

def process_ocr(image_path):
    # OCR işlemi burada yapılacak
    # Örnek yanıt
    return {
        'text': 'Örnek ürün adı',
        'confidence': 0.85
    }

def search_product_database(product_name):
    # Veri tabanında ürün arama işlemi burada yapılacak
    # Örnek yanıt
    return [
        {
            'id': 1,
            'name': 'Kedi Maması Premium',
            'price': 45.99,
            'rating': 4.5,
            'image': 'cat_food.jpg'
        },
        {
            'id': 2,
            'name': 'Köpek Maması Premium',
            'price': 52.99,
            'rating': 4.3,
            'image': 'dog_food.jpg'
        }
    ]

def save_feedback(product_id, rating, comment):
    # Geri bildirimi veri tabanına kaydetme işlemi burada yapılacak
    logger.info(f"Geri bildirim kaydedildi: Ürün ID: {product_id}, Puan: {rating}, Yorum: {comment}")

# Cloud Functions için gerekli fonksiyon
@functions_framework.http
def ptiboxmain(request):
    """HTTP Cloud Function."""
    return app(request.environ, lambda x, y: y) 