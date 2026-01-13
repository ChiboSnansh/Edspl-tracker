from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128))
    role = db.Column(db.String(20), default='technician')  # admin, technician
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    created_tickets = db.relationship('Ticket', backref='creator', lazy='dynamic', foreign_keys='Ticket.created_by')
    assigned_tickets = db.relationship('Ticket', backref='assignee', lazy='dynamic', foreign_keys='Ticket.assigned_to')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Ticket(db.Model):
    __tablename__ = 'tickets'

    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='open', index=True)  # open, in_progress, resolved, closed
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    category = db.Column(db.String(50), default='other')  # network, security, infrastructure, other

    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    comments = db.relationship('Comment', backref='ticket', lazy='dynamic', order_by='Comment.created_at')
    attachments = db.relationship('Attachment', backref='ticket', lazy='dynamic')
    activities = db.relationship('ActivityLog', backref='ticket', lazy='dynamic', order_by='ActivityLog.created_at.desc()')

    @staticmethod
    def generate_ticket_number():
        year = datetime.utcnow().year
        last_ticket = Ticket.query.filter(
            Ticket.ticket_number.like(f'EDSPL-{year}-%')
        ).order_by(Ticket.id.desc()).first()

        if last_ticket:
            last_num = int(last_ticket.ticket_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f'EDSPL-{year}-{new_num:04d}'

    def __repr__(self):
        return f'<Ticket {self.ticket_number}>'


class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Comment {self.id} on Ticket {self.ticket_id}>'


class Attachment(db.Model):
    __tablename__ = 'attachments'

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    filename = db.Column(db.String(256), nullable=False)  # Stored filename (UUID)
    original_filename = db.Column(db.String(256), nullable=False)  # Original name
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    uploader = db.relationship('User', backref='uploads')

    def __repr__(self):
        return f'<Attachment {self.original_filename}>'


class ActivityLog(db.Model):
    __tablename__ = 'activity_log'

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # created, updated, commented, attached, status_changed, assigned
    old_value = db.Column(db.String(256), nullable=True)
    new_value = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship('User', backref='activities')

    def __repr__(self):
        return f'<Activity {self.action} on Ticket {self.ticket_id}>'


def log_activity(ticket_id, user_id, action, old_value=None, new_value=None):
    """Helper function to log ticket activity."""
    activity = ActivityLog(
        ticket_id=ticket_id,
        user_id=user_id,
        action=action,
        old_value=old_value,
        new_value=new_value
    )
    db.session.add(activity)
    return activity
