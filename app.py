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
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return jsonify({
            'response': {
                'text': 'Ошибка: GEMINI_API_KEY не задан в Render.',
                'end_session': False
            },
            'version': '1.0'
        })

    # Отправляем единичный запрос к модели gemini-1.5-flash
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{
            "parts": [{"text": command}]
        }]
    }
    
    try:
        # Тайм-аут 3.5 секунды, чтобы уложиться в лимит Яндекса
        res = requests.post(url, json=payload, timeout=3.5)
        res_data = res.json()
        
        if res.status_code == 200:
            reply_text = res_data['candidates'][0]['content']['parts'][0]['text']
        else:
            err_msg = res_data.get('error', {}).get('message', res.text)
            reply_text = f"Ошибка API ({res.status_code}): {err_msg[:120]}"
            
    except requests.exceptions.Timeout:
        reply_text = "Gemini ответил слишком долго, попробуйте повторить запрос."
    except Exception as e:
        reply_text = f"Ошибка: {str(e)[:100]}"

    return jsonify({
        'response': {
            'text': reply_text[:1000],
            'end_session': False
        },
        'version': '1.0'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
