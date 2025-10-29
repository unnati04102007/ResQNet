from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session, send_from_directory
import json
from flask_babel import Babel, gettext as _
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime, timedelta
import random
import string
import requests
import threading
import time

from dotenv import load_dotenv
import stripe

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.secret_key = 'your-secret-key-here'  # Change this in production
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_DEFAULT_TIMEZONE'] = 'UTC'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'

# i18n / l10n configuration
LANGUAGES = ['en', 'hi']
babel = Babel()

def get_locale():
    # Preferred language comes from session only; no DB dependency
    lang = session.get('language')
    if lang in LANGUAGES:
        return lang
    return 'en'

# Initialize Babel with locale selector (Flask-Babel 4 style)
babel.init_app(app, locale_selector=get_locale)

@app.context_processor
def inject_globals():
    return {
        'AVAILABLE_LANGUAGES': LANGUAGES,
        'CURRENT_LANGUAGE': session.get('language', 'en'),
    }

# Database setup
DATABASE = 'donations.db'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def _column_exists(cursor, table_name: str, column_name: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table_name})")
    return any(row[1] == column_name for row in cursor.fetchall())

def init_db():
    """Initialize the SQLite database and create/migrate tables"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Create users table (uses 'name' per spec)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # If legacy 'username' exists but 'name' missing, add 'name'
    if not _column_exists(cursor, 'users', 'name'):
        cursor.execute("ALTER TABLE users ADD COLUMN name TEXT")
    # Note: language preference is no longer stored in DB
    # If legacy preferred_language exists, migrate table to drop it
    cursor.execute("PRAGMA table_info(users)")
    cols_info = cursor.fetchall()
    has_pref_lang = any(row[1] == 'preferred_language' for row in cols_info)
    if has_pref_lang:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            INSERT OR IGNORE INTO users_new (id, name, email, password_hash, created_at)
            SELECT id, name, email, password_hash, created_at FROM users
        ''')
        cursor.execute('ALTER TABLE users RENAME TO users_old')
        cursor.execute('ALTER TABLE users_new RENAME TO users')
        cursor.execute('DROP TABLE users_old')

    # Create reports table (uses 'name' per spec)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT,
            email TEXT NOT NULL,
            location TEXT NOT NULL,
            disaster_type TEXT NOT NULL,
            description TEXT NOT NULL,
            image_path TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # If legacy 'user_name' column exists, ensure 'name' exists too
    if not _column_exists(cursor, 'reports', 'name'):
        cursor.execute("ALTER TABLE reports ADD COLUMN name TEXT")

    # Create donations table (existing)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donor_name TEXT NOT NULL,
            donor_email TEXT NOT NULL,
            amount REAL NOT NULL CHECK (amount > 0),
            currency TEXT NOT NULL DEFAULT 'USD',
            purpose TEXT,
            pay_via TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Migrate donations schema: add payment_method, payment_reference, status, timestamp
    if not _column_exists(cursor, 'donations', 'payment_method'):
        cursor.execute("ALTER TABLE donations ADD COLUMN payment_method TEXT")
    if not _column_exists(cursor, 'donations', 'payment_reference'):
        cursor.execute("ALTER TABLE donations ADD COLUMN payment_reference TEXT")
    if not _column_exists(cursor, 'donations', 'status'):
        cursor.execute("ALTER TABLE donations ADD COLUMN status TEXT")
    # We already have created_at; avoid adding a new timestamp column to prevent SQLite default issues

    # Create contact_messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            enquiry_type TEXT,
            segment TEXT,
            name TEXT,
            email TEXT,
            mobile TEXT,
            city TEXT,
            description TEXT,
            time_slot TEXT,
            captcha_entered TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create weather_data table for disaster prediction system
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL,
            wind_speed REAL NOT NULL,
            rainfall REAL NOT NULL,
            risk_type TEXT,
            risk_level TEXT,
            alert_message TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create user_preferences table to store city preferences
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            last_city TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.commit()
    conn.close()

@app.route('/')
def home():
    """Serve the Home page"""
    return render_template('home.html')

@app.route('/donation')
def donation():
    return render_template('donation.html')

# Authentication routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        email = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        confirm_password = request.form.get('confirm_password','')
        # Language preference removed from registration

        if not name or not email or not password:
            flash('Please fill all required fields.', 'error')
            return render_template('register.html')
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')

        password_hash = generate_password_hash(password)

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        # Check email uniqueness explicitly
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        existing = cursor.fetchone()
        if existing:
            conn.close()
            flash('Email already registered.', 'error')
            return render_template('register.html')

        # Insert user (support legacy 'username' NOT NULL schema by populating it)
        cursor.execute('PRAGMA table_info(users)')
        cols = [row[1] for row in cursor.fetchall()]  # column names
        if 'username' in cols:
            cursor.execute('''
                INSERT INTO users (name, username, email, password_hash)
                VALUES (?, ?, ?, ?)
            ''', (name, name, email, password_hash))
        else:
            cursor.execute('''
                INSERT INTO users (name, email, password_hash)
                VALUES (?, ?, ?)
            ''', (name, email, password_hash))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()

        # Post-registration: go to login
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    next_url = request.args.get('next') or request.form.get('next') or ''
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, password_hash FROM users WHERE email = ?
        ''', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['name'] = user[1] or ''
            flash('Login successful!', 'success')
            # Redirect to next if provided and safe (same-site path)
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect(url_for('report', openModal=1))
        else:
            flash('Invalid email or password!', 'error')
    
    return render_template('login.html', next_url=next_url)

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/change-language/<lang_code>')
def change_language(lang_code: str):
    if lang_code in LANGUAGES:
        session['language'] = lang_code
    return redirect(request.referrer or url_for('home'))

# Report routes
@app.route('/report', methods=['GET', 'POST'])
def report():
    """Report page - show form and recent incidents"""
    # Enforce login for both GET and POST
    if 'user_id' not in session:
        flash('Please login to access the report page.', 'error')
        # After login, return to report page and auto-open modal
        return redirect(url_for('login', next=url_for('report', openModal=1)))

    if request.method == 'POST':
        # Check if user is logged in
        # Already enforced above
        
        # Get form data
        name = request.form.get('name', '')
        email = request.form['email']
        location = request.form['location']
        disaster_type = request.form['disaster_type']
        description = request.form['description']
        
        # Handle file upload
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to avoid filename conflicts
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                image_path = filename
        
        # Save report to database
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO reports (user_id, name, email, location, disaster_type, description, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (session['user_id'], name, email, location, disaster_type, description, image_path))
        conn.commit()
        conn.close()
        
        flash('Report submitted successfully!', 'success')
        return redirect(url_for('report'))
    
    # Pass flag to auto-open modal
    open_modal = request.args.get('openModal') == '1' or request.args.get('openModal') == 'true'
    return render_template('report.html', open_modal=open_modal)

@app.route('/api/reports')
def api_reports():
    """API endpoint to get recent reports with filters"""
    disaster_type = request.args.get('disaster_type', '')
    location_filter = request.args.get('location', '')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    query = '''
        SELECT r.id, r.name, r.email, r.location, r.disaster_type, 
               r.description, r.image_path, r.status, r.created_at
        FROM reports r
        WHERE 1=1
    '''
    params = []
    
    if disaster_type:
        query += ' AND r.disaster_type = ?'
        params.append(disaster_type)
    
    if location_filter:
        query += ' AND r.location LIKE ?'
        params.append(f'%{location_filter}%')
    
    query += ' ORDER BY r.created_at DESC LIMIT 20'
    
    cursor.execute(query, params)
    reports = []
    for row in cursor.fetchall():
        reports.append({
            'id': row[0],
            'name': row[1] or 'Anonymous',
            'email': row[2],
            'location': row[3],
            'disaster_type': row[4],
            'description': row[5],
            'image_path': row[6],
            'status': row[7],
            'created_at': row[8]
        })
    
    conn.close()
    return jsonify({'reports': reports})

@app.route('/get_alerts')
def get_alerts():
    """API endpoint to get latest 5 reports for emergency alert bar"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    query = '''
        SELECT r.name, r.location, r.disaster_type, r.created_at
        FROM reports r
        ORDER BY r.created_at DESC 
        LIMIT 5
    '''
    
    cursor.execute(query)
    reports = []
    for row in cursor.fetchall():
        reports.append({
            'name': row[0] or 'Anonymous',
            'location': row[1],
            'disaster_type': row[2],
            'created_at': row[3]
        })
    
    conn.close()
    return jsonify({'alerts': reports})

@app.route('/get_weather_alerts')
def get_weather_alerts():
    """API endpoint to get weather alerts for emergency alert bar (supports city filtering)"""
    try:
        city = request.args.get('city', '').strip()
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Get the most recent weather alert for the specified city or overall
        if city:
            cursor.execute('''
                SELECT alert_message, risk_type, risk_level, timestamp, city
                FROM weather_data
                WHERE city = ?
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (city,))
        else:
            cursor.execute('''
                SELECT alert_message, risk_type, risk_level, timestamp, city
                FROM weather_data
                ORDER BY timestamp DESC
                LIMIT 1
            ''')
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return jsonify({
                'success': True,
                'weather_alert': {
                    'message': result[0],
                    'risk_type': result[1],
                    'risk_level': result[2],
                    'timestamp': result[3],
                    'city': result[4]
                }
            })
        else:
            city_msg = f' for {city}' if city else ''
            return jsonify({
                'success': True,
                'weather_alert': {
                    'message': f'✅ Weather monitoring system initializing{city_msg}...',
                    'risk_type': 'none',
                    'risk_level': 'low',
                    'timestamp': datetime.now().isoformat(),
                    'city': city
                }
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Unable to fetch weather alert: {str(e)}'
        }), 500

