from flask import Blueprint , request , flash , redirect , url_for , render_template 
from .models import User , db
from werkzeug.security import check_password_hash , generate_password_hash
from flask_login import login_user , logout_user , current_user , login_required


auth = Blueprint('auth' , __name__) 