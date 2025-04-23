from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
from . import db  # Import `db` from __init__.py

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('passenger', 'driver', name='user_roles'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class DriverProfile(db.Model):
    __tablename__ = 'driver_profiles'
    driver_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    vehicle_model = db.Column(db.String(100), nullable=False)
    vehicle_number = db.Column(db.String(50), nullable=False)
    rating = db.Column(db.Float, default=5.0)

    # Relationship
    user = db.relationship('User', backref=db.backref('driver_profile', uselist=False))

# class Ride(db.Model):
#     __tablename__ = 'rides'
#     ride_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     driver_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
#     origin = db.Column(db.String(100), nullable=False)
#     destination = db.Column(db.String(100), nullable=False)
#     departure_date = db.Column(db.Date, nullable=False)
#     departure_time = db.Column(db.Time, nullable=False)
#     price_per_seat = db.Column(db.Numeric(10, 2), nullable=False)
#     seats_available = db.Column(db.Integer, nullable=False)
#     created_at = db.Column(db.DateTime, server_default=db.func.now())

#     driver = db.relationship('User', backref='rides')


class Ride(db.Model):
    __tablename__ = 'rides'

    ride_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    origin = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    departure_time = db.Column(db.String(100), nullable=False)
    departure_date = db.Column(db.String(100), nullable=False)
    price_per_seat = db.Column(db.Float, nullable=False)
    seats_available = db.Column(db.Integer, nullable=False)

    driver = db.relationship('User', backref=db.backref('rides', lazy=True))

    def __repr__(self):
        return f"<Ride {self.ride_id} - {self.origin} to {self.destination}>"



class Booking(db.Model):
    __tablename__ = 'bookings'

    booking_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('rides.ride_id'), nullable=False)
    passenger_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    seats_booked = db.Column(db.Integer, nullable=False)
    special_requests = db.Column(db.String(255), default=None)
    status = db.Column(db.Enum('confirmed', 'cancelled', name='booking_status'), default='confirmed')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)

    # Relationships
    ride = db.relationship('Ride', backref=db.backref('bookings', lazy=True))
    passenger = db.relationship('User', backref=db.backref('bookings', lazy=True))

    def __repr__(self):
        return f"<Booking {self.booking_id} - Ride {self.ride_id} - Passenger {self.passenger_id}>"