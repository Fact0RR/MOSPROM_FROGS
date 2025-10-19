from flask import Flask, jsonify, request
import whisper
import os

app = Flask(__name__)

# Загружаем модель Whisper medium (вторая по размеру после large)   
print("Загрузка модели Whisper medium...")
model = whisper.load_model("base")
print("Модель загружена успешно!")

@app.route('/ping')
def ping():
    return "", 200

@app.route('/mock', methods=['POST'])
def mock():
    try:
        json_data = request.get_json()
        print(f"Полученные данные: {json_data}")
        
        # Получаем URL голосового файла
        voice_url = json_data.get("voice_url", "")
        
        # В реальном приложении здесь бы происходила загрузка и обработка файла
        # Но по условию задачи файлы скачивать не нужно
        
        # Имитация распознавания текста с помощью Whisper
        # В реальном приложении здесь был бы код:
        result = model.transcribe("http://minio:9000" + voice_url)
        question_text = result["text"]
        
        # Для демонстрации используем заглушку
        # question_text = "Это имитация распознанного текста с помощью Whisper medium модели"
        
        response = {
            "message": question_text,
            "voice_url": voice_url
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Ошибка при обработке запроса: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3333)