# Serve uploaded files
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# Contact Us routes and captcha utilities
def _generate_captcha_code(length: int = 7) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(random.choice(alphabet) for _ in range(length))

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Validate captcha
        expected = session.get('captcha_code')
        entered = request.form.get('captcha_input', '').strip().upper()
        if not expected or entered != expected:
            flash('Invalid captcha. Please try again.', 'error')
            return redirect(url_for('contact'))

        # Collect form data
        enquiry_type = request.form.get('enquiry_type', '')
        segment = request.form.get('segment', '')
        name = request.form.get('name', '')
        email = request.form.get('email', '')
        mobile = request.form.get('mobile', '')
        city = request.form.get('city', '')
        description = request.form.get('description', '')
        time_slot = request.form.get('time_slot', '')

        # Persist to DB
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO contact_messages (
                enquiry_type, segment, name, email, mobile, city, description, time_slot, captcha_entered
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (enquiry_type, segment, name, email, mobile, city, description, time_slot, entered))
        conn.commit()
        conn.close()

        flash('Thank you for reaching out! Our team will get back to you soon.', 'success')
        # regenerate captcha for the next visit
        session['captcha_code'] = _generate_captcha_code()
        return redirect(url_for('contact'))

    # GET: generate captcha
    session['captcha_code'] = _generate_captcha_code()
    return render_template('contact.html', captcha_code=session['captcha_code'])

