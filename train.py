from flask import Flask, request
import requests
import math
import json

app = Flask(__name__)
 
@app.route('/')
def index():
    return "Hello"

def check(data):
    url = "https://trains.p.rapidapi.com/"

    payload = {"search": data}
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": "b295275b53mshc7668843fa2766fp1ddcb2jsn3de912235fdf",
        "X-RapidAPI-Host": "trains.p.rapidapi.com"
    }

    response = requests.request("POST", url, json=payload, headers=headers).text
    data = json.loads(response)
    return data

def send_msg(msg, phone_no):
    headers = {
        'Authorization': 'Bearer EABU18QMaBQ4BAG0ETRrw3OwedWow3IOGLxT22KyPZBVBVMER77ZCusybFQ2lERrB5a2yWFXN4aZCT6bc6zH1IZAobylzb2f29t4U40aeZCxYdeAM9wDZBogZAx95VL9Et44G438ojPE0913lXG9SpeZBg5tHp7v4YsEoNxnS0DO0QI73G5IqlZCveUVHfEeMmmE4IhJv0xZBwcy9aE97ZBuZCZBmB'
        # 'Accept-Language' : 'en-US,en;q=0.5'
        #?ser-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'
   }
    json_data = {
        'messaging_product': 'whatsapp',
        'to': phone_no,
        'type': 'text',
        "text": {
            "body": msg
        }
    }
    response = requests.post('https://graph.facebook.com/v13.0/106970675621311/messages', headers=headers, json=json_data)
    print(response.text)

@app.route('/receive_msg', methods=['POST','GET'])
def webhook():
    print(request)
    res = request.get_json()
    print(res)

    try:
        if res['entry'][0]['changes'][0]['value']['messages'][0]['id']:
            phone_no = res['entry'][0]['changes'][0]['value']['messages'][0]['from']
            data = check(res['entry'][0]['changes'][0]['value']['messages'][0]['text']['body'])
            send_msg(json.dumps(data, indent = 1)[1:-1] ,phone_no)
                
    except:
        pass
    return '200 OK HTTPS.'
 
  
if __name__ == "__main__":
    app.run(debug=True)
