import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Список моделей от самой приоритетной к резервным
MODELS_TO_TRY = [
    "gemini-3.8-flash",
    "gemini-2.5-flash",
    "gemini-1.5-flash"
]

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
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return jsonify({
            'response': {
                'text': 'Ошибка: GEMINI_API_KEY не задан в Render.',
                'end_session': False
            },
            'version': '1.0'
        })

    reply_text = None
    last_error = ""

    # Пробуем отправить запрос, перебирая модели при 503 / 404
    for model_name in MODELS_TO_TRY:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [{"text": command}]
            }]
        }
        
        try:
            # Небольшой тайм-аут на каждую попытку, чтобы суммарно успеть до 4.5с
            res = requests.post(url, json=payload, timeout=2.0)
            res_data = res.json()
            
            if res.status_code == 200:
                reply_text = res_data['candidates'][0]['content']['parts'][0]['text']
                break  # Успех — выходим из цикла!
            else:
                err_msg = res_data.get('error', {}).get('message', res.text)
                last_error = f"{res.status_code}: {err_msg[:80]}"
                # Если 503 или 404 — цикл идет к следующей модели
        except Exception as e:
            last_error = str(e)[:80]
            continue

    if not reply_text:
        reply_text = f"Сервер временно перегружен ({last_error}). Попробуйте ещё раз через пару секунд."

    return jsonify({
        'response': {
            'text': reply_text[:1000],  # Ограничение Алисы
            'end_session': False
        },
        'version': '1.0'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
