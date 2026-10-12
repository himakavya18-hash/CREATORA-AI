from datetime import datetime
from models import db

class Application(db.Model):
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)
    brief_id = db.Column(db.Integer, db.ForeignKey('creative_briefs.id', ondelete='CASCADE'), nullable=False, index=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('creator_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    
    proposal_text = db.Column(db.Text, nullable=False)
    proposed_budget = db.Column(db.Float, nullable=False)
    estimated_delivery_days = db.Column(db.Integer, default=7)
    
    # Status: 'Draft', 'Submitted', 'Shortlisted', 'Accepted', 'Rejected', 'Withdrawn'
    status = db.Column(db.String(30), default='Submitted', nullable=False, index=True)
    is_invitation = db.Column(db.Boolean, default=False) # True if brand sent an invitation to creator
    
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('brief_id', 'creator_id', name='uq_brief_creator_application'),
    )

    def __repr__(self):
        return f'<Application Brief:{self.brief_id} Creator:{self.creator_id} Status:{self.status}>'


class RecommendationFeedback(db.Model):
    __tablename__ = 'recommendation_feedback'

    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand_profiles.id', ondelete='CASCADE'), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('creator_profiles.id', ondelete='CASCADE'), nullable=False)
    brief_id = db.Column(db.Integer, db.ForeignKey('creative_briefs.id', ondelete='CASCADE'), nullable=True)
    
    rating = db.Column(db.Integer, default=5) # 1-5
    helpful = db.Column(db.Boolean, default=True)
    feedback_text = db.Column(db.Text, default='')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    creator = db.relationship('CreatorProfile')
    brand = db.relationship('BrandProfile')
    brief = db.relationship('CreativeBrief')

    def __repr__(self):
        return f'<RecommendationFeedback Rating:{self.rating} Helpful:{self.helpful}>'
