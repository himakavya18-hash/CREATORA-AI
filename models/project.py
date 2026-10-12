from datetime import datetime
from models import db

class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    brief_id = db.Column(db.Integer, db.ForeignKey('creative_briefs.id', ondelete='CASCADE'), nullable=False)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('creator_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    
    agreed_budget = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='USD')
    agreed_deadline = db.Column(db.DateTime, nullable=True)
    
    # Status: 'In Progress', 'In Review', 'Revisions Requested', 'Completed', 'Cancelled'
    status = db.Column(db.String(40), default='In Progress', nullable=False, index=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    milestones = db.relationship('ProjectMilestone', backref='project', lazy='dynamic', cascade='all, delete-orphan', order_by='ProjectMilestone.order_index')
    revisions = db.relationship('RevisionRecord', backref='project', lazy='dynamic', cascade='all, delete-orphan', order_by='RevisionRecord.version_number.desc()')
    messages = db.relationship('Message', backref='project', lazy='dynamic')

    def progress_percentage(self):
        total = self.milestones.count()
        if total == 0:
            return 100 if self.status == 'Completed' else 25
        approved = self.milestones.filter_by(status='Approved').count()
        return int((approved / total) * 100)

    def __repr__(self):
        return f'<Project #{self.id} Status:{self.status}>'


class ProjectMilestone(db.Model):
    __tablename__ = 'project_milestones'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, default='')
    due_date = db.Column(db.DateTime, nullable=True)
    # Status: 'Pending', 'Submitted', 'Approved'
    status = db.Column(db.String(30), default='Pending', nullable=False)
    order_index = db.Column(db.Integer, default=1)

    def __repr__(self):
        return f'<ProjectMilestone {self.title} Status:{self.status}>'


class RevisionRecord(db.Model):
    __tablename__ = 'revision_records'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    milestone_id = db.Column(db.Integer, db.ForeignKey('project_milestones.id', ondelete='SET NULL'), nullable=True)
    
    version_number = db.Column(db.Integer, default=1, nullable=False)
    requested_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    revision_notes = db.Column(db.Text, nullable=False)
    draft_url = db.Column(db.String(300), default='')
    draft_type = db.Column(db.String(30), default='video') # 'video', 'image', 'document'
    # Status: 'Pending Review', 'Accepted', 'Superseded'
    status = db.Column(db.String(30), default='Pending Review', nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    requested_by = db.relationship('User', foreign_keys=[requested_by_user_id])
    milestone = db.relationship('ProjectMilestone', foreign_keys=[milestone_id])

    def __repr__(self):
        return f'<RevisionRecord Project:{self.project_id} v{self.version_number}>'
