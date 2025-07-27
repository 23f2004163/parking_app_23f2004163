from flask import Blueprint , render_template , flash , url_for , redirect , request , session 
from flask_login import login_required , current_user 
from .models import db , ParkingLot , ParkingSpot ,Vehicle , Reservation , User
from datetime import datetime 
from sqlalchemy import func , extract
from werkzeug.security import generate_password_hash


routes = Blueprint('routes' , __name__) 


@routes.route('/')
def home():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('routes.admin'))
        elif current_user.role == 'user':
            return redirect(url_for('routes.user'))
    return redirect(url_for('auth.login'))


@routes.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        flash('You are not authorized to access this page', 'error')
        return redirect(url_for('auth.login'))
    lots = ParkingLot.query.all()
    return render_template('admin.html', current_user=current_user, lots=lots)


@routes.route('/user')
@login_required
def user():
    if current_user.role != 'user':
        flash('You are not authorized to access this page', 'error')
        return redirect(url_for('auth.login'))
    lots = ParkingLot.query.all()
    return render_template('user.html', current_user=current_user, lots=lots)
    
    
@routes.route('/user/user_profile') 
def user_profile() : 
    return render_template("user_profile.html" , user = current_user)
    
    
@routes.route('/admin/create_lot', methods=['GET', 'POST'])
def create_lot():
    if request.method == 'POST':
        # Get form data
        prime_location_name = request.form.get('prime_location_name')
        price = float(request.form.get('price'))
        address = request.form.get('address')
        pin_code = int(request.form.get('pin_code'))
        maximum_number_of_spots = int(request.form.get('maximum_number_of_spots'))

        # Create new parking lot instance
        new_parking_lot = ParkingLot(
            prime_location_name=prime_location_name,
            price=price,
            address=address,
            pin_code=pin_code,
            maximun_number_of_spots=maximum_number_of_spots
        )

        db.session.add(new_parking_lot)
        db.session.commit()

        # ✅ Create parking spots immediately after lot is created
        for _ in range(maximum_number_of_spots):
            spot = ParkingSpot(lot_id=new_parking_lot.id, status='F')
            db.session.add(spot)
        db.session.commit()

        flash(f'Parking lot created and {maximum_number_of_spots} spots added!', 'success')
        return redirect(url_for('routes.admin'))

    return render_template("add_parking_lot.html")


@routes.route('/admin/search_form', methods=['GET' , 'POST'])
def admin_search_form():
    search_query = request.args.get('search', '').strip().lower()
    sort = request.args.get('sort', '')
    lots = get_filtered_lots(search_query , sort = sort)
    return render_template('admin.html', lots=lots, sort = sort , search = search_query )


# helper function 
def get_filtered_lots(search_query='', sort=None):
    query = ParkingLot.query

    if search_query:
        query = query.filter(
            ParkingLot.prime_location_name.ilike(f"%{search_query}%") |
            ParkingLot.address.ilike(f"%{search_query}%")
        )

    if sort == 'cheapest':
        query = query.order_by(ParkingLot.price.asc())

    return query.all()

@routes.route('/admin/view_spots/<int:lot_id>')
@login_required
def view_spots(lot_id):
    parking_lot = ParkingLot.query.get_or_404(lot_id)
    spots = ParkingSpot.query.filter_by(lot_id=lot_id).all()
    return render_template('view_spots.html', parking_lot=parking_lot, spots=spots)


@routes.route('/admin/update/<int:lot_id>', methods=['GET', 'POST'])
def update(lot_id):
    parking_lot = ParkingLot.query.get_or_404(lot_id)

    if request.method == 'POST':
        # Get updated form data
        parking_lot.prime_location_name = request.form.get('prime_location_name').strip()
        parking_lot.price = float(request.form.get('price'))
        parking_lot.address = request.form.get('address')
        parking_lot.pin_code = int(request.form.get('pin_code'))
        
        new_max = int(request.form.get('maximum_number_of_spots'))
        current_spots = len(parking_lot.spots)

        # If new max is greater, add extra spots
        if new_max > current_spots:
            for _ in range(new_max - current_spots):
                new_spot = ParkingSpot(lot_id=parking_lot.id, status='F')
                db.session.add(new_spot)

        # Update the max
        parking_lot.maximun_number_of_spots = new_max

        # Commit changes to DB
        db.session.commit()

        flash('Parking lot updated successfully!', 'success')
        return redirect(url_for('routes.admin'))

    return render_template('update_parking_lot.html', parking_lot=parking_lot)

