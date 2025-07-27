# importing important packages used for our project 

from flask import Blueprint , render_template , flash , url_for , redirect , request  
from flask_login import current_user , login_required 
from .models import ParkingLot , db , ParkingSpot , Reservation , User , Vehicle 
from datetime import datetime 
from sqlalchemy import func , extract 
from werkzeug.security import generate_password_hash







# initializing routes 
routes = Blueprint('routes' , __name__ )

""" FIRST SECTION : ADMIN RELATED CONTENTS AND ROUTES"""

# now lets start with the first page of the app 
@ routes.route('/')
def Home_page() : 
    
    if current_user.is_authenticated :
         
        if current_user.role == 'admin' : 
            return redirect(url_for('routes.admin_dashboard'))
        
        else :   
            return redirect(url_for('routes.user_dashboard')) 
        
    return redirect(url_for('auth.login')) 

# Admin page 
@routes.route('/admin') 
@login_required # will just check whether the user is authenticated or not 

def admin_dashboard() : 
    
    if current_user.role == 'admin' : 
        
        #extracting parking lots from the db 
        parking_lots = ParkingLot.query.filter_by(is_deleted = False).all() 
        return render_template ('admin_dashboard.html' , current_user = current_user , lots = parking_lots)
    
    else : 
        
        flash('oops , you are not permitted to access this page' , category = 'error')
        return redirect(url_for('auth.login')) 
    


# creating parking lot 
@routes.route('/admin/create_parking_lot' , methods = ['GET' , 'POST' ]) 
def create_parking_lot() : 
    
    if request.method == "POST" : 
        
        #get the form data 
        prime_location_name = request.form.get('prime_location_name') 
        price = request.form.get('price') 
        address = request.form.get('address') 
        pincode = request.form.get('pin_code') 
        maximum_number_of_spots = request.form.get('maximum_number_of_spots') 
        
        
        # now , let's convert some data types of these fields to store in the db 
        price = float(price) 
        pincode = int(pincode) 
        maximum_number_of_spots = int(maximum_number_of_spots)
        
        
        #add the fields to db 
        try : 
            
            new_parking_lot = ParkingLot(
                
                prime_location_name = prime_location_name ,
                price = price , 
                address = address , 
                pin_code = pincode ,
                maximun_number_of_spots = maximum_number_of_spots
            )
            
            db.session.add(new_parking_lot) 
            db.session.commit()  
            
            
            # we can also create parking spots immediately after parking lot is created 
            
            for _ in range(maximum_number_of_spots) : 
                parking_spot = ParkingSpot (
                    lot_id = new_parking_lot.id ,
                    status = "F"
                ) 
                db.session.add(parking_spot)
                
             
            db.session.commit() 
            
            flash (f'Parking lot created and {maximum_number_of_spots} spots added successfully !' , category = 'success')
            
            return redirect(url_for('routes.admin_dashboard')) 
            
            
        except Exception as error : 
            
            db.session.rollback() 
            
            print( "creation error :" , error)
            flash ( "Something went wrong while creating parking lot" , category = 'error') 
            
    return render_template("add_parking_lot.html") 



# Updating Parking lot 
@routes.route('/admin/update_parking_lot/<int:lot_id>', methods=["GET", "POST"])
def update_parking_lot(lot_id):
    parking_lot = ParkingLot.query.filter_by(id = lot_id , is_deleted = False).first_or_404()

    if request.method == "POST":
        parking_lot.prime_location_name = request.form.get('prime_location_name')
        parking_lot.price = float(request.form.get('price'))
        parking_lot.address = request.form.get('address')
        parking_lot.pin_code = int(request.form.get('pin_code'))

        new_maximum_spot = int(request.form.get('maximum_number_of_spots'))
        current_spots = len(parking_lot.spots)

        if new_maximum_spot >= current_spots:
            try:
                for _ in range(new_maximum_spot - current_spots):
                    new_spot = ParkingSpot(
                        lot_id=parking_lot.id,
                        status="F"
                    )
                    db.session.add(new_spot)

                parking_lot.maximum_number_of_spots = new_maximum_spot

                db.session.commit()
                flash('Hurray! Parking lot updated successfully', category="success")
                return redirect(url_for('routes.admin_dashboard'))  # ✅ successful return here

            except Exception as error:
                db.session.rollback()
                print("update error:", error)
                flash('Oops! Something went wrong while updating the parking lot', category='error')
                return redirect(url_for('routes.update_parking_lot', lot_id=lot_id))

        else:
            flash('Oops! Reducing number of spots is not allowed', category='error')
            return redirect(url_for('routes.update_parking_lot', lot_id=lot_id))

    return render_template('update_parking_lot.html', parking_lot=parking_lot)
            
