import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
	SECRET_KEY = os.getenv("SECRET_KEY") or "123456"
	BASIC_AUTH_USERNAME = os.getenv("BASIC_AUTH_USERNAME") or "root1234"
	BASIC_AUTH_PASSWORD = os.getenv("BASIC_AUTH_PASSWORD") or "123456789"
	uri = os.getenv("DATABASE_URL")
	if uri.startswith("postgres://"):
		uri = uri.replace("postgres://", "postgresql://", 1)
	SQLALCHEMY_DATABASE_URI = uri or 'sqlite:///' + os.path.join(basedir, 'app.db')
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	MAIL_SERVER = os.getenv("MAIL_SERVER")
	MAIL_PORT = int(os.getenv("MAIL_PORT", 25))
	MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", None)
	MAIL_USERNAME = os.getenv("MAIL_USERNAME")
	MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
	ADMINS = ["vuhuycoder@gmail.com"]
	POSTS_PER_PAGE = 5
	