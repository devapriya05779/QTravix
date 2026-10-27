from app import app, db, Bus
from sqlalchemy import text
import os

# Define the new model locally for migration purposes
class RouteStop(db.Model):
    __tablename__ = 'route_stop'
    id = db.Column(db.Integer, primary_key=True)
    bus_id = db.Column(db.String(50), db.ForeignKey('bus.id'), nullable=False)
    stop_name = db.Column(db.String(100), nullable=False)
    stop_order = db.Column(db.Integer, nullable=False)

def migrate():
    with app.app_context():
        # 1. Create the new table
        print("Creating route_stop table...")
        db.create_all()

        # 2. Get all buses with their stops
        buses = Bus.query.all()
        
        # 3. Migrate data
        print(f"Migrating stops for {len(buses)} buses...")
        for bus in buses:
            if bus.stops:
                # Handle cases with leading/trailing commas or spaces
                stop_list = [s.strip() for s in bus.stops.split(',') if s.strip()]
                
                # Clear any existing stops for this bus in route_stop (just in case)
                RouteStop.query.filter_by(bus_id=bus.id).delete()
                
                for index, stop_name in enumerate(stop_list):
                    new_stop = RouteStop(
                        bus_id=bus.id,
                        stop_name=stop_name,
                        stop_order=index
                    )
                    db.session.add(new_stop)
        
        db.session.commit()
        print("Data migration to route_stop table successful!")

        # 4. (Optional but recommended for normalization) 
        # We should ideally remove the 'stops' column from 'bus' table.
        # SQLite doesn't support DROP COLUMN easily in older versions, 
        # but SQLAlchemy/Alembic or a manual process can do it.
        # For now, we'll keep it but the app will use the new table.

if __name__ == "__main__":
    migrate()