# delete parking lot 
@routes.route('/admin/delete_parking_lot/<int:lot_id>') 
@login_required

def delete_parking_lot(lot_id) : 
    parking_lot = ParkingLot.query.filter_by(id = lot_id , is_deleted = False).first_or_404() 
    
    
    #before deleting , check if a parking spot in the lot is occupied or not   
    if ParkingSpot.query.filter_by(lot_id = lot_id , status = 'O').first() :
        flash("Oops ! cannot delete this parking lot , some spots are occupied" , category = 'error') 
        
        return redirect(url_for('routes.admin_dashboard')) 
    
    
    # checking resrvation history 
    has_reservations = Reservation.query.filter_by(lot_id = lot_id).first()
    
    
    try : 
        
        if has_reservations:
            
            # we are going to soft delete the lot to maintain the data integrity 
            parking_lot.is_deleted = True
            db.session.commit()
            flash(f"Hurray ! Parking lot available in {parking_lot.prime_location_name} was archived" , category = 'success')
        
        else : 
               
            #deleting spots associated with the parking lot
            ParkingSpot.query.filter_by(lot_id = lot_id).delete() 
            db.session.delete(parking_lot) 
            db.session.commit() 
        
            flash(f"parking lot in {parking_lot.prime_location_name} got successfully deleted !" , category = 'success')
        
        return redirect(url_for('routes.admin_dashboard'))
        
    except Exception as error : 
            
        db.session.rollback() 
        print('Deletion error:' , error) 
        flash("oops! unexpected error occured while deleting the lot" , category = 'error') 
        return redirect(url_for('routes.admin_dashboard'))
    
        

# view parking spots 
@routes.route('/admin/view_parking_spots/<int:lot_id>')
def view_parking_spots(lot_id) : 
    
    parking_lot = ParkingLot.query.filter_by(id = lot_id , is_deleted = False).first_or_404()
    parking_spots = ParkingSpot.query.filter_by(lot_id = lot_id ).all() 
    
    return render_template ('view_parking_spots.html' , parking_lot = parking_lot , spots = parking_spots)



#deleting parking spot 

@routes.route('/admin/delete_parking_spot/<int:spot_id>' , methods = ["GET"]) 
def delete_parking_spot(spot_id) : 
    parking_spot = ParkingSpot.query.get_or_404(spot_id) 
    parking_lot_id = parking_spot.lot_id
    
    
    
    #now lets check if the spot is reserved or not 
    is_reserved = Reservation.query.filter_by(spot_id = parking_spot.id).first() 
    
    # if parking spot is occupied , we cannot delete that 
    if parking_spot.status == 'O' : 
        flash("Oops! cannot delete this parking spot" , category = 'error') 
    
    elif is_reserved : 
        flash('Oops! cannot delete this spot , it has reservation history' , category = 'error') 
    
    else : 
        
        try : 
            
            db.session.delete(parking_spot) 
            db.session.commit() 
            flash("Hurray ! the spot has been deleted successfully" , category = 'success') 
            
        except Exception as error : 
            
            db.session.rollback()
            print("Deletion error :" , error) 
            flash("something went wrong while deleting the spot!" , category = 'error')
            
    
    return redirect(url_for('routes.view_parking_spots' , lot_id = parking_lot_id)) # providing lot id over here will ensure that after deleting the spot , we stay intact inside of the parking lot 
            
            
        
# overview users of the application 

@routes.route('/admin/show_users') 
@login_required 

def show_users() : 
    users = User.query.all() 
    now = datetime.now()
    
    return render_template('users_info.html' , users = users , now = now) 


# summary charts - admin panel 

@routes.route('/admin/admin_charts') 
def admin_charts() : 
    
    # chart 1 : for reservation per parking lot  
    
    lot_reservations = db.session.query(
        ParkingLot.prime_location_name ,
        func.count(Reservation.id)
    ).join(Reservation).group_by(ParkingLot.id).all() 
    
    # this will return list of parking lot name and number of reservations of each lot 
    
    #extact name alone
    parking_lot_names = [name for name,_ in lot_reservations] 
    
    #extract count alone 
    reservation_counts = [count for _,count in lot_reservations]
    
    
    #chart 2 : Booked spots vs available spots 
    
    total_spots = db.session.query(ParkingSpot).count()
    booked_spots = db.session.query(ParkingSpot).filter(ParkingSpot.status == 'O').count() 
    available_spots = total_spots - booked_spots 
    
    
    return render_template('admin_charts.html' ,
                           lot_names = parking_lot_names , 
                           reservation_counts = reservation_counts ,
                           booked_spots = booked_spots , 
                           available_spots = available_spots)
    
    
