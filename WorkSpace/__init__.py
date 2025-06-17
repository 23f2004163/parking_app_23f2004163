from flask import Flask 
from .models import User , db 
from werkzeug.security import generate_password_hash
from .configurations import SECRET_KEY 



def create_app() : 
    
    app = Flask(__name__) 
    
    
    
    #load configurations 
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # we can avoid tracking modifications of objects 
    
    
    #initializing database to app
    db.init_app(app) 
    
    
    #initializing login manager 
    from flask_login import LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login' # redirects to login page if not logged in 
    
    
    @login_manager.user_loader 
    def load_user(user_id) : 
        return User.query.get(int(user_id)) # get the user object from the database using user id 
    
    
    #register the blue prints 
    from .auth import auth 
    from .routes import routes 
    app.register_blueprint(auth)
    app.register_blueprint(routes)
    
    
    with app.app_context() : 
        db.create_all() 
        
        
        if not User.query.filter_by(role='admin').first() : 
            admin_user = User(
                username =  'admin' ,
                email = 'admin123@gmail.com' ,
                fullname = 'admin' ,
                password = generate_password_hash('admin123' , method = 'pbkdf2:sha256' , salt_length = 8) ,
                role = 'admin' 
            )
            db.session.add(admin_user) 
            db.session.commit()
            
    return app 