import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json() or {}
    
    user_request = data.get('request', {})
    command = user_request.get('command', '').strip()
    is_new = data.get('session', {}).get('new', False)
    
    # При приветствии / первом запуске
    if is_new or not command:
        return jsonify({
            'response': {
                'text': 'Привет! Я на связи с Gemini. О чём поговорим?',
                'end_session': False
            },
            'version': '1.0'
        })
    
    # Проверяем наличие ключа
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return jsonify({
            'response': {
                'text': 'Ошибка: Не задан GEMINI_API_KEY в настройках Render.',
                'end_session': False
            },
            'version': '1.0'
        })

    # Прямой HTTP-запрос к официальному REST API Gemini 2.0 Flash
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": command}]
        }]
    }
    
    try:
        res = requests.post(url, json=payload, timeout=12)
        res_data = res.json()
        
        if res.status_code == 200:
            reply_text = res_data['candidates'][0]['content']['parts'][0]['text']
        else:
            err_msg = res_data.get('error', {}).get('message', res.text)
            reply_text = f"Ошибка API ({res.status_code}): {err_msg[:120]}"
            
    except Exception as e:
        print(f"Request Error: {e}")
        reply_text = f"Ошибка соединения с Gemini: {str(e)[:100]}"

    return jsonify({
        'response': {
            'text': reply_text[:1000],  # Ограничение длины ответа Алисы
            'end_session': False
        },
        'version': '1.0'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