# search functionalities 

@routes.route('/admin/search_form' , methods = ["GET" , "POST"])
def admin_search_form() : 
    
    search_query = request.args.get('search', '').strip().lower() 
    sort = request.args.get('sort', '')
    
    filtered_lots = get_filtered_lots(search_query,sort = sort) 
    
    return render_template('admin_dashboard.html' , lots = filtered_lots , search = search_query , sort = sort ) 



# helper function for filtering lots 

def get_filtered_lots(search_query = '' , sort = None) : 
    
    Query = ParkingLot.query.filter_by(is_deleted = False) 
    
    if search_query : 
        
        Query = Query.filter(
            ParkingLot.prime_location_name.ilike(f"%{search_query}%") |
            ParkingLot.address.ilike(f"%{search_query}%")  
        )
        
    if sort == 'cheapest' : 
        
        Query = Query.order_by(ParkingLot.price.asc()) 
        
    return Query.all() 



""" SECTION 2 : USER RELATED CONTENTS AND ROUTES """

#User page 

@routes.route('/user') 
@login_required

def user_dashboard() : 
    if current_user.role == 'user' : 
        
        parking_lots = ParkingLot.query.filter_by(is_deleted = False).all() 
        
        return render_template('user_dashboard.html' , current_user = current_user , lots = parking_lots )
    
    else : 
        flash("Oops ! you are not permitted to access this page !" , category = "error") 
        return redirect(url_for('auth.login')) 
    
    
# user profile 

@routes.route('/user/user_profile') 
@login_required 

def user_profile() : 
    return render_template('user_profile.html' , user = current_user) 


#update user profile 

@routes.route('/user/update_profile' , methods = ['GET' , 'POST']) 
def update_profile() : 
    
    if request.method == "POST" :
        
        username = request.form.get('username')
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        password = request.form.get('password')
        
        
        try : 
            
            #update the current_user information 
        
            current_user.username = username 
            current_user.fullname = fullname 
            current_user.email = email 
            
            if password : 
                
                current_user.password = generate_password_hash(password) 
                
            db.session.commit()
            flash('Hurray ! your profile was updated successfully' , category = "success")
            return redirect(url_for('routes.user_profile'))
                
        except Exception as error : 
            
            db.session.rollback()
            print("update error:" , error)
            flash('Oops ! something went wrong while updating the user profile' , category = 'error') 
            
            return redirect(url_for('routes.user_profile')) 
        
    
    return render_template('update_profile.html' , user= current_user) 


# parking lots will be displayed in user page itself , so need to create a route for viewing spots 

   
@routes.route('/user/show_parking_spots/<int:lot_id>') 
@login_required 

def show_parking_spots(lot_id) : 
    
    parking_spots = ParkingSpot.query.filter_by(lot_id = lot_id , status = "F").all() 
    parking_lot = ParkingLot.query.filter_by(id = lot_id , is_deleted = False).first_or_404() 
    
    return render_template('show_parking_spots.html' , spots = parking_spots , parking_lot = parking_lot) 


# Reserving parking lot based on spot availability 

@routes.route('/user/reserve_spot/<int:lot_id>' , methods = ["GET" , "POST"]) 
@login_required 

