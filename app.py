import os
from flask import Flask, request, jsonify
from google import genai

app = Flask(__name__)

# Список моделей для проверки по очереди
MODELS_TO_TRY = [
    'gemini-2.0-flash',
    'gemini-1.5-flash',
    'gemini-2.5-flash',
    'gemini-flash'
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
    
    # Отправка запроса в Gemini
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return jsonify({
            'response': {
                'text': ' Ошибка: Не задан GEMINI_API_KEY в Render.',
                'end_session': False
            },
            'version': '1.0'
        })

    client = genai.Client(api_key=api_key)
    reply_text = None
    last_error = ""

    # Перебираем варианты моделей
    for model_name in MODELS_TO_TRY:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=command,
            )
            if response.text:
                reply_text = response.text
                break
        except Exception as e:
            last_error = str(e)
            print(f"Failed with {model_name}: {e}")
            continue

    if not reply_text:
        reply_text = f" Ошибка API: {last_error[:120]}"

    return jsonify({
        'response': {
            'text': reply_text[:1000],  # Лимит Алисы
            'end_session': False
        },
        'version': '1.0'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
