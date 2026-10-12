from datetime import datetime
from models import db

class CreatorProfile(db.Model):
    __tablename__ = 'creator_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    display_name = db.Column(db.String(100), nullable=False, index=True)
    headline = db.Column(db.String(200), default='AI Artist & Content Creator')
    bio = db.Column(db.Text, default='')
    
    # Skills, Specialization, Tools
    skills = db.Column(db.Text, default='Midjourney, Runway Gen-2, Video Synthesis, Digital Art') # comma-separated
    specialization = db.Column(db.String(100), default='Commercial Ads', index=True)
    experience_level = db.Column(db.String(50), default='Intermediate') # Beginner, Intermediate, Expert, Pro Agency
    ai_tools = db.Column(db.Text, default='Midjourney, Stable Diffusion, Runway Gen-3, ElevenLabs, Pika') # comma-separated
    content_categories = db.Column(db.Text, default='E-Commerce, Social Media, Product Visuals')
    project_types = db.Column(db.Text, default='Short-form Video, Image Campaign, Concept Design')
    
    # Availability & Rates
    availability_status = db.Column(db.String(50), default='Available', index=True) # Available, Busy, On Leave
    hourly_rate_min = db.Column(db.Float, default=24000.0)
    hourly_rate_max = db.Column(db.Float, default=144000.0)
    preferred_rate_unit = db.Column(db.String(50), default='per project')
    
    # Metadata
    languages = db.Column(db.String(200), default='English')
    portfolio_completeness = db.Column(db.Integer, default=40) # 0 to 100%
    verification_status = db.Column(db.String(50), default='Not Submitted', index=True)
    contact_preferences = db.Column(db.String(255), default='Creatora In-App Messaging')
    
    location = db.Column(db.String(100), default='Global / Remote')
    website = db.Column(db.String(255), default='')
    social_links = db.Column(db.Text, default='')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    portfolio_items = db.relationship('PortfolioItem', backref='creator', lazy='dynamic', cascade='all, delete-orphan')
    verification_records = db.relationship('VerificationRecord', backref='creator', lazy='dynamic', cascade='all, delete-orphan')
    applications = db.relationship('Application', backref='creator', lazy='dynamic', cascade='all, delete-orphan')
    projects = db.relationship('Project', backref='creator', lazy='dynamic')
    saved_campaigns = db.relationship('SavedCampaign', backref='creator', lazy='dynamic', cascade='all, delete-orphan')

    def calculate_completeness(self):
        score = 0
        if self.display_name: score += 10
        if self.headline: score += 10
        if self.bio and len(self.bio) > 30: score += 15
        if self.skills: score += 15
        if self.specialization: score += 10
        if self.ai_tools: score += 10
        if self.location: score += 5
        if self.hourly_rate_min and self.hourly_rate_max: score += 10
        item_count = self.portfolio_items.count()
        if item_count >= 1: score += 10
        if item_count >= 3: score += 5
        self.portfolio_completeness = min(100, score)
        return self.portfolio_completeness

    def get_skills_list(self):
        if not self.skills:
            return []
        return [s.strip() for s in self.skills.split(',') if s.strip()]

    def get_tools_list(self):
        if not self.ai_tools:
            return []
        return [t.strip() for t in self.ai_tools.split(',') if t.strip()]

    def get_categories_list(self):
        if not self.content_categories:
            return []
        return [c.strip() for c in self.content_categories.split(',') if c.strip()]

    def __repr__(self):
        return f'<CreatorProfile {self.display_name}>'


class VerificationRecord(db.Model):
    __tablename__ = 'verification_records'

    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('creator_profiles.id', ondelete='CASCADE'), nullable=False)
    
    status = db.Column(db.String(50), default='Pending Review', nullable=False, index=True)
    # 'Not Submitted', 'Pending Review', 'Verified', 'Rejected', 'Additional Evidence Required'
    
    portfolio_evidence_links = db.Column(db.Text, nullable=False)
    tools_workflow_info = db.Column(db.Text, nullable=False)
    past_references = db.Column(db.Text, default='')
    supporting_documents = db.Column(db.Text, default='')
    
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reviewer_notes = db.Column(db.Text, default='')
    reviewed_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    reviewer = db.relationship('User', foreign_keys=[reviewer_id])

    def __repr__(self):
        return f'<VerificationRecord Creator:{self.creator_id} Status:{self.status}>'


class SavedCampaign(db.Model):
    __tablename__ = 'saved_campaigns'

    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('creator_profiles.id', ondelete='CASCADE'), nullable=False)
    brief_id = db.Column(db.Integer, db.ForeignKey('creative_briefs.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('creator_id', 'brief_id', name='uq_creator_brief_save'),
    )
