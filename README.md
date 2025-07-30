A web-based parking lot reservation system built using Flask, SQLite, Bootstrap, and Jinja2. This app allows users to reserve, check in, check out, and view reservation history, while admins can manage parking lots, monitor usage, and analyze statistics via charts.

🚀 Features
👤 User Registration & Login

📍 Reserve parking spots in different locations

⏱ Auto-leaves after 2 hours or manual checkout

📊 Admin dashboard with charts (reservations & availability)

🧮 Automatic parking cost calculation

📅 User reservation history with charts

🔐 Role-based access control (Admin / User)


🧰 Tech Stack
Backend: Flask, SQLAlchemy

Frontend: HTML, Bootstrap, Chart.js , Css

Database: SQLite

Auth: Flask-Login

DB SCHEMA : 

1.  Users : it stores user information and the fields are username , fullname , email , password and role ( eg : admin / user) 

2. Vehicles : it stores User’s registered vehicles and the fields are registration_number , user_id (foreign key)  and vehicle_type ( eg : car / bike / auto)

3. ParkingLot : it stores the details of each parking lot location  and the fields are prime_location_name , price , address , pincode , maximum_number_of_spots  and is_deleted flag ( eg : True / False)

4. ParkingSpot : it stores individual parking spots within a lot and the fields are lot_id (foreign key)  and status ( eg : ‘O’ / ‘F’ )

5. Reservations  : it stores record of each parking booking  and the fields are lot_id (foreign key) , spot_id (foreign key) , user_id ( foreign key) , vehicle_id ( foreign key) , parking_timestamp ( eg : 2025-07-22 16:30:45  )  and leaving_timestamp ( eg :2025-07-22 18:45:40)

👷 Application Architecture : 

MVC ( Model - View - Controller) is a software architecture used to separate concerns in web applications. It divides an application into three interconnected components


### Setup Instructions:
1. Clone the repository:
```bash
git https://github.com/23f2004163/parking_app_23f2004163.git
cd parking_app_23f2004163
 ```
2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # For Linux/MacOS
venv\Scripts\activate     # For Windows
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Run the application:
```bash
flask run
```


### Login:
- Admin: `http://127.0.0.1:8000/login`
    - Email: ```admin123@gmail.com```
    - Password: ```admin123```

- User: `http://127.0.0.1:5000/login`
    - Email: ```user1@gmail.com```
    - Password: ```user123```
