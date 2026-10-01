import os
from flask import Flask, request, jsonify
from google import genai

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

@app.route('/webhook', methods=['POST'])
def webhook():
    event = request.json or {}
    
    user_text = event.get('request', {}).get('original_utterance', '')
    session_is_new = event.get('session', {}).get('new', False)

    if session_is_new or not user_text:
        reply_text = "Привет! Я на связи с Gemini. О чём поговорим?"
    else:
        try:
            if not client:
                reply_text = "Ошибка: не настроен GEMINI_API_KEY на сервере."
            else:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=user_text,
                )
                reply_text = response.text
        except Exception as e:
            reply_text = "Произошла ошибка при обработке запроса в Gemini."

    return jsonify({
        "version": event.get('version', '1.0'),
        "session": event.get('session', {}),
        "response": {
            "text": reply_text,
            "end_session": False
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
