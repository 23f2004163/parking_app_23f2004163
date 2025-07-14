from flask import Blueprint , request , flash , redirect , url_for , render_template 
from .models import User , db
from werkzeug.security import check_password_hash , generate_password_hash
from flask_login import login_user , logout_user , current_user , login_required


auth = Blueprint('auth' , __name__) 


# login route 

@auth.route('/login' , methods = ['GET' , 'POST']) 
def login() :
    if request.method == 'POST' :  
        identifier = request.form.get('identifier') 
        password = request.form.get('password') 
        
        
        user = User.query.filter((User.email == identifier) | (User.username == identifier)).first() 
        
        
        if user and check_password_hash(user.password , password) : 
            login_user(user , remember = True) 
            flash('Logged in succesfully!' , category = 'success') 
            if user.role == 'admin' : 
                return redirect(url_for('routes.admin')) 
            else : 
                return redirect(url_for('routes.user')) 
        else : 
            flash('Invalid credentials' , category = 'error') 
        
    return render_template('login.html') 


@auth.route('/signup', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        fullname = request.form.get('fullname')

        user_by_email = User.query.filter_by(email=email).first()
        user_by_username = User.query.filter_by(username=username).first()

        if user_by_email:
            flash('Email already exists', category='error')
        elif user_by_username:
            flash('Username already exists', category='error')
        else:
            new_user = User(
                email=email,
                username=username,
                fullname=fullname,
                password=generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash('Account created successfully', category='success')
            return redirect(url_for('auth.login'))

    return render_template('sign_up.html')


@auth.route('/logout') 
@login_required
def logout() : 
    logout_user() 
    flash('Logged out successfully' , category = 'success')
    return redirect(url_for('auth.login')) 
    