# Safe Route page
@app.route('/safe-route')
def safe_route():
    return render_template('safe_route.html')

@app.route('/get-shelters')
def get_shelters():
    """Serve shelters list from local JSON file"""
    try:
        with open('shelters.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Basic validation/normalization
        items = []
        for item in data:
            try:
                name = str(item.get('name', '')).strip()
                lat = float(item.get('lat'))
                lon = float(item.get('lon'))
                items.append({ 'name': name, 'lat': lat, 'lon': lon })
            except Exception:
                continue
        return jsonify({ 'shelters': items })
    except FileNotFoundError:
        return jsonify({ 'shelters': [] })

# ---- Stripe configuration and Checkout routes ----

# Load environment variables for Stripe keys
load_dotenv()
STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY', '')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

def _inr_smallest_unit(amount: float, currency: str) -> int:
    # Stripe expects the amount in the smallest currency unit
    # For zero-decimal currencies this would be different, but for INR/USD/EUR/GBP it's cents/paise
    return int(round(float(amount) * 100))

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    """Create Stripe Checkout Session from donation form."""
    try:
        data = request.get_json(force=True, silent=False) or {}
        donor_name = (data.get('donor_name') or '').strip()
        donor_email = (data.get('donor_email') or '').strip()
        purpose = (data.get('purpose') or '').strip()
        currency = (data.get('currency') or 'USD').upper()
        pay_via = (data.get('pay_via') or 'Other').strip()
        amount = float(data.get('amount') or 0)

        if not donor_name or not donor_email or amount <= 0:
            return jsonify({'error': 'Invalid donation data'}), 400

        if not STRIPE_SECRET_KEY:
            return jsonify({'error': 'Stripe is not configured on the server'}), 500

        amount_smallest = _inr_smallest_unit(amount, currency)

        success_url = url_for('success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}'
        cancel_url = url_for('cancel', _external=True)

        # Create Checkout Session
        session_obj = stripe.checkout.Session.create(
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=donor_email,
            line_items=[{
                'price_data': {
                    'currency': currency.lower(),
                    'product_data': {
                        'name': 'ResQNet Donation',
                        'description': purpose or 'Support ResQNet operations'
                    },
                    'unit_amount': amount_smallest,
                },
                'quantity': 1,
            }],
            metadata={
                'donor_name': donor_name,
                'donor_email': donor_email,
                'purpose': purpose,
                'pay_via': pay_via,
                'currency': currency,
                'amount': str(amount)
            }
        )

        # Save minimal details in Flask session for cancel handling
        session['last_checkout'] = {
            'donor_name': donor_name,
            'donor_email': donor_email,
            'purpose': purpose,
            'pay_via': pay_via,
            'currency': currency,
            'amount': amount,
            'payment_reference': session_obj.id,
        }

        return jsonify({'id': session_obj.id, 'url': session_obj.url})
    except Exception as e:
        return jsonify({'error': f'Checkout error: {str(e)}'}), 500

@app.route('/success')
def success():
    """Payment success page; persist donation with status Succeeded."""
    session_id = request.args.get('session_id', '')
    if not session_id or not STRIPE_SECRET_KEY:
        flash('Missing payment session.', 'error')
        return redirect(url_for('donation'))

    try:
        checkout_session = stripe.checkout.Session.retrieve(session_id, expand=['payment_intent'])
        metadata = checkout_session.get('metadata', {})
        payment_intent = checkout_session.get('payment_intent')
        payment_reference = session_id
        status = 'Succeeded'

        donor_name = metadata.get('donor_name', '')
        donor_email = metadata.get('donor_email', '')
        purpose = metadata.get('purpose', '')
        pay_via = metadata.get('pay_via', 'Other')
        currency = (metadata.get('currency') or 'USD').upper()
        try:
            amount = float(metadata.get('amount'))
        except Exception:
            amount = 0.0

        # Insert donation record with success
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO donations (donor_name, donor_email, amount, currency, purpose, pay_via, payment_method, payment_reference, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            donor_name,
            donor_email,
            amount,
            currency,
            purpose,
            pay_via,
            'Stripe Checkout',
            payment_reference,
            status
        ))
        conn.commit()
        conn.close()

        # Clear saved checkout draft
        session.pop('last_checkout', None)

        # Show thank-you page
        return render_template('success.html',
                               donor_name=donor_name,
                               amount=amount,
                               currency=currency,
                               payment_reference=payment_reference)
    except Exception as e:
        flash(f'Unable to verify payment: {str(e)}', 'error')
        return redirect(url_for('donation'))

@app.route('/cancel')
def cancel():
    """User cancelled payment; record cancellation and redirect back with message."""
    draft = session.pop('last_checkout', None)
    if draft:
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO donations (donor_name, donor_email, amount, currency, purpose, pay_via, payment_method, payment_reference, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                draft.get('donor_name',''),
                draft.get('donor_email',''),
                float(draft.get('amount') or 0),
                (draft.get('currency') or 'USD').upper(),
                draft.get('purpose',''),
                draft.get('pay_via','Other'),
                'Stripe Checkout',
                draft.get('payment_reference',''),
                'Cancelled'
            ))
            conn.commit()
            conn.close()
        except Exception:
            pass
    flash('Payment Cancelled', 'error')
    return redirect(url_for('donation'))

