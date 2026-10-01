import os
from flask import Flask, request, jsonify
from google import genai

app = Flask(__name__)

# Получаем API ключ
api_key = os.environ.get("GEMINI_API_KEY")

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json() or {}
    
    user_request = data.get('request', {})
    command = user_request.get('command', '').strip()
    is_new = data.get('session', {}).get('new', False)
    
    # При старте навыка
    if is_new or not command:
        return jsonify({
            'response': {
                'text': 'Привет! Я на связи с Gemini. О чём поговорим?',
                'end_session': False
            },
            'version': '1.0'
        })
    
    # Обращение к Gemini
    try:
        # Инициализируем клиент с ключом
        client = genai.Client(api_key=api_key)
        
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=command,
        )
        reply_text = response.text if response.text else "Gemini прислал пустой ответ."
    except Exception as e:
        print(f"Gemini API Error: {e}")
        reply_text = f" Ошибка API: {str(e)[:100]}"
        
    return jsonify({
        'response': {
            'text': reply_text[:1000], # Ограничение длины Алисы
            'end_session': False
        },
        'version': '1.0'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
