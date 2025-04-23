from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from .models import db, User, Ride, Booking
from flask_login import current_user
from werkzeug.security import check_password_hash, generate_password_hash
import re,logging



# Create a Blueprint for the main module
bp = Blueprint('main', __name__)

# Route: Home Page
@bp.route('/')
def home():
    """
    Render the home page.
    """
    return render_template('home.html')



# Route: User Registration
@bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handle user registration.
    For GET requests, render the registration form.
    For POST requests, validate and save user data.
    """
    if request.method == 'POST':
        # Retrieve form data
        name = request.form.get('name')
        email = request.form.get('email')

        # Defensive programming: Validate form inputs
        if not name or not email:
            flash('Name and email are required.', 'error')
            return redirect(url_for('main.register'))

        # Regex for validating the email format
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            flash('Invalid email format. Please enter a valid email address.', 'error')
            return redirect(url_for('main.register'))

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email is already registered. Please log in.', 'error')
            return redirect(url_for('main.register'))

        # Save the new user to the database
        try:
            new_user = User(name=name, email=email)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful!', 'success')
            return redirect(url_for('main.home'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again later.', 'error')
            return redirect(url_for('main.register'))

    # Render the registration form for GET requests
    return render_template('register.html')



# Route: Driver Dashboard (Signed-in)
@bp.route('/driver-signin', methods=['GET'])
def driver_signin():
    """
    Display the driver dashboard only if the user is signed in as a driver.
    Redirect unauthorized users to the home page.
    """
    if session.get('role') != 'driver':
        flash('Unauthorized access!', 'error')
        return redirect(url_for('main.home'))
    return render_template('driver_signin.html')


# Route: Passenger Dashboard (Signed-in)
@bp.route('/passenger-signin', methods=['GET'])
def passenger_signin():
    """
    Display the passenger dashboard only if the user is signed in as a passenger.
    Redirect unauthorized users to the home page.
    """
    if session.get('role') != 'passenger':
        flash('Unauthorized access!', 'error')
        return redirect(url_for('main.home'))
    return render_template('passenger_signin.html')

# Route: Logout
@bp.route('/logout', methods=['GET'])
def logout():
    """
    Log out the user by clearing the session and redirecting to the home page.
    """
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('main.home'))


# Route: Login
@bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login.
    For GET requests, render the login form.
    For POST requests, validate credentials and log the user in.
    """
    if request.method == 'POST':
        # Retrieve form data
        email = request.form['email']
        password = request.form['password']

        # Email regex validation
        email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_pattern, email):
            flash('Invalid email format.', 'error')
            return redirect(url_for('main.login'))

        # Fetch user from the database
        user = User.query.filter_by(email=email).first()

        # Validate user and password
        if user and check_password_hash(user.password, password):
            # Store user information in session
            session['user_id'] = user.user_id
            session['email'] = user.email
            session['role'] = user.role
            session['name'] = user.name

            flash('Login successful!', 'success')

            # Lambda function to validate role
            is_valid_role = lambda role: role in ['driver', 'passenger']
            if is_valid_role(user.role):
                # Redirect based on role
                if user.role == 'driver':
                    return redirect(url_for('main.driver_signin'))
                elif user.role == 'passenger':
                    return redirect(url_for('main.passenger_signin'))
            else:
                flash('Unknown role. Contact support.', 'error')
                return redirect(url_for('main.home'))
        else:
            flash('Invalid email or password.', 'error')

    return render_template('login.html')


