from flask import request, jsonify

@app.route('/analyze_ingredients', methods=['POST'])
def analyze_ingredients():
    data = request.get_json()
    ingredients_text = data.get('ingredients', '')
    ingredients = [i.strip() for i in ingredients_text.split(',') if i.strip()]

    # Basit analiz algoritması (örnek)
    safe_list = ['tavuk eti', 'hindi eti', 'kuzu eti', 'somon', 'pirinç', 'patates', 'havuç', 'elma posası', 'bezelye']
    danger_list = ['bha', 'bht', 'sodyum nitrit', 'sodyum benzoat']
    warning_list = ['mısır gluteni', 'soya unu', 'arpa', 'selüloz', 'bezelye proteini']

    analyzed = []
    score = 100
    for ing in ingredients:
        ing_lower = ing.lower()
        if any(d in ing_lower for d in danger_list):
            analyzed.append({'name': ing, 'status': 'danger', 'description': 'Zararlı veya tartışmalı içerik'})
            score -= 30
        elif any(w in ing_lower for w in warning_list):
            analyzed.append({'name': ing, 'status': 'warning', 'description': 'Dikkat edilmesi gereken içerik'})
            score -= 10
        elif any(s in ing_lower for s in safe_list):
            analyzed.append({'name': ing, 'status': 'safe', 'description': 'Faydalı içerik'})
        else:
            analyzed.append({'name': ing, 'status': 'warning', 'description': 'Bilinmeyen içerik'})
            score -= 5

    score = max(0, min(100, score))
    if score >= 80:
        score_label = "Çok İyi"
    elif score >= 51:
        score_label = "Orta"
    else:
        score_label = "Kötü"

    summary = f"Ürün {len(ingredients)} içerik içeriyor. Skor: {score}."
    advice = "İçerikleri detaylı inceleyin ve veterinerinize danışın."

    return jsonify({
        'score': score,
        'score_label': score_label,
        'ingredients': analyzed,
        'summary': summary,
        'advice': advice
    }) 