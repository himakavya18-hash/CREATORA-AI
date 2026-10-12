from datetime import datetime
from models import db

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, index=True)
    
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Message {self.id} From:{self.sender_id} To:{self.receiver_id}>'


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(255), default='#')
    notification_type = db.Column(db.String(40), default='system', index=True) 
    # 'application', 'invitation', 'revision', 'approval', 'system', 'message'
    
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Notification {self.id} User:{self.user_id} Type:{self.notification_type}>'


class Report(db.Model):
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    reporter_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    reported_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    target_type = db.Column(db.String(40), nullable=False) # 'creator', 'brief', 'portfolio', 'message'
    target_id = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(100), nullable=False) # 'Copyright Infringement', 'Misleading AI Claim', 'Harassment', 'Spam'
    details = db.Column(db.Text, default='')
    status = db.Column(db.String(30), default='Pending', nullable=False, index=True) # 'Pending', 'Reviewed', 'Dismissed', 'Action Taken'
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    reporter = db.relationship('User', foreign_keys=[reporter_user_id])
    reported_user = db.relationship('User', foreign_keys=[reported_user_id])

    def __repr__(self):
        return f'<Report {self.id} Target:{self.target_type} Status:{self.status}>'


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    action = db.Column(db.String(100), nullable=False, index=True) # 'USER_LOGIN', 'CREATOR_VERIFIED', etc.
    resource_type = db.Column(db.String(50), nullable=False)
    resource_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, default='')
    ip_address = db.Column(db.String(50), default='127.0.0.1')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<AuditLog {self.action} on {self.resource_type}>'
