import os
os.environ['DISABLE_SQLALCHEMY_CEXT'] = '1'

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models for convenient access across the app
from models.user import User
from models.creator import CreatorProfile, VerificationRecord, SavedCampaign
from models.portfolio import PortfolioItem, PortfolioTool
from models.brand import BrandProfile, SavedCreator
from models.brief import CreativeBrief, BriefRequirement
from models.application import Application, RecommendationFeedback
from models.project import Project, ProjectMilestone, RevisionRecord
from models.messaging import Message, Notification, Report, AuditLog

__all__ = [
    'db',
    'User',
    'CreatorProfile',
    'VerificationRecord',
    'SavedCampaign',
    'PortfolioItem',
    'PortfolioTool',
    'BrandProfile',
    'SavedCreator',
    'CreativeBrief',
    'BriefRequirement',
    'Application',
    'RecommendationFeedback',
    'Project',
    'ProjectMilestone',
    'RevisionRecord',
    'Message',
    'Notification',
    'Report',
    'AuditLog'
]
