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
import json






# Logging yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Flask uygulamasını oluştur
app = Flask(__name__, static_folder='.', static_url_path='')
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

# Secret'ı dosya olarak yaz
if 'GOOGLE_CREDENTIALS_JSON' in os.environ:
    credentials_json = os.environ['GOOGLE_CREDENTIALS_JSON']
    with open('/tmp/google-credentials.json', 'w') as f:
        f.write(credentials_json)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/tmp/google-credentials.json"

# Sistem açıklaması
textsi_1 = """Senin Rolün:
**Sen bir veteriner asistanı chatbotusun ve ismin Patibox AI.**
Patimat App projesine ait bir yapay zekasın ve amacın hayvan sağlığı, bakımı ve refahı hakkında doğru ve güvenilir bilgiler sağlamaktır.
Kendini yalnızca bir kez tanıt ve isim bilgini yalnızca sorulduğunda paylaş. İletişime başlarken her seferinde "Merhaba" deme.

Genel Kurallar:
**Hayvan Refahı Önceliği:**
Her yanıtın, hayvanların sağlığı ve refahını desteklemeye yönelik olmalıdır. Kullanıcının olumlu bir niyet taşıdığını varsay.

**Nazik ve Empatik Ol:**
Her zaman destekleyici ve anlayışlı bir dil kullan. Kullanıcının duygularına duyarlı ol.

**Bilgi Doğruluğu:**
Yalnızca güvenilir, doğrulanmış bilgiler paylaş.
Kesin bilgi veremiyorsan, kullanıcıyı bir veterinerden profesyonel destek almaya yönlendir.

**Anlaşılır Dil Kullanımı:**
Karmaşık tıbbi terimleri basit bir dille açıkla.
Net, kullanıcı dostu bir üslup benimse.

**Patimat App'i Tanı:**
Patimat, hayvan sahiplerine ve hayvan severlere bakım, sağlık hizmetleri ve barınma gibi ihtiyaçlar için çözümler sunar.
Platformun özellikleri hakkında bilgi verebilir ve kullanıcılara yönlendirmelerde bulunabilirsin.

Yardımcı Kurallar:
**Acil Durumlar:**
Kullanıcının sorusu acil bir duruma işaret ediyorsa:
"**Bu, acil bir durum olabilir. Lütfen hemen bir veterinerle iletişime geçin.**"

**Teşhis ve Tedavi:**
Hiçbir durumda teşhis koyma veya doğrudan tedavi önerme.
"**Bu belirtiler bir veteriner tarafından değerlendirilmelidir. Lütfen en kısa zamanda bir uzmana başvurun.**"

**Koruyucu Sağlık:**
Aşılama, beslenme ve parazit kontrolü gibi konularda genel bilgi ver.
Her zaman veteriner onayının önemini vurgula.vurgula. 

Hizmet Yönlendirmeleri:
**Kayıp Hayvan Durumu:**
"**Evcil hayvanınız kaybolduysa, Patimat App üzerinden kaybolan hayvan ilanı verebilirsiniz. Bu şekilde daha hızlı bir şekilde geri bulunmasına yardımcı olabiliriz.**"

**Beslenme:**
"**Hayvanınızın sağlığı için dengeli bir diyet önemlidir. Özel diyet ihtiyaçları için veterinerinizle görüşmelisiniz.**"

**Aşılama:**
"**Köpeğiniz için temel aşılar arasında kuduz, parvovirüs ve distemper yer alır. Aşılama programını veterinerinizle görüşmek önemlidir.**"

**Davranış Sorunları:**
"**Hayvanınızın davranışları, stres veya sağlık sorunları nedeniyle değişebilir. Bu konuda bir veteriner veya davranış uzmanına danışmanız faydalı olacaktır.**"

**Klinik Hizmetler:**
"**Patimat App üzerinden size en yakın veteriner kliniğini bulabilir ve randevu alabilirsiniz.**"

**Bakım Hizmetleri:**
"**Evcil hayvanınızın bakımına yardımcı olmak için Patimat App üzerinden barınma ve bakım hizmetlerinden yararlanabilirsiniz.**"

**Hayvan Sahiplendirme:**
"**Evcil hayvanınızı sahiplendirmek isterseniz, Patimat App üzerinden sahiplendirme ilanı verebilirsiniz.**"

**Kan Bağışı:**
"**Evcil hayvanınız kan bağışı yapabilecek durumdaysa, Patimat App üzerinden size en yakın kan bağışı noktalarını bulabilirsiniz. Ancak, bu işlem öncesinde veterinerinizin onayını almanız önemlidir.**"

Topluluk ve Destek:
**Patimat Topluluğu:**
Kullanıcılara, Patimat App'in topluluk özelliklerinden yararlanarak diğer hayvan sahiplerinden bilgi ve destek alabileceklerini hatırlat.
"**Toplulukta fikir alışverişinde bulunabilir ve sorularınıza daha hızlı yanıt bulabilirsiniz.**"

Özel Durumlar:
**Olumsuz veya Zararlı Sorular:**
Kullanıcı hayvan refahına aykırı bir soru sorduğunda:
"**Ben yalnızca hayvan refahını destekleyen bir veteriner asistanıyım.**"
"**Patimat App projesine ait bir yapay zeka olarak, hayvan refahını destekleyen önerilere odaklanırım.**"

**İlgisiz Sorular:**
Kullanıcı hayvanlarla ilgisi olmayan bir soru sorduğunda:
"**Patibox AI, yalnızca hayvan sağlığı ve refahı ile ilgilenen bir veteriner asistanıdır.**"

Dikkat Edilmesi Gereken Durumlar:
**Hamilelik ve Doğum:**
Hamile hayvanların doğum belirtileri hakkında bilgi ver.
Her durumda veteriner desteğini öner.

**Yavru Hayvan Bakımı:**
Yavru hayvanların bakım ve gelişim ihtiyaçlarını açıkla.
Çevre koşulları ve beslenme hakkında tavsiyelerde bulun.

**Yaşlı Hayvanlar:**
Yaşlı hayvanların özel ihtiyaçlarını belirt.
Sağlık yönetimi için veteriner öner.

**Otomatlar:**
Mama Otomatları Sistemi

Patimat App, sahipsiz hayvanların beslenme ihtiyaçlarını sürdürülebilir şekilde karşılamak amacıyla bağış destekli mama otomatları ile entegre bir sistem sunmaktadır. Bu sistem sayesinde, kullanıcılar dijital olarak bağış yaparak mama otomatlarını uzaktan doldurabilir ve sokak hayvanlarının düzenli beslenmesine katkıda bulunabilir.

Nasıl Çalışır?

Bağış Sistemi: Kullanıcılar, uygulama üzerinden belirli bir miktar bağış yaparak mama otomatlarına katkıda bulunur.
Otomatik Besleme: Toplanan bağışlar doğrultusunda belirlenen noktalardaki mama otomatları düzenli olarak doldurulur.
Akıllı Takip: Otomatların doluluk durumu, tüketim verileri ve ihtiyaç analizleri uygulama üzerinden takip edilebilir.
Konum Bazlı Destek: Kullanıcılar, uygulama üzerinden otomatların konumlarını görüntüleyerek diledikleri noktaya bağış yapabilir.

Neden Önemli?
Sürdürülebilir Beslenme: Sokak hayvanları için sürekli mama temini sağlanır.
Şeffaf Bağış Yönetimi: Blockchain teknolojisi ile uzun vadede bağış takibi planlanmaktadır.
Toplumsal Katılım: Hayvanseverler, küçük katkılarla büyük bir etki yaratabilir.
Bu sistem, hayvanseverlerin desteğini dijitalleştirerek etkili ve şeffaf bir çözüm sunmayı hedeflemektedir.

Önemli Not: Sadece Hayvanlar İle Alakalı Sorulara Yanıt Vereceksin Diğer Sorulan Sorulara İs Bu Yanıtı Ver : Üzgünüm ben Bir Veteriner Asistanı Chatbotuyum Bu Alanda Bilgi Sahibi Değilim Ben Sadece Hayvanlar İle İlgili Sorulara Cevap Veririm.
Ayrıca sorulan dili algıla ve ona göre cevap ver. 
sosyal medya hesaplarımız instagram @patimat.app , linkden hesabımız ise @patimat.app , web sitesmiz ise patimatapp.com
"""

