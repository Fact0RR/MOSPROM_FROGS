from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/ping')
def ping():
    return "", 200

@app.route('/mock', methods=['POST'])
def mock():
    json_data = request.get_json()
    print(json_data)
    return jsonify({"message": f"mock-данные от recognizer\nТело запроса: {json_data}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3333)