import hmac
import hashlib
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import qrcode
import io
import os

app = Flask(__name__)
# Use a more secure secret key, preferably from environment variables
app.secret_key = os.environ.get('SECRET_KEY', 'qtravix_secure_fallback_key_2026')

# Database Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'qtravix.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Security Helper: QR Signature
def generate_ticket_signature(data_str):
    """Generate a short HMAC signature to prevent QR forgery."""
    return hmac.new(app.secret_key.encode(), data_str.encode(), hashlib.sha256).hexdigest()[:10]

# Models
class Admin(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Conductor(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    admin_id = db.Column(db.String(50), db.ForeignKey('admin.id'), nullable=True) # Linked to Admin
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)

class RouteStop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bus_id = db.Column(db.String(50), db.ForeignKey('bus.id'), nullable=False)
    stop_name = db.Column(db.String(100), nullable=False)
    stop_order = db.Column(db.Integer, nullable=False)

class Bus(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    admin_id = db.Column(db.String(50), db.ForeignKey('admin.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    route_from = db.Column(db.String(100), nullable=False)
    route_to = db.Column(db.String(100), nullable=False)
    starting_time = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    base_fare = db.Column(db.Float, default=0.0)
    stops = db.Column(db.String(500)) # Kept for backward compatibility, but we use RouteStop now
    route_stops = db.relationship('RouteStop', backref='bus', lazy=True, cascade="all, delete-orphan")

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bus_id = db.Column(db.String(50), nullable=False)
    source = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    num_passengers = db.Column(db.Integer, nullable=False)
    fare = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_validated = db.Column(db.Boolean, default=False)
    validated_at = db.Column(db.DateTime)
    booked_by = db.Column(db.String(20), default='Passenger') # 'Passenger' or 'Conductor'

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/bus_details')
def bus_details():
    buses = Bus.query.all()
    return render_template('bus_details.html', buses=buses)

@app.route('/ticket_booking')
def ticket_booking():
    buses = Bus.query.all()
    return render_template('ticket_booking.html', buses=buses)

@app.route('/book_ticket_qr/<bus_id>')
def book_ticket_qr(bus_id):
    bus = Bus.query.get_or_404(bus_id)
    return render_template('booking_form.html', bus=bus)

@app.route('/book_ticket_qr/<bus_id>', methods=['POST'])
def book_ticket_post(bus_id):
    bus = Bus.query.get_or_404(bus_id)
    source = request.form.get('source')
    destination = request.form.get('destination')
    num_passengers = int(request.form.get('num_passengers', 1))
    fare = float(request.form.get('fare'))
    
    # Track who is booking the ticket
    booked_by = 'Conductor' if 'conductor_id' in session else 'Passenger'
    
    new_booking = Booking(
        bus_id=bus_id,
        source=source,
        destination=destination,
        num_passengers=num_passengers,
        fare=fare,
        date=bus.date,
        booked_by=booked_by
    )
    db.session.add(new_booking)
    db.session.commit()
    
    return redirect(url_for('payment', booking_id=new_booking.id))

@app.route('/payment/<int:booking_id>', methods=['GET', 'POST'])
def payment(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if request.method == 'POST':
        # Dummy payment success logic
        return redirect(url_for('ticket', booking_id=booking.id))
    
    bus = Bus.query.get(booking.bus_id)
    return render_template('payment.html', booking=booking, bus=bus)

@app.route('/ticket/<int:booking_id>')
def ticket(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    bus = Bus.query.get(booking.bus_id)
    
    # Secure Ticket Data with Signature
    raw_data = f"{booking.id}:{booking.bus_id}:{booking.fare}"
    signature = generate_ticket_signature(raw_data)
    ticket_data = f"TICKET:{raw_data}:{signature}"
    
    return render_template('ticket.html', booking=booking, bus=bus, ticket_data=ticket_data)

# Auth Routes
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin_id = request.form.get('admin_id')
        password = request.form.get('password')
        admin = Admin.query.get(admin_id)
        if admin and check_password_hash(admin.password, password):
            session.clear() # Clear existing session for security
            session['admin_id'] = admin.id
            flash('Login Successful!')
            return redirect(url_for('admin_dashboard'))
        flash('Invalid Credentials!')
    return render_template('login.html', user_type='Admin')

@app.route('/admin_register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        admin_id = request.form.get('admin_id')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if Admin.query.get(admin_id):
            flash('ID already exists!')
            return redirect(url_for('admin_register'))
            
        new_admin = Admin(id=admin_id, email=email, password=generate_password_hash(password))
        db.session.add(new_admin)
        db.session.commit()
        flash('Registration Successful!')
        return redirect(url_for('admin_login'))
    return render_template('register.html', user_type='Admin')

@app.route('/conductor_login', methods=['GET', 'POST'])
def conductor_login():
    if request.method == 'POST':
        conductor_id = request.form.get('conductor_id')
        password = request.form.get('password')
        conductor = Conductor.query.get(conductor_id)
        if conductor and check_password_hash(conductor.password, password):
            session.clear() # Clear existing session for security
            session['conductor_id'] = conductor.id
            flash('Login Successful!')
            return redirect(url_for('conductor_dashboard'))
        flash('Invalid Credentials!')
    return render_template('login.html', user_type='Conductor')

@app.route('/conductor_register', methods=['GET', 'POST'])
def conductor_register():
    if request.method == 'POST':
        conductor_id = request.form.get('conductor_id')
        admin_id = request.form.get('admin_id')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if Admin exists
        if not Admin.query.get(admin_id):
            flash('Invalid Admin ID! Registration failed.')
            return redirect(url_for('conductor_register'))
            
        if Conductor.query.get(conductor_id):
            flash('ID already exists!')
            return redirect(url_for('conductor_register'))
            
        new_conductor = Conductor(id=conductor_id, admin_id=admin_id, email=email, password=generate_password_hash(password))
        db.session.add(new_conductor)
        db.session.commit()
        flash('Registration Successful!')
        return redirect(url_for('conductor_login'))
    return render_template('register.html', user_type='Conductor')

# Dashboard Routes
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    buses = Bus.query.filter_by(admin_id=session['admin_id']).all()
    return render_template('admin_dashboard.html', buses=buses)

@app.route('/add_bus', methods=['POST'])
def add_bus():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    bus_id = request.form.get('bus_id')
    bus_name = request.form.get('bus_name')
    route_from = request.form.get('route_from')
    route_to = request.form.get('route_to')
    starting_time = request.form.get('starting_time')
    date = request.form.get('date')
    base_fare = float(request.form.get('base_fare'))
    stops = request.form.get('stops', '')
    
    new_bus = Bus(id=bus_id, admin_id=session['admin_id'], name=bus_name, route_from=route_from, route_to=route_to, 
                  starting_time=starting_time, date=date, base_fare=base_fare, stops=stops)
    db.session.add(new_bus)
    db.session.commit()
    flash('Bus Added Successfully!')
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_bus/<bus_id>', methods=['POST'])
def delete_bus(bus_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    bus = Bus.query.filter_by(id=bus_id, admin_id=session['admin_id']).first_or_404()
    db.session.delete(bus)
    db.session.commit()
    flash('Bus Deleted!')
    return redirect(url_for('admin_dashboard'))

@app.route('/revenue')
def revenue():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    admin_bus_ids = [bus.id for bus in Bus.query.filter_by(admin_id=session['admin_id']).all()]
    
    selected_date = request.args.get('date')
    selected_month = request.args.get('month')
    view_mode = 'daily'

    query = Booking.query.filter(Booking.bus_id.in_(admin_bus_ids) if admin_bus_ids else Booking.bus_id == 'NONE')

    if selected_month:
        view_mode = 'monthly'
        bookings = query.filter(db.func.strftime('%Y-%m', Booking.timestamp) == selected_month).all()
        display_label = datetime.strptime(selected_month, '%Y-%m').strftime('%B %Y')
        selected_date = datetime.now().strftime('%Y-%m-%d')
    else:
        if not selected_date:
            selected_date = datetime.now().strftime('%Y-%m-%d')
        view_mode = 'daily'
        bookings = query.filter(db.func.date(Booking.timestamp) == selected_date).all()
        display_label = datetime.strptime(selected_date, '%Y-%m-%d').strftime('%d %b %Y')
        current_month = datetime.strptime(selected_date, '%Y-%m-%d').strftime('%Y-%m')
        selected_month = current_month

    # Calculate separated revenue and passenger counts
    passenger_bookings = [b for b in bookings if b.booked_by == 'Passenger']
    conductor_bookings = [b for b in bookings if b.booked_by == 'Conductor']
    
    passenger_revenue = sum(b.fare for b in passenger_bookings)
    conductor_revenue = sum(b.fare for b in conductor_bookings)
    total_revenue = passenger_revenue + conductor_revenue

    # Sum of passengers
    passenger_pax_total = sum(b.num_passengers for b in passenger_bookings)
    conductor_pax_total = sum(b.num_passengers for b in conductor_bookings)
    total_pax_count = passenger_pax_total + conductor_pax_total

    # Monthly total for summary
    monthly_total_bookings = query.filter(db.func.strftime('%Y-%m', Booking.timestamp) == selected_month).all()
    monthly_total_revenue = sum(b.fare for b in monthly_total_bookings)
    
    return render_template('revenue.html', 
                         bookings=bookings, 
                         total_revenue=total_revenue,
                         passenger_revenue=passenger_revenue,
                         conductor_revenue=conductor_revenue,
                         passenger_count=len(passenger_bookings),
                         conductor_count=len(conductor_bookings),
                         passenger_pax_total=passenger_pax_total,
                         conductor_pax_total=conductor_pax_total,
                         total_pax_count=total_pax_count,
                         monthly_total_revenue=monthly_total_revenue,
                         selected_date=selected_date,
                         selected_month=selected_month,
                         view_mode=view_mode,
                         display_label=display_label)

@app.route('/conductor_dashboard')
def conductor_dashboard():
    if 'conductor_id' not in session:
        return redirect(url_for('conductor_login'))
    return render_template('conductor_dashboard.html')

@app.route('/validate_ticket', methods=['POST'])
def validate_ticket():
    data = request.json
    ticket_data = data.get('ticket_data', '')
    
    if not ticket_data.startswith('TICKET:'):
        return jsonify({'status': 'error', 'message': 'Invalid QR Format'})
        
    parts = ticket_data.split(':')
    # New format: TICKET:id:bus_id:fare:signature (len 5)
    if len(parts) < 5:
        return jsonify({'status': 'error', 'message': 'Legacy or Incomplete Ticket'})
        
    booking_id = parts[1]
    bus_id = parts[2]
    fare = parts[3]
    signature_received = parts[4]
    
    # Verify Signature
    expected_raw = f"{booking_id}:{bus_id}:{fare}"
    if generate_ticket_signature(expected_raw) != signature_received:
        return jsonify({'status': 'error', 'message': 'Security Alert: Forged Ticket!'})

    # NEW: Ensure Conductor belongs to the same Admin as the Bus
    conductor = Conductor.query.get(session.get('conductor_id'))
    bus = Bus.query.get(bus_id)
    if not conductor or not bus or bus.admin_id != conductor.admin_id:
        return jsonify({'status': 'error', 'message': 'Access Denied: Not your Admin\'s bus'})

    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'status': 'error', 'message': 'Ticket Not Found'})
        
    if booking.is_validated:
        return jsonify({
            'status': 'warning', 
            'details': f"Already used at {booking.validated_at.strftime('%H:%M:%S')}"
        })
        
    booking.is_validated = True
    booking.validated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'details': f"Ticket ID #{booking.id} - {booking.num_passengers} Pass. - ₹{booking.fare}"
    })

@app.route('/generate_qr/<bus_id>')
def generate_qr(bus_id):
    bus = Bus.query.get_or_404(bus_id)
    download = request.args.get('download', 'false').lower() == 'true'
    booking_url = url_for('book_ticket_qr', bus_id=bus_id, _external=True)
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(booking_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    if download:
        return send_file(img_io, mimetype='image/png', as_attachment=True, download_name=f'QR_{bus_id}.png')
    return send_file(img_io, mimetype='image/png')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged Out!')
    return redirect(url_for('index'))

@app.route('/api/buses')
def api_buses():
    if 'conductor_id' not in session:
        return jsonify([])
    
    conductor = Conductor.query.get(session['conductor_id'])
    if not conductor:
        return jsonify([])
        
    buses = Bus.query.filter_by(admin_id=conductor.admin_id).all()
    return jsonify([{
        'id': bus.id,
        'name': bus.name,
        'route_from': bus.route_from,
        'route_to': bus.route_to,
        'starting_time': bus.starting_time,
        'date': bus.date,
        'base_fare': bus.base_fare
    } for bus in buses])

import socket
from sqlalchemy import text

# Create instance directory if it doesn't exist
os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)

def repair_db():
    """Ensure database schema is up-to-date with all required columns."""
    try:
        with app.app_context():
            with db.engine.connect() as conn:
                columns_booking = [row[1] for row in conn.execute(text("PRAGMA table_info(booking)")).fetchall()]
                
                if 'is_validated' not in columns_booking:
                    conn.execute(text("ALTER TABLE booking ADD COLUMN is_validated BOOLEAN DEFAULT 0"))
                if 'validated_at' not in columns_booking:
                    conn.execute(text("ALTER TABLE booking ADD COLUMN validated_at DATETIME"))
                if 'booked_by' not in columns_booking:
                    print("Adding 'booked_by' column...")
                    conn.execute(text("ALTER TABLE booking ADD COLUMN booked_by VARCHAR(20) DEFAULT 'Passenger'"))
                
                columns_bus = [row[1] for row in conn.execute(text("PRAGMA table_info(bus)")).fetchall()]
                if 'admin_id' not in columns_bus:
                    conn.execute(text("ALTER TABLE bus ADD COLUMN admin_id VARCHAR(50)"))
                
                columns_conductor = [row[1] for row in conn.execute(text("PRAGMA table_info(conductor)")).fetchall()]
                if 'admin_id' not in columns_conductor:
                    print("Adding 'admin_id' column to conductor table...")
                    conn.execute(text("ALTER TABLE conductor ADD COLUMN admin_id VARCHAR(50)"))
                
                conn.commit()
            print("Database schema verified.")
    except Exception as e:
        print(f"Database repair skipped: {e}")

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def auto_populate():
    """Populate database with sample data if it's empty."""
    with app.app_context():
        if Bus.query.first() is None:
            today = datetime.now().strftime('%Y-%m-%d')
            # Using slightly better passwords for sample data
            admin = Admin(id="admin01", email="admin@qtravix.com", password=generate_password_hash("admin@qtravix"))
            conductor = Conductor(id="cond01", admin_id="admin01", email="cond@qtravix.com", password=generate_password_hash("cond@qtravix"))
            db.session.add(admin)
            db.session.add(conductor)
            
            sample_buses = [
                Bus(id="B001", admin_id="admin01", name="Malabar Express", route_from="Payyanur", route_to="Kannur", 
                    starting_time="08:30", date=today, base_fare=10.0, stops="Payyanur, Pilathara, Pazhayangadi, Cherukunnu, Pappinisseri, Kannur"),
                Bus(id="B002", admin_id="admin01", name="Coastal Flyer", route_from="Kasaragod", route_to="Payyanur", 
                    starting_time="09:15", date=today, base_fare=12.0, stops="Kasaragod, Kanhangad, Nileshwar, Cheruvathur, Payyanur"),
                Bus(id="B003", admin_id="admin01", name="City Shuttle", route_from="Kannur", route_to="Thalassery", 
                    starting_time="10:00", date=today, base_fare=8.0, stops="Kannur, Thottada, Edakkad, Dharmadam, Thalassery")
            ]
            db.session.add_all(sample_buses)
            db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    repair_db()
    auto_populate()
    
    local_ip = get_local_ip()
    print(f"\n🚀 QTravix SECURE SERVER RUNNING")
    print(f"💻 DESKTOP: https://localhost:5000")
    print(f"📱 MOBILE:  https://{local_ip}:5000\n")
    
    # Keep debug=True for your development, but in a real production environment, this should be False.
    # We keep 'adhoc' SSL for camera support on mobile devices.
    app.run(host='0.0.0.0', port=5000, debug=True, ssl_context='adhoc')
