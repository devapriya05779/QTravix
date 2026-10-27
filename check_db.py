from app import app, db, Conductor, Bus, Admin

with app.app_context():
    print("--- Conductors ---")
    conductors = Conductor.query.all()
    for c in conductors:
        print(f"ID: {c.id}, Admin ID: {c.admin_id}, Email: {c.email}")
    
    print("\n--- Buses ---")
    buses = Bus.query.all()
    for b in buses:
        print(f"ID: {b.id}, Admin ID: {b.admin_id}, Name: {b.name}")

    print("\n--- Admins ---")
    admins = Admin.query.all()
    for a in admins:
        print(f"ID: {a.id}, Email: {a.email}")