# Route: Post a Ride
@bp.route('/post-ride', methods=['GET', 'POST'])
def post_ride():
    """
    Handle ride posting by a logged-in driver.
    For POST requests, validate and save ride details.
    """
    if request.method == 'POST':
        # Retrieve form data
        origin = request.form['origin']
        destination = request.form['destination']
        departure_date = request.form['departure_date']
        departure_time = request.form['departure_time']
        price_per_seat = request.form['price_per_seat']
        seats_available = request.form['seats_available']
        driver_id = session.get('user_id')  # Get the logged-in driver's ID

        # Validate session and form data
        if not driver_id:
            flash('You need to log in first!', 'error')
            return redirect(url_for('main.login'))

        # Create and save the new ride
        new_ride = Ride(
            driver_id=driver_id,
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            departure_time=departure_time,
            price_per_seat=price_per_seat,
            seats_available=seats_available
        )

        db.session.add(new_ride)
        db.session.commit()

        flash('Ride posted successfully!', 'success')
        return redirect(url_for('main.manage_rides'))

    return render_template('post_ride.html')


# Route: Manage Rides
@bp.route('/manage-rides', methods=['GET'])
def manage_rides():
    """
    Display all rides posted by the logged-in driver.
    Redirect to login if the user is not authenticated.
    """
    driver_id = session.get('user_id')  # Get logged-in driver's ID
    if not driver_id:
        flash("You need to log in first!", "error")
        return redirect(url_for('main.login'))

    # Fetch rides for the logged-in driver
    rides = Ride.query.filter_by(driver_id=driver_id).all()
    return render_template('driver.html', rides=rides)


