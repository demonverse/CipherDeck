from flask import Flask, render_template, request, jsonify
from ciphers import CIPHERS

app = Flask(__name__)


@app.route('/')
def index():
    cipher_info = {k: {"name": v.name, "description": v.description, "key_hint": v.key_hint}
                   for k, v in CIPHERS.items()}
    return render_template('index.html', ciphers=cipher_info)


@app.route('/process', methods=['POST'])
def process():
    data = request.get_json()
    cipher_id = data.get('cipher', '')
    text = data.get('text', '')
    key = data.get('key', '')
    mode = data.get('mode', 'encrypt')

    if cipher_id not in CIPHERS:
        return jsonify({'error': 'Unknown cipher'}), 400

    cipher = CIPHERS[cipher_id]
    try:
        if mode == 'encrypt':
            result = cipher.encrypt(text, key)
        else:
            result = cipher.decrypt(text, key)
        return jsonify({'result': result})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    # host='0.0.0.0' makes it reachable on local network
    app.run(host='0.0.0.0', port=5000, debug=False)
