from datetime import datetime
from models import db

class CreativeBrief(db.Model):
    __tablename__ = 'creative_briefs'

    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    product_or_service = db.Column(db.String(120), nullable=False)
    objective = db.Column(db.String(100), default='Brand Awareness', index=True)
    target_audience = db.Column(db.String(255), default='General Public')
    
    # Formats & Specifications
    content_category = db.Column(db.String(80), default='Commercial Ads', index=True)
    content_type = db.Column(db.String(80), default='AI Video Ad', index=True) # AI Video Ad, 3D Render, Motion Graphics
    creative_style = db.Column(db.String(100), default='Hyper-realistic, Cinematic')
    preferred_platform = db.Column(db.String(80), default='Instagram & TikTok')
    video_duration = db.Column(db.String(50), default='15-30 seconds')
    aspect_ratio = db.Column(db.String(30), default='9:16 (Vertical)')
    resolution = db.Column(db.String(30), default='1080x1920 (HD)')
    deliverables_count = db.Column(db.Integer, default=1)
    
    # Requirements & Tools
    required_skills = db.Column(db.Text, default='Runway Gen-3, Midjourney, Video Upscaling')
    preferred_ai_tools = db.Column(db.Text, default='Midjourney v6, Runway Gen-3, ElevenLabs')
    
    # Budget & Timelines
    budget_min = db.Column(db.Float, default=50000.0)
    budget_max = db.Column(db.Float, default=150000.0)
    currency = db.Column(db.String(10), default='INR')
    deadline = db.Column(db.DateTime, nullable=True)
    delivery_schedule = db.Column(db.String(150), default='Initial draft within 4 days, final cut in 7 days')
    
    # Commercial Rights & Terms
    commercial_use_required = db.Column(db.Boolean, default=True)
    usage_duration = db.Column(db.String(100), default='12 Months Paid Media & Organic')
    permitted_platforms = db.Column(db.String(150), default='Instagram, TikTok, YouTube Shorts, Web')
    reference_links = db.Column(db.Text, default='')
    acceptance_criteria = db.Column(db.Text, default='4K resolution output, no visible artifact warping, sound design included.')
    review_stages = db.Column(db.Integer, default=2) # 2 rounds of review
    
    # Lifecycle
    status = db.Column(db.String(30), default='Draft', nullable=False, index=True) # 'Draft', 'Published', 'Paused', 'Closed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    requirements = db.relationship('BriefRequirement', backref='brief', lazy='dynamic', cascade='all, delete-orphan')
    applications = db.relationship('Application', backref='brief', lazy='dynamic', cascade='all, delete-orphan')
    projects = db.relationship('Project', backref='brief', lazy='dynamic')
    saved_by_creators = db.relationship('SavedCampaign', backref='brief', lazy='dynamic', cascade='all, delete-orphan')

    def get_skills_list(self):
        if not self.required_skills:
            return []
        return [s.strip() for s in self.required_skills.split(',') if s.strip()]

    def get_tools_list(self):
        if not self.preferred_ai_tools:
            return []
        return [t.strip() for t in self.preferred_ai_tools.split(',') if t.strip()]

    def __repr__(self):
        return f'<CreativeBrief {self.title} Status:{self.status}>'


class BriefRequirement(db.Model):
    __tablename__ = 'brief_requirements'

    id = db.Column(db.Integer, primary_key=True)
    brief_id = db.Column(db.Integer, db.ForeignKey('creative_briefs.id', ondelete='CASCADE'), nullable=False)
    
    requirement_text = db.Column(db.String(255), nullable=False)
    is_mandatory = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<BriefRequirement {self.requirement_text}>'
