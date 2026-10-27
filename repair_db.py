from app import app, db
from sqlalchemy import text

def repair_db():
    with app.app_context():
        # Check if columns exist in Booking table
        with db.engine.connect() as conn:
            # Repair Booking table
            columns_booking = [row[1] for row in conn.execute(text("PRAGMA table_info(booking)")).fetchall()]
            
            if 'is_validated' not in columns_booking:
                print("Adding column is_validated to booking table...")
                conn.execute(text("ALTER TABLE booking ADD COLUMN is_validated BOOLEAN DEFAULT 0"))
                conn.commit()
            
            if 'validated_at' not in columns_booking:
                print("Adding column validated_at to booking table...")
                conn.execute(text("ALTER TABLE booking ADD COLUMN validated_at DATETIME"))
                conn.commit()

            # Repair Bus table
            columns_bus = [row[1] for row in conn.execute(text("PRAGMA table_info(bus)")).fetchall()]
            if 'admin_id' not in columns_bus:
                print("Adding column admin_id to bus table...")
                conn.execute(text("ALTER TABLE bus ADD COLUMN admin_id VARCHAR(50)"))
                conn.commit()
                
        print("Database repair complete!")

if __name__ == "__main__":
    repair_db()
