from app import app, db, Conductor

with app.app_context():
    # Link cond01 to admin01
    c1 = Conductor.query.get('cond01')
    if c1:
        c1.admin_id = 'admin01'
        print("Updated cond01 with admin01")
    
    # Link ab to admin01 (as an example, or whatever admin created the buses)
    c2 = Conductor.query.get('ab')
    if c2:
        c2.admin_id = 'admin01'
        print("Updated ab with admin01")

    db.session.commit()
    print("Database updated.")
