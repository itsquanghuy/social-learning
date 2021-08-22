from flask import render_template
from datetime import date 
from time import sleep
import requests
from app.constraints import days_before_locked, max_due
from app.models import User, Warning
from app import db, create_app
from app.email import send_email


app = create_app()
app.app_context().push()
