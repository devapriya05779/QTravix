from app import app, db, Admin, Conductor, Bus, Booking
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

def populate():
    with app.app_context():
        # Clear existing data to avoid duplicates
        db.drop_all()
        db.create_all()

        # 1. Create Admin
        admin = Admin(id="admin01", email="admin@qtravix.com", password=generate_password_hash("admin123"))
        db.session.add(admin)

        # 2. Create Conductor
        conductor = Conductor(id="cond01", email="cond@qtravix.com", password=generate_password_hash("cond123"))
        db.session.add(conductor)

        # 3. Create Sample Buses with Intermediate Stops
        today = datetime.now().strftime('%Y-%m-%d')
        
        buses = [
            Bus(
                id="B001", 
                name="Malabar Express", 
                route_from="Payyanur", 
                route_to="Kannur", 
                starting_time="08:30", 
                date=today, 
                base_fare=10.0,
                stops="Payyanur, Pilathara, Pazhayangadi, Cherukunnu, Pappinisseri, Kannur"
            ),
            Bus(
                id="B002", 
                name="Coastal Flyer", 
                route_from="Kasaragod", 
                route_to="Payyanur", 
                starting_time="09:15", 
                date=today, 
                base_fare=12.0,
                stops="Kasaragod, Kanhangad, Nileshwar, Cheruvathur, Payyanur"
            ),
            Bus(
                id="B003", 
                name="City Shuttle", 
                route_from="Kannur", 
                route_to="Thalassery", 
                starting_time="10:00", 
                date=today, 
                base_fare=8.0,
                stops="Kannur, Thottada, Edakkad, Dharmadam, Thalassery"
            ),
            Bus(
                id="B004", 
                name="Hill Queen", 
                route_from="Taliparamba", 
                route_to="Iritty", 
                starting_time="07:45", 
                date=today, 
                base_fare=15.0,
                stops="Taliparamba, Sreekandapuram, Irikkur, Mattannur, Iritty"
            ),
            Bus(
                id="B005", 
                name="Wayfarer", 
                route_from="Kozhikode", 
                route_to="Wayanad", 
                starting_time="06:30", 
                date=today, 
                base_fare=20.0,
                stops="Kozhikode, Kunnamangalam, Thamarassery, Adivaram, Lakkidi, Vythiri, Kalpetta"
            ),
            Bus(
                id="B006", 
                name="Town Connect", 
                route_from="Payyanur", 
                route_to="Taliparamba", 
                starting_time="11:30", 
                date=today, 
                base_fare=10.0,
                stops="Payyanur, Karivellur, Vellur, Pariyaram, Taliparamba"
            )
        ]

        db.session.add_all(buses)

        # 4. Create some sample bookings
        new_booking = Booking(
            bus_id="B001",
            source="Payyanur",
            destination="Kannur",
            num_passengers=2,
            fare=100.0, # 5 stages * 10 * 2
            date=today,
            is_validated=False
        )
        db.session.add(new_booking)

        db.session.commit()
        print(f"Database populated with {len(buses)} buses and intermediate stops!")

if __name__ == "__main__":
    populate()
