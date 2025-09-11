# create_tables.py
from app import app
from models import db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()
    print("Tables created (via create_all).")

    # optional: create admin if not exists
    if not User.query.filter_by(email='admin@example.com').first():
        admin = User(
            name='Admin',
            email='admin@example.com',
            password_hash=generate_password_hash('adminpass')
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created: admin@example.com / adminpass")
