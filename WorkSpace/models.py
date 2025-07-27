from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

# Initializing database object
db = SQLAlchemy()

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    fullname = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(120), nullable=False, default='user')

    vehicles = db.relationship('Vehicle', backref='user', lazy=True)
    reservations = db.relationship('Reservation', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

# Vehicle model
class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    registration_number = db.Column(db.String(20), unique=True, nullable=False)
    vehicle_type = db.Column(db.String(50))  # car, bus, lorry
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    reservations = db.relationship('Reservation', backref='vehicle', lazy=True)

    def __repr__(self):
        return f"<Vehicle {self.registration_number}>"

# Parking Lot model
class ParkingLot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prime_location_name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(250), nullable=False)
    pin_code = db.Column(db.Integer, nullable=False)
    maximun_number_of_spots = db.Column(db.Integer, nullable=False)
    is_deleted = db.Column(db.Boolean , default = False , nullable = False)

    spots = db.relationship('ParkingSpot', backref='lot', lazy=True)
    reservations = db.relationship('Reservation', backref='lot', lazy=True)

    def __repr__(self):
        return f"<ParkingLot {self.prime_location_name}>"

# Parking Spot model
class ParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    status = db.Column(db.String(1), nullable=False)  # 'F' or 'O'

    reservations = db.relationship('Reservation', backref='spot', lazy=True)

    def __repr__(self):
        return f"<ParkingSpot Lot#{self.lot_id} Status: {self.status}>"

# Reservation model
class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    parking_timestamp = db.Column(db.DateTime, nullable=False)
    leaving_timestamp = db.Column(db.DateTime, nullable=True)  # Now nullable
    parking_cost = db.Column(db.Float, nullable=True)          # Now nullable

    def __repr__(self):
        return f"<Reservation Spot#{self.spot_id} by User#{self.user_id}>"
