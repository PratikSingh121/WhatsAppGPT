import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class DbConfig(object):
	SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')
	SQLALCHEMY_BINDS = {
		'chat': 'sqlite:///' + os.path.join(BASE_DIR, 'chat_log.db'),
		'host':	'sqlite:///' + os.path.join(BASE_DIR, 'host_msg.db')
	}


	SQLALCHEMY_TRACK_MODIFICATIONS = False