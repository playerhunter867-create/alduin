from flask import Flask, request, jsonify, render_template_string
from database import get_phone_info
import re
import os

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Phone Detective</title>
    <style>
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(145deg, #0b0e1a 0%, #1a1f2f 100%);
            color: #e0e0e0;
            height: 100vh;
            margin: 0;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: rgba(20, 25, 40, 0.9);
            backdrop-filter: blur(12px);
            padding: 3rem 4rem;
            border-radius: 40px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.8);
            text-align: center;
            min-width: 420px;
        }
        input {
            width: 100%;
            padding: 18px 20px;
            font-size: 1.4rem;
            border: none;
            border-radius: 60px;
            background: #2a3050;
            color: #fff;
            outline: 2px solid #3e4a7a;
            margin: 20px 0;
            box-sizing: border-box;
        }
        button {
            background: #6c5ce7;
            color: #fff;
            border: none;
            padding: 16px 40px;
            font-size: 1.4rem;
            border-radius: 60px;
            cursor: pointer;
            transition: 0.2s;
            font-weight: bold;
            box-shadow: 0 0 20px #6c5ce7aa;
        }
        button:hover {
            background: #5a4bd1;
            transform: scale(1.02);
        }
        .result-box {
            margin-top: 30px;
            background: #0e121f;
            padding: 20px;
            border-radius: 20px;
            text-align: left;
            border-left: 6px solid #6c5ce7;
        }
        .result-box h3 {
            margin-top: 0;
            color: #a29bfe;
        }
        .result-box p {
            margin: 8px 0;
        }
        .error {
            color: #ff6b6b;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📡 Введите номер телефона</h1>
        <input type="text" id="phoneInput" placeholder="+7 900 123 45 67">
        <button onclick="lookup()">🔍 Вычислить всё</button>
        <div id="result" class="result-box"></div>
    </div>
    <script>
        function lookup() {
            const phone = document.getElementById('phoneInput').value;
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = '⏳ Загрузка...';
            
            fetch('/lookup', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({phone: phone})
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    resultDiv.innerHTML = `<span class="error">❌ ${data.error}</span>`;
                    return;
                }
                resultDiv.innerHTML = `
                    <h3>✅ Результат по номеру ${data.phone_raw}</h3>
                    <p><strong>Оператор:</strong> ${data.operator}</p>
                    <p><strong>Регион:</strong> ${data.region}</p>
                    <p><strong>Город:</strong> ${data.city}</p>
                    <p><strong>Часовой пояс:</strong> ${data.timezone}</p>
                    <p><strong>Координаты:</strong> ${data.lat}, ${data.lon}</p>
                    <p><strong>Вероятный адрес:</strong> ${data.street}</p>
                    <p><strong>Владелец (демо):</strong> ${data.full_name}, возраст ${data.age} лет</p>
                    <p style="font-size:0.8rem; color:#888;">* Персональные данные сгенерированы для демонстрации</p>
                `;
            })
            .catch(err => {
                resultDiv.innerHTML = `<span class="error">⚠️ Ошибка сервера: ${err}</span>`;
            });
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/lookup', methods=['POST'])
def lookup():
    data = request.get_json()
    phone = data.get('phone', '').strip()
    
    raw = re.sub(r'\D', '', phone)
    if len(raw) < 7:
        return jsonify({'error': 'Слишком короткий номер'}), 400
    
    country_code = ''
    if raw.startswith('7') or raw.startswith('8'):
        country_code = '7'
        raw = raw[1:] if raw.startswith('7') else raw[1:]
    elif raw.startswith('1'):
        country_code = '1'
        raw = raw[1:]
    elif raw.startswith('44'):
        country_code = '44'
        raw = raw[2:]
    elif raw.startswith('49'):
        country_code = '49'
        raw = raw[2:]
    else:
        country_code = '7'
        if raw.startswith('7'):
            raw = raw[1:]
    
    if len(raw) >= 3:
        def_code = raw[:3]
    else:
        return jsonify({'error': 'Недостаточно цифр'}), 400
    
    info = get_phone_info(country_code, def_code)
    
    if not info:
        return jsonify({'error': 'Оператор/регион не найдены'}), 404
    
    import random
    names = ['Иванов Иван Иванович', 'Петров Пётр Петрович', 'Сидоров Сидор Сидорович',
             'Кузнецова Анна Сергеевна', 'Смирнов Алексей Владимирович']
    streets = ['Ленина', 'Пушкина', 'Гагарина', 'Советская', 'Мира', 'Центральная']
    
    info['full_name'] = random.choice(names)
    info['age'] = random.randint(18, 75)
    info['street'] = f"ул. {random.choice(streets)}, д. {random.randint(1, 150)}"
    info['phone_raw'] = phone
    
    return jsonify(info)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)