# Route: Signup
@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    Handle user signup.
    For POST requests, validate inputs, hash passwords, and register a new user.
    """
    if request.method == 'POST':
        try:
            # Retrieve form data
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']
            role = request.form['role']

            logging.debug(f"Form data received: Name={name}, Email={email}, Role={role}")

            # Check if email already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('Email is already registered.', 'error')
                return render_template('signup.html')

            # Hash password
            hashed_password = generate_password_hash(password)

            # Create and save the new user
            new_user = User(name=name, email=email, password=hashed_password, role=role)
            db.session.add(new_user)
            db.session.commit()

            logging.debug("New user registered successfully.")

            flash('Account created successfully!', 'success')
            return redirect(url_for('main.login'))
        except Exception as e:
            logging.error(f"Error during signup: {e}")
            flash('An error occurred during signup. Please try again later.', 'error')

    return render_template('signup.html')



# Route: Passenger Page

@bp.route('/passenger-dashboard', methods=['GET'])
def passenger_dashboard():
    """
    Displays the passenger dashboard with available rides and booked rides.

    Available rides are fetched from the database and filtered for those with
    available seats. Booked rides specific to the logged-in user are also displayed.
    """
    if 'user_id' not in session:
        flash("You must be logged in to access the dashboard.", "error")
        return redirect(url_for('main.login'))

    # Fetch available rides
    rides = (
        db.session.query(
            Ride.ride_id,
            Ride.origin,
            Ride.destination,
            Ride.departure_time,
            Ride.departure_date,
            Ride.price_per_seat.label("price"),
            Ride.seats_available,
            User.name.label("driver"),
        )
        .join(User, Ride.driver_id == User.user_id)
        .filter(Ride.seats_available > 0)
        .all()
    )

    # Convert query results to dictionaries for easier handling
    rides_data = [
        {
            "id": ride.ride_id,
            "origin": ride.origin,
            "destination": ride.destination,
            "departure_time": ride.departure_time,
            "departure_date": ride.departure_date,
            "price": ride.price,
            "seats_available": ride.seats_available,
            "driver": ride.driver,
        }
        for ride in rides
    ]

    # Fetch booked rides for the current user
    booked_rides = (
        db.session.query(
            Ride.ride_id,
            Ride.origin,
            Ride.destination,
            Ride.departure_time,
            Ride.departure_date,
            Ride.price_per_seat.label("price"),
            Booking.seats_booked,
            Booking.status,
        )
        .join(Booking, Ride.ride_id == Booking.ride_id)
        .filter(Booking.passenger_id == session['user_id'])
        .all()
    )

    booked_rides_data = [
        {
            "id": ride.ride_id,
            "origin": ride.origin,
            "destination": ride.destination,
            "departure_time": ride.departure_time,
            "departure_date": ride.departure_date,
            "price": ride.price,
            "seats_booked": ride.seats_booked,
            "status": ride.status,
        }
        for ride in booked_rides
    ]

    # Render the passenger dashboard with rides and booked rides
    return render_template('passenger.html', rides=rides_data, booked_rides=booked_rides_data)



@bp.route('/cancel-booking', methods=['POST'])
def cancel_booking():
    """
    Cancels a booking made by the logged-in passenger and updates ride availability.
    Validates the booking ID and updates the booking status and ride availability.
    """
    booking_id = request.form.get('ride_id')
    if not booking_id:
        flash("No booking ID provided.", "error")
        return redirect(url_for('main.passenger_dashboard'))

    # Find the booking for the logged-in user
    booking = Booking.query.filter_by(
        booking_id=booking_id, passenger_id=session['user_id']
    ).first()

    if not booking:
        flash("Booking not found or unauthorized action.", "error")
        return redirect(url_for('main.passenger_dashboard'))

    # Cancel the booking
    booking.status = 'cancelled'
    db.session.commit()

    # Update the ride's seat availability
    ride = Ride.query.get(booking.ride_id)
    if ride:
        ride.seats_available += booking.seats_booked
        db.session.commit()

    flash("Booking cancelled successfully.", "success")
    return redirect(url_for('main.passenger_dashboard'))


@bp.route('/search-rides', methods=['POST'])
def search_rides():
    """
    Searches for available rides based on user-provided criteria such as origin,
    destination, date, and time.
    """
    origin = request.form.get('origin')
    destination = request.form.get('destination')
    date = request.form.get('date')
    time = request.form.get('time')

    # Fetch rides from the database
    rides = Ride.query.filter(
        Ride.origin.ilike(f"%{origin}%"),
        Ride.destination.ilike(f"%{destination}%"),
        Ride.departure_date == date,
        Ride.departure_time == time,
        Ride.seats_available > 0,
    ).all()

    # Render the results on the passenger page
    return render_template('passenger.html', rides=rides)


@bp.route('/dashboard', methods=['GET'])
def dashboard():
    """
    Displays the dashboard with all available rides and booked rides for the current user.

    Available rides are shown with filtering for seat availability. Booked rides
    are fetched with details of the user's confirmed bookings.
    """
    if 'user_id' not in session:
        flash("Please log in to access the dashboard.", "error")
        return redirect(url_for('main.login'))

    # Fetch available rides
    rides = Ride.query.filter(Ride.seats_available > 0).all()

    # Fetch booked rides for the logged-in user
    booked_rides = (
        db.session.query(Ride, Booking)
        .join(Booking, Ride.ride_id == Booking.ride_id)
        .filter(
            Booking.passenger_id == session['user_id'],
            Booking.status == 'confirmed',
        )
        .add_columns(Booking.seats_booked, Booking.booking_id)
        .all()
    )

    # Render the dashboard
    return render_template('dashboard.html', rides=rides, booked_rides=booked_rides)



# Route: Driver Dashboard
@bp.route('/driver-dashboard', methods=['GET'])
def driver_dashboard():
    # Ensure the user is logged in
    if 'user_id' not in session:
        return redirect(url_for('main.login'))  # Redirect to login if not logged in

    # Example posted rides (replace with actual database query)
    rides = [
        # Uncomment and update when integrating with the database
        # {
        #     'id': 1,
        #     'origin': 'City A',
        #     'destination': 'City B',
        #     'departure_time': '10:00 AM',
        #     'departure_date': '2024-11-24',
        #     'price': 15,
        #     'seats_available': 3
        # },
    ]
    logging.debug(f"Driver Dashboard accessed by user {session['user_id']}. Rides count: {len(rides)}")
    return render_template('driver.html', rides=rides)

# Route: Edit Ride
@bp.route('/edit-ride', methods=['GET', 'POST'])
def edit_ride():
    # Get the ride ID from query parameters
    ride_id = request.args.get('ride_id')
    ride = Ride.query.get(ride_id)

    if not ride:
        logging.error(f"Ride ID {ride_id} not found.")
        flash("Ride not found.", "error")
        return redirect(url_for('main.manage_rides'))

    if request.method == 'POST':
        try:
            # Update ride details
            ride.origin = request.form['origin']
            ride.destination = request.form['destination']
            ride.departure_date = request.form['departure_date']
            ride.departure_time = request.form['departure_time']
            ride.price_per_seat = float(request.form['price_per_seat'])
            ride.seats_available = int(request.form['seats_available'])

            # Commit changes
            db.session.commit()
            logging.info(f"Ride ID {ride_id} updated successfully.")
            flash("Ride updated successfully!", "success")
        except Exception as e:
            logging.error(f"Error updating ride ID {ride_id}: {str(e)}")
            flash("An error occurred while updating the ride.", "danger")

        return redirect(url_for('main.manage_rides'))

    logging.debug(f"Edit Ride page accessed for Ride ID {ride_id}.")
    return render_template('edit_ride.html', ride=ride)

# Route: Delete Ride
@bp.route('/delete-ride', methods=['GET'])
def delete_ride():
    # Get the ride ID from query parameters
    ride_id = request.args.get('ride_id')
    ride = Ride.query.get(ride_id)

    if not ride:
        logging.error(f"Ride ID {ride_id} not found.")
        flash("Ride not found.", "error")
        return redirect(url_for('main.manage_rides'))

    try:
        # Delete the ride
        db.session.delete(ride)
        db.session.commit()
        logging.info(f"Ride ID {ride_id} deleted successfully.")
        flash("Ride deleted successfully!", "success")
    except Exception as e:
        logging.error(f"Error deleting Ride ID {ride_id}: {str(e)}")
        flash("An error occurred while deleting the ride.", "danger")

    return redirect(url_for('main.manage_rides'))

# Route: Book a Ride
@bp.route('/book-ride/<int:ride_id>', methods=['POST'])
def book_ride(ride_id):
    # Ensure the user is logged in
    if 'user_id' not in session:
        return redirect(url_for('main.login'))  # Redirect to login if not logged in

    seats_requested = request.form.get('seats_requested')
    if not seats_requested.isdigit():
        logging.warning(f"Invalid seat request by user {session['user_id']}.")
        flash("Invalid number of seats requested.", "danger")
        return redirect(url_for('main.passenger_dashboard'))

    seats_requested = int(seats_requested)
    ride = Ride.query.filter_by(ride_id=ride_id).first()

    if not ride:
        logging.error(f"Ride ID {ride_id} not found.")
        flash("Ride not found.", "danger")
        return redirect(url_for('main.passenger_dashboard'))

    if ride.seats_available < seats_requested:
        logging.warning(f"Not enough seats available for Ride ID {ride_id}. Requested: {seats_requested}, Available: {ride.seats_available}")
        flash("Not enough seats available.", "danger")
        return redirect(url_for('main.passenger_dashboard'))

    try:
        # Create a new booking
        booking = Booking(
            ride_id=ride_id,
            passenger_id=session['user_id'],
            seats_booked=seats_requested,
            status='confirmed'
        )

        # Update the available seats
        ride.seats_available -= seats_requested

        db.session.add(booking)
        db.session.commit()
        logging.info(f"Booking successful: Ride ID {ride_id}, User ID {session['user_id']}, Seats: {seats_requested}")
        flash(f"Ride booked successfully for {seats_requested} seat(s).", "success")
    except Exception as e:
        logging.error(f"Error booking ride ID {ride_id}: {str(e)}")
        flash("An error occurred while booking the ride.", "danger")

    return redirect(url_for('main.passenger_dashboard'))


# Route for Contact Us page
@bp.route('/contact')
def contact():
    return render_template('contact.html')