@app.route('/api/donate', methods=['POST'])
def donate():
    """Handle donation submission"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['donor_name', 'donor_email', 'amount', 'pay_via']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate amount
        try:
            amount = float(data['amount'])
            if amount <= 0:
                return jsonify({'error': 'Amount must be greater than 0'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid amount format'}), 400
        
        # Insert into database
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO donations (donor_name, donor_email, amount, currency, purpose, pay_via)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data['donor_name'],
            data['donor_email'],
            amount,
            data.get('currency', 'USD'),
            data.get('purpose', ''),
            data['pay_via']
        ))
        
        donation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Donation submitted successfully',
            'donation_id': donation_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/get-donations', methods=['GET'])
def get_donations():
    """Retrieve all donations"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, donor_name, donor_email, amount, currency, purpose, pay_via, created_at
            FROM donations
            ORDER BY created_at DESC
        ''')
        
        donations = []
        for row in cursor.fetchall():
            donations.append({
                'id': row[0],
                'donor_name': row[1],
                'donor_email': row[2],
                'amount': row[3],
                'currency': row[4],
                'purpose': row[5],
                'pay_via': row[6],
                'created_at': row[7]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'donations': donations,
            'count': len(donations)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/fetch-city-weather', methods=['POST'])
def fetch_city_weather():
    """Fetch and store weather data for a specific city"""
    try:
        data = request.get_json()
        city = data.get('city', '').strip()
        latitude = float(data.get('latitude', 0))
        longitude = float(data.get('longitude', 0))
        
        if not city or not latitude or not longitude:
            return jsonify({'success': False, 'error': 'Invalid city data'}), 400
        
        # Fetch weather data from NASA API
        weather_data = fetch_nasa_weather_data_for_coords(latitude, longitude)
        
        if weather_data.get('success'):
            # Predict disaster risk
            prediction = predict_disaster_risk(
                weather_data['temperature'],
                weather_data['humidity'],
                weather_data['wind_speed'],
                weather_data['rainfall'],
                city
            )
            
            # Store in database
            store_weather_data(
                city=city,
                latitude=latitude,
                longitude=longitude,
                temperature=weather_data['temperature'],
                humidity=weather_data['humidity'],
                wind_speed=weather_data['wind_speed'],
                rainfall=weather_data['rainfall'],
                risk_type=prediction['risk_type'],
                risk_level=prediction['risk_level'],
                alert_message=prediction['alert_message']
            )
            
            return jsonify({
                'success': True,
                'weather': {
                    'city': city,
                    'temperature': weather_data['temperature'],
                    'humidity': weather_data['humidity'],
                    'wind_speed': weather_data['wind_speed'],
                    'rainfall': weather_data['rainfall'],
                    'risk_type': prediction['risk_type'],
                    'risk_level': prediction['risk_level'],
                    'alert_message': prediction['alert_message']
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': weather_data.get('error', 'Failed to fetch weather data')
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error fetching city weather: {str(e)}'
        }), 500

@app.route('/api/user-preferences', methods=['GET'])
def get_user_preferences():
    """Get user preferences including last selected city"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Not logged in'}), 401
        
        user_id = session['user_id']
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT last_city, updated_at
            FROM user_preferences
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return jsonify({
                'success': True,
                'preferences': {
                    'last_city': result[0],
                    'updated_at': result[1]
                }
            })
        else:
            return jsonify({
                'success': True,
                'preferences': {}
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error fetching preferences: {str(e)}'
        }), 500

@app.route('/api/save-city-preference', methods=['POST'])
def save_city_preference():
    """Save user's last selected city"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Not logged in'}), 401
        
        user_id = session['user_id']
        data = request.get_json()
        city = data.get('city', '').strip()
        
        if not city:
            return jsonify({'success': False, 'error': 'Invalid city'}), 400
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Insert or update preference
        cursor.execute('''
            INSERT INTO user_preferences (user_id, last_city, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                last_city = excluded.last_city,
                updated_at = CURRENT_TIMESTAMP
        ''', (user_id, city))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'City preference saved'})
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error saving preference: {str(e)}'
        }), 500

# Disaster Prediction System Functions
def fetch_nasa_weather_data_for_coords(latitude, longitude):
    """Fetch weather data from NASA POWER API for specific coordinates"""
    try:
        # Get current date and previous day for more recent data
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        
        start_date = yesterday.strftime('%Y%m%d')
        end_date = today.strftime('%Y%m%d')
        
        # NASA POWER API endpoint with custom coordinates
        url = "https://power.larc.nasa.gov/api/temporal/hourly/point"
        params = {
            'start': start_date,
            'end': end_date,
            'latitude': latitude,
            'longitude': longitude,
            'community': 're',
            'parameters': 'T2M,PRECTOTCORR,WS2M,RH2M',
            'format': 'json',
            'units': 'metric',
            'user': 'resqnet',
            'header': 'true'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract the latest weather data
        if 'properties' in data and 'parameter' in data['properties']:
            params_data = data['properties']['parameter']
            
            # Get the most recent data point (last hour)
            latest_temperature = None
            latest_rainfall = None
            latest_wind_speed = None
            latest_humidity = None
            
            for param_name, param_data in params_data.items():
                if param_data and len(param_data) > 0:
                    # Get the last available data point
                    latest_value = list(param_data.values())[-1]
                    
                    if param_name == 'T2M':
                        latest_temperature = latest_value
                    elif param_name == 'PRECTOTCORR':
                        latest_rainfall = latest_value
                    elif param_name == 'WS2M':
                        latest_wind_speed = latest_value
                    elif param_name == 'RH2M':
                        latest_humidity = latest_value
            
            return {
                'temperature': latest_temperature,
                'rainfall': latest_rainfall,
                'wind_speed': latest_wind_speed,
                'humidity': latest_humidity,
                'success': True
            }
        
        return {'success': False, 'error': 'No weather data found'}
        
    except Exception as e:
        print(f"Error fetching NASA weather data: {str(e)}")
        # Return mock data for testing purposes
        print("Using mock data for testing...")
        return {
            'temperature': 35.5,  # Moderate temperature
            'rainfall': 5.2,      # Low rainfall
            'wind_speed': 8.3,    # Moderate wind
            'humidity': 65.0,     # Moderate humidity
            'success': True
        }

def predict_disaster_risk(temperature, humidity, wind_speed, rainfall, city='your area'):
    """Predict disaster risk based on weather parameters"""
    try:
        # Convert to float if they're strings
        temp = float(temperature) if temperature is not None else 0
        hum = float(humidity) if humidity is not None else 0
        wind = float(wind_speed) if wind_speed is not None else 0
        rain = float(rainfall) if rainfall is not None else 0
        
        # Prediction logic based on requirements
        if rain > 10 and hum > 80:
            return {
                'risk_type': 'flood',
                'risk_level': 'high',
                'alert_message': f'🚨 Flood risk in {city} due to heavy rainfall and high humidity.'
            }
        elif temp > 40 and hum < 30:
            return {
                'risk_type': 'heatwave',
                'risk_level': 'high',
                'alert_message': f'🔥 Heatwave risk in {city}. Stay hydrated and indoors.'
            }
        else:
            return {
                'risk_type': 'none',
                'risk_level': 'low',
                'alert_message': f'✅ No active weather risks detected in {city}.'
            }
            
    except Exception as e:
        return {
            'risk_type': 'error',
            'risk_level': 'unknown',
            'alert_message': f'⚠️ Unable to assess weather risks: {str(e)}'
        }

def fetch_nasa_weather_data():
    """Backward compatibility wrapper - fetches weather data for Agra (default)"""
    return fetch_nasa_weather_data_for_coords(27.1767, 78.0081)

def store_weather_data(city, latitude, longitude, temperature, humidity, wind_speed, rainfall, risk_type, risk_level, alert_message):
    """Store weather data and prediction in database"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO weather_data (city, latitude, longitude, temperature, humidity, wind_speed, rainfall, risk_type, risk_level, alert_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (city, latitude, longitude, temperature, humidity, wind_speed, rainfall, risk_type, risk_level, alert_message))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error storing weather data: {str(e)}")
        return False

def update_weather_data():
    """Background function to update weather data periodically for all major cities"""
    # List of major Indian cities with coordinates
    cities = [
        {'name': 'Delhi', 'lat': 28.6139, 'lon': 77.2090},
        {'name': 'Mumbai', 'lat': 19.0760, 'lon': 72.8777},
        {'name': 'Chennai', 'lat': 13.0827, 'lon': 80.2707},
        {'name': 'Kolkata', 'lat': 22.5726, 'lon': 88.3639},
        {'name': 'Bengaluru', 'lat': 12.9716, 'lon': 77.5946},
        {'name': 'Hyderabad', 'lat': 17.3850, 'lon': 78.4867},
        {'name': 'Agra', 'lat': 27.1767, 'lon': 78.0081},
        {'name': 'Patna', 'lat': 25.5941, 'lon': 85.1376},
        {'name': 'Guwahati', 'lat': 26.1445, 'lon': 91.7362},
        {'name': 'Jaipur', 'lat': 26.9124, 'lon': 75.7873}
    ]
    
    while True:
        try:
            print("Updating weather data for all cities...")
            
            # Update weather data for each city
            for city_info in cities:
                try:
                    # Fetch weather data from NASA API
                    weather_data = fetch_nasa_weather_data_for_coords(
                        city_info['lat'], 
                        city_info['lon']
                    )
                    
                    if weather_data.get('success'):
                        # Predict disaster risk
                        prediction = predict_disaster_risk(
                            weather_data['temperature'],
                            weather_data['humidity'],
                            weather_data['wind_speed'],
                            weather_data['rainfall'],
                            city_info['name']
                        )
                        
                        # Store in database
                        store_weather_data(
                            city=city_info['name'],
                            latitude=city_info['lat'],
                            longitude=city_info['lon'],
                            temperature=weather_data['temperature'],
                            humidity=weather_data['humidity'],
                            wind_speed=weather_data['wind_speed'],
                            rainfall=weather_data['rainfall'],
                            risk_type=prediction['risk_type'],
                            risk_level=prediction['risk_level'],
                            alert_message=prediction['alert_message']
                        )
                        
                        print(f"Weather data updated for {city_info['name']}. Risk: {prediction['risk_type']}")
                    else:
                        print(f"Failed to fetch weather data for {city_info['name']}: {weather_data.get('error', 'Unknown error')}")
                    
                    # Small delay between API calls to avoid rate limiting
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"Error updating weather for {city_info['name']}: {str(e)}")
                    continue
                
        except Exception as e:
            print(f"Error in weather update cycle: {str(e)}")
        
        # Wait for 4 hours (14400 seconds) before next update
        time.sleep(14400)

def initialize_weather_data():
    """Initialize weather data on startup for default city (Agra)"""
    try:
        print("Initializing weather data for Agra (default)...")
        weather_data = fetch_nasa_weather_data()
        
        if weather_data.get('success'):
            prediction = predict_disaster_risk(
                weather_data['temperature'],
                weather_data['humidity'],
                weather_data['wind_speed'],
                weather_data['rainfall'],
                'Agra'
            )
            
            store_weather_data(
                city='Agra',
                latitude=27.1767,
                longitude=78.0081,
                temperature=weather_data['temperature'],
                humidity=weather_data['humidity'],
                wind_speed=weather_data['wind_speed'],
                rainfall=weather_data['rainfall'],
                risk_type=prediction['risk_type'],
                risk_level=prediction['risk_level'],
                alert_message=prediction['alert_message']
            )
            
            print(f"Initial weather data stored for Agra. Risk: {prediction['risk_type']}")
        else:
            print(f"Failed to initialize weather data: {weather_data.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Error initializing weather data: {str(e)}")

@app.route('/api/weather-alert')
def get_weather_alert():
    """API endpoint to get the latest weather alert for emergency bar"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Get the most recent weather data
        cursor.execute('''
            SELECT alert_message, risk_type, risk_level, timestamp
            FROM weather_data
            ORDER BY timestamp DESC
            LIMIT 1
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return jsonify({
                'success': True,
                'alert_message': result[0],
                'risk_type': result[1],
                'risk_level': result[2],
                'timestamp': result[3]
            })
        else:
            return jsonify({
                'success': True,
                'alert_message': '✅ Weather monitoring system initializing...',
                'risk_type': 'none',
                'risk_level': 'low',
                'timestamp': datetime.now().isoformat()
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Unable to fetch weather alert: {str(e)}'
        }), 500

@app.route('/api/weather-data')
def get_weather_data():
    """API endpoint to get latest weather data for dashboard"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Get the most recent weather data
        cursor.execute('''
            SELECT city, temperature, humidity, wind_speed, rainfall, risk_type, risk_level, alert_message, timestamp
            FROM weather_data
            ORDER BY timestamp DESC
            LIMIT 1
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return jsonify({
                'success': True,
                'data': {
                    'city': result[0],
                    'temperature': result[1],
                    'humidity': result[2],
                    'wind_speed': result[3],
                    'rainfall': result[4],
                    'risk_type': result[5],
                    'risk_level': result[6],
                    'alert_message': result[7],
                    'timestamp': result[8]
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No weather data available'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Unable to fetch weather data: {str(e)}'
        }), 500

if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    
    # Initialize weather data on startup
    initialize_weather_data()
    
    # Start background weather update thread
    weather_thread = threading.Thread(target=update_weather_data, daemon=True)
    weather_thread.start()
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)
