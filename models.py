from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ---------------- USERS TABLE ----------------
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'employee', 'agent', 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------- TICKETS TABLE ----------------
class Ticket(db.Model):
    __tablename__ = 'tickets'

    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    impact = db.Column(db.String(10), nullable=False)
    urgency = db.Column(db.String(10), nullable=False)
    recommended_priority = db.Column(db.String(5))
    priority = db.Column(db.String(5))
    status = db.Column(db.String(20), default='Open')

    assigned_agent_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    assigned_at = db.Column(db.DateTime, nullable=True)
    sla_deadline = db.Column(db.DateTime, nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)
    raised_by = db.relationship('User', foreign_keys=[user_id], backref='my_tickets')
    assigned_agent = db.relationship('User', foreign_keys=[assigned_agent_id], backref='assigned_tickets')

# ---------------- COMMENTS TABLE ----------------
class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User')
    ticket = db.relationship('Ticket', backref='comments')

# ---------------- TICKET HISTORY TABLE ----------------
class TicketHistory(db.Model):
    __tablename__ = 'ticket_history'

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User')
    ticket = db.relationship('Ticket', backref='history')