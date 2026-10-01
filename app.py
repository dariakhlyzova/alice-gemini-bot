import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Список моделей для проверки по порядку
MODELS_TO_TRY = [
    "gemini-3.8-flash",
    "gemini-3.5-flash",
    "gemini-2.5-flash"
]

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json() or {}
    
    user_request = data.get('request', {})
    command = user_request.get('command', '').strip()
    is_new = data.get('session', {}).get('new', False)
    
    # При старте навыка / приветствии
    if is_new or not command:
        return jsonify({
            'response': {
                'text': 'Привет! Я на связи с Gemini. О чём поговорим?',
                'end_session': False
            },
            'version': '1.0'
        })
    
    # Проверка ключа
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return jsonify({
            'response': {
                'text': 'Ошибка: GEMINI_API_KEY не задан в настройках Render.',
                'end_session': False
            },
            'version': '1.0'
        })

    reply_text = None
    last_error = ""

    # Перебираем актуальные модели Google Gemini
    for model_name in MODELS_TO_TRY:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [{"text": command}]
            }]
        }
        
        try:
            res = requests.post(url, json=payload, timeout=10)
            res_data = res.json()
            
            if res.status_code == 200:
                reply_text = res_data['candidates'][0]['content']['parts'][0]['text']
                break  # Успешный ответ найден, выходим из цикла
            else:
                last_error = res_data.get('error', {}).get('message', res.text)
        except Exception as e:
            last_error = str(e)
            continue

    if not reply_text:
        reply_text = f"Ошибка API: {last_error[:120]}"

    return jsonify({
        'response': {
            'text': reply_text[:1000],  # Лимит Алисы по длине
            'end_session': False
        },
        'version': '1.0'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
