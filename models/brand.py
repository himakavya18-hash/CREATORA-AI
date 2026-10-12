from datetime import datetime
from models import db

class BrandProfile(db.Model):
    __tablename__ = 'brand_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    company_name = db.Column(db.String(120), nullable=False, index=True)
    logo_url = db.Column(db.String(255), default='/static/images/default-brand.png')
    industry = db.Column(db.String(100), default='Technology & Consumer Goods', index=True)
    description = db.Column(db.Text, default='')
    
    website = db.Column(db.String(255), default='')
    contact_email = db.Column(db.String(120), default='')
    target_audience = db.Column(db.String(255), default='Tech enthusiasts & modern consumers')
    preferred_formats = db.Column(db.String(200), default='Vertical Video (9:16), High-Res 4K Visuals')
    brand_style = db.Column(db.Text, default='Futuristic, clean, vibrant aesthetics with cinematic lighting')
    
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    briefs = db.relationship('CreativeBrief', backref='brand', lazy='dynamic', cascade='all, delete-orphan')
    saved_creators = db.relationship('SavedCreator', backref='brand', lazy='dynamic', cascade='all, delete-orphan')
    projects = db.relationship('Project', backref='brand', lazy='dynamic')

    def __repr__(self):
        return f'<BrandProfile {self.company_name}>'


class SavedCreator(db.Model):
    __tablename__ = 'saved_creators'

    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand_profiles.id', ondelete='CASCADE'), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('creator_profiles.id', ondelete='CASCADE'), nullable=False)
    notes = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    creator = db.relationship('CreatorProfile', backref='saved_by_brands')

    __table_args__ = (
        db.UniqueConstraint('brand_id', 'creator_id', name='uq_brand_creator_save'),
    )

    def __repr__(self):
        return f'<SavedCreator Brand:{self.brand_id} Creator:{self.creator_id}>'