@routes.route('/delete_lot/<int:lot_id>')
@login_required
def delete_lot(lot_id):
    parking_lot = ParkingLot.query.get_or_404(lot_id)

    # Check if any spots are occupied
    if ParkingSpot.query.filter_by(lot_id=lot_id, status='O').first():
        flash("Cannot delete: Some parking spots are currently occupied.", "error")
        return redirect(url_for('routes.admin'))

    # Check if any spot has reservation history
    for spot in parking_lot.spots:
        if Reservation.query.filter_by(spot_id=spot.id).first():
            flash("Cannot delete: One or more spots have reservation history.", "error")
            return redirect(url_for('routes.admin'))

    # Safe to delete all spots and the lot
    ParkingSpot.query.filter_by(lot_id=lot_id).delete()
    db.session.delete(parking_lot)
    db.session.commit()

    flash(f"Parking lot '{parking_lot.prime_location_name}' deleted successfully.", "success")
    return redirect(url_for('routes.admin'))



@routes.route('/admin/delete_spot/<int:spot_id>')
def delete_spot(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    lot_id = spot.lot_id

    # Check if the spot has been used in any reservation
    has_reservations = Reservation.query.filter_by(spot_id=spot.id).first()

    if spot.status == 'O':
        flash("Can't delete an occupied spot", "danger")
    elif has_reservations:
        flash("Can't delete spot with reservation history", "danger")
    else:
        db.session.delete(spot)
        db.session.commit()
        flash("Spot deleted", "success")

    return redirect(url_for('routes.view_spots', lot_id=lot_id))



@routes.route('/admin/users')
@login_required  # Optional: secure it
def all_users():
    users = User.query.all()
    now = datetime.now()
    return render_template('users_info.html', users=users, now=now)



@routes.route('/admin/charts')
def charts():
    # Chart 1: Reservations per Lot
    lot_reservations = db.session.query(
        ParkingLot.prime_location_name,
        func.count(Reservation.id)
    ).join(Reservation).group_by(ParkingLot.id).all()

    lot_names = [name for name, _ in lot_reservations]
    reservation_counts = [count for _, count in lot_reservations]

    # Chart 2: Booked vs Available
    total_spots = db.session.query(ParkingSpot).count()
    booked_spots = db.session.query(ParkingSpot).filter(ParkingSpot.status == 'O').count()
    available_spots = total_spots - booked_spots

    return render_template('charts.html',
                           lot_names=lot_names,
                           reservation_counts=reservation_counts,
                           booked_spots=booked_spots,
                           available_spots=available_spots) 
    
    
    



# USER PAGE 


@routes.route('/user/search_form', methods=['GET'])
def user_search_form():
    search_query = request.args.get('search', '').strip().lower()
    sort = request.args.get('sort', '')
    lots = get_filtered_lots(search_query , sort = sort)
    return render_template('user.html', lots=lots, sort = sort , search = search_query  )


@routes.route('/user/spots/<int:lot_id>')
def show_spots(lot_id):
    spots = ParkingSpot.query.filter_by(lot_id=lot_id, status='F').all()
    parking_lot = ParkingLot.query.get_or_404(lot_id)
    return render_template('spots.html', spots=spots, parking_lot=parking_lot)




@routes.route('/user/reserve/<int:lot_id>', methods=['GET', 'POST'])
@login_required
def reserve_spot(lot_id):
    parking_lot = ParkingLot.query.get_or_404(lot_id)
    
    if request.method == 'POST':
        vehicle_number = request.form.get('vehicle_number')
        vehicle_type = request.form.get('vehicle_type')

        # Auto-assign the first available free spot
        spot = ParkingSpot.query.filter_by(lot_id=lot_id, status='F').first()
        if not spot:
            flash("No available spots in this lot.", "danger")
            return redirect(url_for('routes.user'))

        # Check if vehicle already exists
        existing_vehicle = Vehicle.query.filter_by(registration_number=vehicle_number).first()
        if existing_vehicle:
            vehicle = existing_vehicle
        else:
            vehicle = Vehicle(
                user_id=current_user.id,
                registration_number=vehicle_number,
                vehicle_type=vehicle_type
            )
            db.session.add(vehicle)
            db.session.commit()  # So we can use vehicle.id

        # Create reservation
        now = datetime.now()

        try:
            reservation = Reservation(
                user_id=current_user.id,
                lot_id=lot_id,
                spot_id=spot.id,
                vehicle_id=vehicle.id,
                parking_timestamp=now,
                leaving_timestamp=None,          # Set as null
                parking_cost=None                 # Set as null
            )
            db.session.add(reservation)

            # Update spot status to 'Occupied'
            spot.status = 'O'

            db.session.commit()
            flash(f"Reservation successful! Assigned Spot #{spot.id}", "success")
            return redirect(url_for('routes.user'))

        except Exception as e:
            db.session.rollback()
            print("Reservation Error:", e)
            flash("Something went wrong while reserving spot", "error")
            return redirect(url_for('routes.reserve_spot', lot_id=lot_id))

    return render_template('reserve_form.html', lot=parking_lot)


@routes.route('/user/my_reservations')
@login_required
def my_reservations():
    reservations = Reservation.query.filter_by(user_id=current_user.id).all()
    return render_template('my_reservations.html', reservations=reservations, now=datetime.now())



@routes.route('/user/checkout/<int:reservation_id>', methods=['GET'])
@login_required
def checkout(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    lot = ParkingLot.query.get(reservation.lot_id)
    

    # Prevent someone else's reservation being checked out
    if reservation.user_id != current_user.id:
        flash("Unauthorized access", "error")
        return redirect(url_for('routes.user'))

    # Update timestamps and cost
    reservation.leaving_timestamp = datetime.now()
    
    cost = calculate_parking_cost(reservation.parking_timestamp , reservation.leaving_timestamp, lot.price)
    
    reservation.parking_cost = cost 

    # Free up the spot
    reservation.spot.status = 'F'

    db.session.commit()
    flash(f"Checked out successfully. Total cost: ₹{reservation.parking_cost}", "success")
    return redirect(url_for('routes.my_reservations'))

def calculate_parking_cost(parking_timestamp, leaving_timestamp, price_per_hour):
    # Calculate total duration in hours (rounded up)
    duration = leaving_timestamp - parking_timestamp
    total_hours = int(duration.total_seconds() // 3600)
    if duration.total_seconds() % 3600 != 0:
        total_hours += 1  # round up partial hours

    # Calculate cost
    total_cost = total_hours * price_per_hour
    return total_cost 


@routes.route('/user/history')
@login_required
def user_history():
    # Query: count of reservations grouped by year and month for the current user
    reservations = db.session.query(
        extract('year', Reservation.parking_timestamp).label('year'),
        extract('month', Reservation.parking_timestamp).label('month'),
        func.count(Reservation.id)
    ).filter_by(user_id=current_user.id).group_by('year', 'month').order_by('year', 'month').all()

    # Prepare labels and counts
    month_labels = []
    counts = []
    for year, month, count in reservations:
        label = f"{datetime(int(year), int(month), 1).strftime('%B %Y')}"
        month_labels.append(label)
        counts.append(count)

    return render_template('user_history.html', labels=month_labels, counts=counts)


@routes.route('/user/update_profile/' , methods = ['GET','POST'])
def update_profile() : 
    if request.method == "POST" :
        username = request.form.get('username')
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        password = request.form.get('password') 
        
        
        current_user.username = username 
        current_user.fullname = fullname 
        current_user.email = email 
        
        if password : 
            current_user.password = generate_password_hash(password) 
            
        # commit the changes to db 
        db.session.commit()
        flash ('profile update succesfully !' , 'success')
        return redirect(url_for('routes.user')) 
    
    return render_template('update_profile.html' , user=current_user) 
        
        
    
    
    
    