def reserve_spot(lot_id) : 
    
    parking_lot = ParkingLot.query.filter_by(id = lot_id , is_deleted = False).first_or_404() 
    
    if request.method == "POST"  : 
        
        vehicle_registration_number = request.form.get('vehicle_number') 
        vehicle_type = request.form.get('vehicle_type') 
        
        #we are going to auto assign the first available spot 
        parking_spot = ParkingSpot.query.filter_by(lot_id = lot_id , status = "F").first() 
        
        #return to dashboard if no spots available 
        if not parking_spot : 
            
            flash("Oops! there is no parking spot available in the parking lot" , category = "error") 
            return redirect (url_for('routes.user_dashboard')) 
        
        
        
        try : 
            
            # check if this user already has his/her vehicle registered and upload to db
            existing_vehicle = Vehicle.query.filter_by(registration_number = vehicle_registration_number).first()
        
            if existing_vehicle : 
                vehicle = existing_vehicle 
                
            else : 
                
                vehicle = Vehicle(
                    user_id = current_user.id , 
                    registration_number = vehicle_registration_number , 
                    vehicle_type = vehicle_type 
                )
                
                db.session.add(vehicle)
                db.session.commit() # we are commiting vehicle changes to db because , we need vehicle id for reserving 
                
        except Exception as error : 
            
            db.session.rollback()
            print("vehicle uploading error :" , error) 
            flash("Oops ! something went wrong while adding vehicle data" , category = "error")
            return redirect(url_for('routes.reserve_spot', lot_id = lot_id))
        
        # Now let's create reservation 
        
        now = datetime.now() 
        
        try : 
            
            reservation = Reservation(
                user_id = current_user.id , 
                lot_id = lot_id ,
                spot_id = parking_spot.id ,
                vehicle_id = vehicle.id ,
                parking_timestamp = now , 
                leaving_timestamp = None ,  # let it be null 
                parking_cost = None   # let it be null 
            )
            
            db.session.add(reservation)
            
            
            # dont forget to update the parking spot status to "occupied"
            
            parking_spot.status = 'O' 
            
            db.session.commit() # now finally commmit the changes to db 
            flash(f"Hurray ! your Reservation is successful and your assigned spot is {parking_spot.id}" , category = "success") 
            return redirect(url_for('routes.user_dashboard'))
        
        except Exception as error : 
            
            db.session.rollback() 
            print("reservation error :" ,error)
            flash("Oops ! something went wrong while reserving the spot " , category = "error") 
            return redirect(url_for('routes.reserve_spot' , lot_id = lot_id ))
        
    return render_template('reserve_form.html' , lot = parking_lot )

#check out form 

@routes.route('/user/checkout/<int:reservation_id>' , methods = ['GET']) 
@login_required

def checkout(reservation_id) : 
    
    reservation = Reservation.query.get_or_404(reservation_id)
    parking_lot = ParkingLot.query.filter_by(id = reservation.lot_id , is_deleted = False).first_or_404()
    
    try : 
        
        #we need to update timestamp and cost 
        reservation.leaving_timestamp = datetime.now() 
    
        total_parking_cost = calculate_parking_cost(reservation.parking_timestamp , reservation.leaving_timestamp , parking_lot.price)
    
        reservation.parking_cost = total_parking_cost 
        
        #update the spot in spot table 
        reservation.spot.status = 'F' 
        
        db.session.commit()
        flash(f'Hurray ! checked out of the parking spot successfully , your total cost is ₹{reservation.parking_cost} ' , category = 'success')
        return redirect(url_for('routes.my_reservations'))
    
    except Exception as error : 
        
        db.session.rollback()
        print("checkout error :", error)
        flash('Oops! something went wrong while checking out' , category = 'error') 
        return redirect(url_for('routes.my_reservations'))
    

# helper function for calculating parking cost

def calculate_parking_cost(parking_timestamp,leaving_timestamp,price_per_hour) :
    
    Duration = leaving_timestamp - parking_timestamp 
    Total_hours = int(Duration.total_seconds() // 3600) 
     
    if Duration.total_seconds() % 3600 != 0 : 
        Total_hours += 1  
         
    # cost calculation 
    Total_cost = Total_hours*price_per_hour
    return Total_cost

#see your reservation history (including ongoing) 

@routes.route('/user/my_reservations') 
@login_required

def my_reservations() :
    
    reservations = Reservation.query.filter_by(user_id = current_user.id).all()

    return render_template('my_reservations.html' , reservations = reservations , now = datetime.now() )
            
      
#user chart 

@routes.route('/user/chart') 
@login_required

def user_chart() : 
     
    #we can visualize count of reservations of user grouped bu year and month of the currrent user 
    reservations = db.session.query(
        extract('year' , Reservation.parking_timestamp).label('year') ,
        extract('month' , Reservation.parking_timestamp).label('month') ,
        func.count(Reservation.id)
    ).filter_by(user_id = current_user.id).group_by('year' , 'month').order_by('year','month').all() #=> [(2024 , 5 , 1) , (2024 ,6,1)] here this in the format of (year , month ,date) 
    
    #preparing labels for chart 
    month_labels = []
    counts = []
    
    for year, month , count in reservations : 
        #string manipulation 
        temp_label = f"{datetime(int(year),int(month),1).strftime('%B %Y')}" # => "Jan 2024"
        month_labels.append(temp_label) 
        counts.append(count) 
        
    return render_template('user_chart.html' , labels = month_labels , counts = counts) 
        

#user search functionality 

@routes.route('/user/user_search_form' , methods = ['GET']) 
@login_required

def user_search_form() : 
    search_query = request.args.get('search', '').strip().lower()
    sort = request.args.get('sort', '')
    lots = get_filtered_lots(search_query , sort = sort)
    
    return render_template('user_dashboard.html', lots=lots, sort = sort , search = search_query  )  
            
            

    
