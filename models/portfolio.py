from datetime import datetime
from models import db

class PortfolioItem(db.Model):
    __tablename__ = 'portfolio_items'

    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('creator_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(80), nullable=False, index=True) # e.g. Product Ads, Fashion, Sci-Fi, Concept Art
    tags = db.Column(db.String(255), default='') # comma-separated
    
    # Media
    media_type = db.Column(db.String(20), default='image', nullable=False) # 'image', 'video'
    media_url = db.Column(db.String(300), nullable=False)
    thumbnail_url = db.Column(db.String(300), default='')
    
    # AI Pipeline & Specifications
    ai_tools_used = db.Column(db.String(200), default='Midjourney, Photoshop AI')
    models_used = db.Column(db.String(150), default='Midjourney v6.1')
    workflow_stages = db.Column(db.Text, default='Prompting -> Latent Inpainting -> Magnific AI Upscale -> Final Color Grade')
    output_format = db.Column(db.String(50), default='PNG') # MP4, PNG, WebM, etc.
    aspect_ratio = db.Column(db.String(20), default='16:9') # 16:9, 9:16, 1:1, 4:5
    resolution = db.Column(db.String(30), default='3840x2160') # 4K, 1080p, etc.
    intended_use = db.Column(db.String(100), default='Commercial Brand Campaign')
    
    # Licensing & Compliance
    asset_sources = db.Column(db.Text, default='Original synthetic generation from prompt')
    licensing_declaration = db.Column(db.String(100), default='Commercial Use Permitted by Tool License')
    ownership_declaration = db.Column(db.String(150), default='Created and curated by creator using licensed AI engines')
    
    # Visibility & Flags
    is_featured = db.Column(db.Boolean, default=False, index=True)
    is_public = db.Column(db.Boolean, default=True, index=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    tools = db.relationship('PortfolioTool', backref='portfolio_item', lazy='dynamic', cascade='all, delete-orphan')

    def get_tags_list(self):
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(',') if t.strip()]

    def get_tools_list(self):
        if not self.ai_tools_used:
            return []
        return [t.strip() for t in self.ai_tools_used.split(',') if t.strip()]

    def __repr__(self):
        return f'<PortfolioItem {self.title}>'


class PortfolioTool(db.Model):
    __tablename__ = 'portfolio_tools'

    id = db.Column(db.Integer, primary_key=True)
    portfolio_item_id = db.Column(db.Integer, db.ForeignKey('portfolio_items.id', ondelete='CASCADE'), nullable=False)
    
    tool_name = db.Column(db.String(80), nullable=False)
    role_in_pipeline = db.Column(db.String(120), default='Base Generation') # e.g. Base Generation, Upscaling, Voiceover
    prompt_notes = db.Column(db.Text, default='') # configuration, parameters, seed notes

    def __repr__(self):
        return f'<PortfolioTool {self.tool_name} for Item:{self.portfolio_item_id}>'
