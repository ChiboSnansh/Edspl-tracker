#!/usr/bin/env python3
"""
EDSPL Tracker - Database Initialization Script
Creates the database and default users.
"""

from app import app, db
from models import User

def init_database():
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully.")

        # Check if admin user exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            # Create admin user
            admin = User(
                username='admin',
                full_name='System Administrator',
                email='admin@edspl.net',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print("Created admin user: admin / admin123")

        # Check if tech user exists
        tech1 = User.query.filter_by(username='tech1').first()
        if not tech1:
            # Create technician user
            tech1 = User(
                username='tech1',
                full_name='Technical Support',
                email='support@edspl.net',
                role='technician'
            )
            tech1.set_password('tech123')
            db.session.add(tech1)
            print("Created technician user: tech1 / tech123")

        # Create additional sample users
        sample_users = [
            ('vijay', 'Vijay Tyagi', 'vijay@edspl.net', 'admin', 'vijay123'),
            ('sanjeev', 'Sanjeev Tyagi', 'sanjeev@edspl.net', 'admin', 'sanjeev123'),
            ('tech2', 'Network Engineer', 'network@edspl.net', 'technician', 'tech123'),
            ('tech3', 'Security Analyst', 'security@edspl.net', 'technician', 'tech123'),
        ]

        for username, full_name, email, role, password in sample_users:
            existing = User.query.filter_by(username=username).first()
            if not existing:
                user = User(
                    username=username,
                    full_name=full_name,
                    email=email,
                    role=role
                )
                user.set_password(password)
                db.session.add(user)
                print(f"Created user: {username} / {password}")

        db.session.commit()
        print("\nDatabase initialization complete!")
        print("\n" + "="*50)
        print("EDSPL Technical Support Tracker")
        print("="*50)
        print("\nDefault Login Credentials:")
        print("-" * 30)
        print("Admin:      admin / admin123")
        print("Tech Lead:  vijay / vijay123")
        print("CEO:        sanjeev / sanjeev123")
        print("Tech 1:     tech1 / tech123")
        print("Tech 2:     tech2 / tech123")
        print("Tech 3:     tech3 / tech123")
        print("-" * 30)
        print("\nRun 'python app.py' to start the server.")
        print("Access at: http://localhost:5000")
        print("="*50)

if __name__ == '__main__':
    init_database()