# Vertex AI modelini başlatan ve yanıt üreten fonksiyon
def multiturn_generate_content(session_id, user_message):
    """
    Belirli bir kullanıcı için modelle etkileşime girer ve yanıt üretir.

    Args:
        session_id: Kullanıcının oturum kimliği.
        user_message: Kullanıcının gönderdiği mesaj.

    Returns:
        Modelin ürettiği metin yanıtı veya bir hata mesajı.
    """
    try:
        vertexai.init(project="the-other-459900-e8", location="us-central1")
        model = GenerativeModel(
            "gemini-2.0-flash-001",
            system_instruction=textsi_1
        )

        start_time = time.time()

        with user_chats_lock: # Kilitleme
            if session_id not in user_chats:
                # Kullanıcı için yeni bir sohbet başlat (ilk kez etkileşim kuruyorsa)
                user_chats[session_id] = model.start_chat()
            chat = user_chats[session_id]  # Kullanıcının mevcut sohbet nesnesini al

        try:
            response = chat.send_message(
                user_message,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            end_time = time.time()
            response_time = end_time - start_time
            print(f"API'den yanıt alma süresi: {response_time:.2f} saniye")
            time.sleep(random.uniform(0.5, 1)) # İsteğe bağlı bekleme. Tüm mesajlarda.
            return response.text if hasattr(response, 'text') else str(response)
        except Exception as e:
            if "429" in str(e):  # Hata mesajında "429" varsa (hız sınırı)
                wait_time = random.uniform(2, 5)  # 2 ile 5 saniye arasında rastgele bekle
                print(f"Hız sınırı aşıldı. {wait_time:.2f} saniye bekleniyor ve tekrar deneniyor...")
                time.sleep(wait_time)
                return multiturn_generate_content(session_id, user_message)  # Tekrar fonksiyonu çağır (tekrar dene)
            return f"Bir hata oluştu: {e}"  # Diğer hatalar için normal hata mesajı
    except Exception as e:
        print(f"Model başlatılırken hata: {e}")
        return "Üzgünüm, şu anda hizmet veremiyorum. Lütfen daha sonra tekrar deneyin."

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/get_response', methods=['POST'])
def get_response():
    """
    Kullanıcıdan gelen mesajı alıp, modeli çağırır ve yanıtı JSON formatında döndürür.
    """
    try:
        # JSON veya form verilerini kontrol et
        if request.is_json:
            data = request.get_json()
            user_message = data.get('message', '')
        else:
            user_message = request.form.get('message', '')

        if not user_message.strip():
            return jsonify({"response": "Lütfen geçerli bir mesaj girin."})

        # Session ID kontrolü
        if 'session_id' not in session:
            session['session_id'] = os.urandom(16).hex()
        session_id = session['session_id']

        # AI yanıtını al
        ai_response = multiturn_generate_content(session_id, user_message)
        return jsonify({"response": ai_response})

    except Exception as e:
        print(f"Hata oluştu: {e}")
        return jsonify({"response": "Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin."})

@app.route('/analysis')
def analysis():
    return render_template('analysis.html')

@app.route('/analyze_image', methods=['POST'])
def analyze_image():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        image = request.files['image']
        analysis_type = request.form.get('type', 'ocr')
        
        if image.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        if image and allowed_file(image.filename):
            # Güvenli dosya adı oluştur
            filename = secure_filename(image.filename)
            
            # Geçici olarak dosyayı kaydet
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(temp_path)
            
            try:
                if analysis_type == 'barcode':
                    # Barkod okuma işlemi
                    result = process_barcode(temp_path)
                else:
                    # OCR işlemi
                    result = process_ocr(temp_path)
                
                # Analiz sonuçlarını döndür
                return jsonify(result)
                
            finally:
                # Geçici dosyayı temizle
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
        return jsonify({'error': 'Invalid file type'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/search_product', methods=['POST'])
def search_product():
    try:
        data = request.get_json()
        product_name = data.get('product_name')
        
        if not product_name:
            return jsonify({'error': 'No product name provided'}), 400
            
        # Veri tabanında ürün ara
        result = search_product_database(product_name)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        rating = data.get('rating')
        comment = data.get('comment')
        
        if not all([product_id, rating]):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Geri bildirimi kaydet
        save_feedback(product_id, rating, comment)
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}

def process_barcode(image_path):
    # Barkod okuma işlemi burada yapılacak
    # Örnek yanıt
    return {
        'product_name': 'Örnek Ürün',
        'health_score': 85,
        'ingredients': [
            {'name': 'Doğal İçerik', 'status': 'safe', 'description': 'Doğal kaynaklı madde'},
            {'name': 'İşlenmiş Madde', 'status': 'warning', 'description': 'İşlenmiş içerik'},
            {'name': 'Yapay Katkı', 'status': 'danger', 'description': 'Yapay koruyucu'}
        ],
        'recommendations': [
            'Bu ürün orta kalitede içeriğe sahip',
            'Yapay katkı maddeleri içeriyor',
            'Doğal alternatifler mevcut'
        ]
    }

def process_ocr(image_path):
    # OCR işlemi burada yapılacak
    # Örnek yanıt
    return {
        'product_name': 'Örnek Ürün',
        'health_score': 85,
        'ingredients': [
            {'name': 'Doğal İçerik', 'status': 'safe', 'description': 'Doğal kaynaklı madde'},
            {'name': 'İşlenmiş Madde', 'status': 'warning', 'description': 'İşlenmiş içerik'},
            {'name': 'Yapay Katkı', 'status': 'danger', 'description': 'Yapay koruyucu'}
        ],
        'recommendations': [
            'Bu ürün orta kalitede içeriğe sahip',
            'Yapay katkı maddeleri içeriyor',
            'Doğal alternatifler mevcut'
        ]
    }

def search_product_database(product_name):
    # Veri tabanında ürün arama işlemi burada yapılacak
    # Örnek yanıt
    return {
        'product_name': 'Örnek Ürün',
        'health_score': 85,
        'ingredients': [
            {'name': 'Doğal İçerik', 'status': 'safe', 'description': 'Doğal kaynaklı madde'},
            {'name': 'İşlenmiş Madde', 'status': 'warning', 'description': 'İşlenmiş içerik'},
            {'name': 'Yapay Katkı', 'status': 'danger', 'description': 'Yapay koruyucu'}
        ],
        'recommendations': [
            'Bu ürün orta kalitede içeriğe sahip',
            'Yapay katkı maddeleri içeriyor',
            'Doğal alternatifler mevcut'
        ]
    }

def save_feedback(product_id, rating, comment):
    # Geri bildirimi veri tabanına kaydetme işlemi burada yapılacak
    pass

if __name__ == '__main__':
    logger.info('Starting application on port 8080...')
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=False) 