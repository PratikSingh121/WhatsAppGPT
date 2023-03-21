from flask import Flask, request , render_template
import os
import requests
import math
import openai
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from config import DbConfig
from flask_migrate import Migrate
from token import openai, wa_token

owner_phone = "onwer's phone number"

DEFAULT_TOKEN = 1000
PREMIUM_TOKEN = 3000

openai.api_key = openai
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__ , template_folder='templates')
app.config.from_object(DbConfig)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class database(db.Model):
    cno = db.Column(db.Integer, primary_key = True)
    user = db.Column(db.String(80), nullable = False)
    token = db.Column(db.Integer, nullable = False)
    premium = db.Column(db.Integer, nullable = False, default = 0)
    usage_times = db.Column(db.Integer, nullable = False)
    usage_words = db.Column(db.Integer, nullable = False)
    command_limit = db.Column(db.Integer, default = 100)

    def __repr__(self):
        return f'{self.cno}'

class chat_log(db.Model):
    __bind_key__ = 'chat'
    id = db.Column(db.Integer, primary_key = True)
    cno = db.Column(db.Integer, nullable = False)
    user = db.Column(db.String(100))
    prompt = db.Column(db.String(1000), nullable = False)

    def __repr__(self):
        return f'{self.cno}'

class host_msg(db.Model):
    __bind_key__ = 'host'
    id = db.Column(db.Integer, primary_key = True)
    cno = db.Column(db.Integer, nullable = False)
    user = db.Column(db.String(100))
    msg = db.Column(db.String(1000))

    def __repr__(self):
        return f'{self.user}'

@app.cli.command()
def scheduled():
    '''Resets all the token value at scheduled time'''
    for data in database.query.all():
        if data.premium == 1:
            val = PREMIUM_TOKEN
        else:
            val = DEFAULT_TOKEN
        data.token = val
        data.command_limit = 100
        db.session.add(data)
    db.session.commit()
    print('Changed data')

def commands(cno, user, prompt):
    command = prompt[0][1:]

    if command.lower() == 'host':
        message = prompt[1]
        obj = host_msg(cno = cno, user = user, msg = message)
        db.session.add(obj)
        db.session.commit()
        statement = f'''HOST COMMAND:
{user} ({cno}) : {message}'''
        send_msg(msg = statement, phone_no = owner_phone)

    if command.lower() == 'words':
        words_left = database.query.filter_by(cno = cno).first().token
        print(words_left)
        #monthly words to be added
        send_msg(words_left, cno)

def api_process(data):
    response = openai.Completion.create(
    model="text-davinci-003",
    prompt=data,
    temperature=0.9,
    max_tokens=500,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0.6
    # stop=[" Human:", " AI:"]
    )

    resp = response.choices[0].text
    print(resp)
    return resp

def send_msg(msg, phone_no):
    headers = {
        'Authorization': f'Bearer {wa_token}'
        # 'Accept-Language' : 'en-US,en;q=0.5'
        # user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'
   }
    json_data = {
        'messaging_product': 'whatsapp',
        'to': str(phone_no),
        'type': 'text',
        "text": {
            "body": msg
        }
    }
    response = requests.post('https://graph.facebook.com/v13.0/106970675621311/messages', headers=headers, json=json_data)
    #print(response.text)
        
def chat_record(phone_no ,user , prompt):
    obj = chat_log(cno = phone_no,user = user, prompt = prompt)
    db.session.add(obj)
    db.session.commit()

def token_calculation(phone_no, prompt):
    global data
    prompt_words = prompt.count(' ')+1
    pointer = db.session.query(database).filter_by(cno = phone_no).first()
    if prompt_words*2 < pointer.token:
        data = api_process(prompt)
        words_used = data.count(' ')+prompt_words+1 #Count the Number of words used
        
        #Updating value
        pointer.token =pointer.token - words_used 
        pointer.usage_words += words_used
        pointer.usage_times += 1  
        db.session.add(pointer)
        db.session.commit()
        return 1
    return 0

def create_data(phone_no, user):
    new = database(cno = phone_no, token = DEFAULT_TOKEN, premium = 0, user = user,usage_words = 0, usage_times = 0 ,command_limit = 100)
    db.session.add(new)
    db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/receive_msg', methods=['POST','GET'])
def webhook():
    # print(request)
    res = request.get_json()
    # print(res)

    try:
        if res['entry'][0]['changes'][0]['value']['messages'][0]['id']:
            phone_no = int(res['entry'][0]['changes'][0]['value']['messages'][0]['from'])
            user = res['entry'][0]['changes'][0]['value']['contacts'][0]['profile']['name']
            prompt = res['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']

            print(f"{user} - {prompt}")
            
            if prompt.startswith('/'):
                commands(phone_no, user, prompt.split(' ', 1))
            else:
                chat_record(phone_no,user, prompt)
                if phone_no not in [data.cno for data in database.query.all()]:
                    create_data(phone_no, user)
                if token_calculation(phone_no, prompt):
                    send_msg(data, phone_no)
                else:
                    send_msg('Daily Limit Exceeded', phone_no)
                
    except:
        pass
    return '200 OK HTTPS.'

if __name__ == "__main__":
    app.run(debug = True)