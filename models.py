"""Database models for the Lost and Found system."""
from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    roll_number = db.Column(db.String(40), nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active_account = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    items = db.relationship('Item', backref='owner',
                            cascade='all, delete-orphan',
                            foreign_keys='Item.user_id', lazy=True)
    claims = db.relationship('Claim', backref='claimant',
                             cascade='all, delete-orphan',
                             foreign_keys='Claim.claimant_id', lazy=True)

    @property
    def initials(self):
        parts = self.name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        return self.name[:2].upper()

    def __repr__(self):
        return f'<User {self.email}>'


class Item(db.Model):
    __tablename__ = 'items'

    CATEGORIES = [
        'Electronics',
        'ID Cards & Documents',
        'Books & Stationery',
        'Bags & Backpacks',
        'Clothing & Accessories',
        'Keys',
        'Wallets & Money',
        'Jewellery',
        'Water Bottles',
        'Sports Equipment',
        'Other',
    ]

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(80), nullable=False, index=True)
    location = db.Column(db.String(200), nullable=False)
    date_occurred = db.Column(db.Date, nullable=False)
    contact_info = db.Column(db.String(200))
    item_type = db.Column(db.String(10), nullable=False, index=True)  # 'lost' or 'found'
    status = db.Column(db.String(20), default='open', nullable=False, index=True)
    image_filename = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = db.Column(db.DateTime)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    claims = db.relationship('Claim', backref='item',
                             cascade='all, delete-orphan', lazy=True)

    @property
    def badge_color(self):
        return 'danger' if self.item_type == 'lost' else 'success'

    @property
    def status_color(self):
        return {'open': 'primary',
                'resolved': 'success',
                'closed': 'secondary'}.get(self.status, 'secondary')

    def __repr__(self):
        return f'<Item {self.id} {self.item_type} {self.title}>'


class Claim(db.Model):
    __tablename__ = 'claims'

    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)
    # pending | approved | rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    claimant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    @property
    def status_color(self):
        return {'pending': 'warning',
                'approved': 'success',
                'rejected': 'danger'}.get(self.status, 'secondary')

    def __repr__(self):
        return f'<Claim {self.id} item={self.item_id} status={self.status}>'
