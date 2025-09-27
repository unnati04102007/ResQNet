from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database setup
DATABASE = 'donations.db'

def init_db():
    """Initialize the SQLite database and create donations table"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donor_name TEXT NOT NULL,
            donor_email TEXT NOT NULL,
            amount REAL NOT NULL CHECK (amount > 0),
            currency TEXT NOT NULL DEFAULT 'USD',
            purpose TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')

@app.route('/api/donate', methods=['POST'])
def donate():
    """Handle donation submission"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['donor_name', 'donor_email', 'amount']
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
            INSERT INTO donations (donor_name, donor_email, amount, currency, purpose)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            data['donor_name'],
            data['donor_email'],
            amount,
            data.get('currency', 'USD'),
            data.get('purpose', '')
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
            SELECT id, donor_name, donor_email, amount, currency, purpose, created_at
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
                'created_at': row[6]
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
