from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session, send_from_directory
from flask_babel import Babel, gettext as _
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime
import random
import string

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
    # If user selected language during session
    lang = session.get('language')
    if lang in LANGUAGES:
        return lang
    # If logged in and has preferred language in DB
    try:
        if 'user_id' in session:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('SELECT preferred_language FROM users WHERE id = ?', (session['user_id'],))
            row = cursor.fetchone()
            conn.close()
            if row and row[0] in LANGUAGES:
                return row[0]
    except Exception:
        pass
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            preferred_language TEXT
        )
    ''')

    # If legacy 'username' exists but 'name' missing, add 'name'
    if not _column_exists(cursor, 'users', 'name'):
        cursor.execute("ALTER TABLE users ADD COLUMN name TEXT")
    # Ensure preferred_language column exists
    if not _column_exists(cursor, 'users', 'preferred_language'):
        cursor.execute("ALTER TABLE users ADD COLUMN preferred_language TEXT")

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
        preferred_language = request.form.get('preferred_language','en')

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
        lang_value = preferred_language if preferred_language in LANGUAGES else 'en'
        if 'username' in cols:
            cursor.execute('''
                INSERT INTO users (name, username, email, password_hash, preferred_language)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, name, email, password_hash, lang_value))
        else:
            cursor.execute('''
                INSERT INTO users (name, email, password_hash, preferred_language)
                VALUES (?, ?, ?, ?)
            ''', (name, email, password_hash, lang_value))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()

        # Auto-login and set language
        session['user_id'] = user_id
        session['name'] = name
        session['language'] = preferred_language if preferred_language in LANGUAGES else 'en'
        flash('Registration successful!', 'success')
        return redirect(url_for('home'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, password_hash, preferred_language FROM users WHERE email = ?
        ''', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['name'] = user[1] or ''
            if user[3] in LANGUAGES:
                session['language'] = user[3]
            flash('Login successful!', 'success')
            return redirect(url_for('report'))
        else:
            flash('Invalid email or password!', 'error')
    
    return render_template('login.html')

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
        # Optionally persist for logged-in users
        try:
            if 'user_id' in session:
                conn = sqlite3.connect(DATABASE)
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET preferred_language = ? WHERE id = ?', (lang_code, session['user_id']))
                conn.commit()
                conn.close()
        except Exception:
            pass
    return redirect(request.referrer or url_for('home'))

# Report routes
@app.route('/report', methods=['GET', 'POST'])
def report():
    """Report page - show form and recent incidents"""
    # Enforce login for both GET and POST
    if 'user_id' not in session:
        flash('Please login to access the report page.', 'error')
        return redirect(url_for('login'))

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
    
    return render_template('report.html')

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

if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)
