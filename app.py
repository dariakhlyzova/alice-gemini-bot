import os
from flask import Flask, request, jsonify
from google import genai

app = Flask(__name__)

# Инициализируем клиент Gemini
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json() or {}
    
    user_request = data.get('request', {})
    command = user_request.get('command', '').strip()
    is_new = data.get('session', {}).get('new', False)
    
    # При приветствии
    if is_new or not command:
        return jsonify({
            'response': {
                'text': 'Привет! Я на связи с Gemini. О чём поговорим?',
                'end_session': False
            },
            'version': '1.0'
        })
    
    # Запрос к Gemini
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=command
        )
        reply_text = response.text if response.text else "Не удалось получить текст ответа."
    except Exception as e:
        print(f"Gemini API Error: {e}")
        reply_text = "Произошла ошибка при вызове Gemini API."
        
    return jsonify({
        'response': {
            'text': reply_text[:1000],  # Ограничение длины ответа для Алисы
            'end_session': False
        },
        'version': '1.0'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
