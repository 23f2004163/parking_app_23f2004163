from flask import Blueprint , render_template , flash , url_for , redirect , request , session 
from flask_login import login_required , current_user 
from .models import db , ParkingLot , ParkingSpot ,Vehicle , Reservation , User
from datetime import datetime , timedelta
from sqlalchemy import func , extract


routes = Blueprint('routes' , __name__) 
