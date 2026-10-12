import pytest
from app import create_app
from models import db, User, CreatorProfile, CreativeBrief, PortfolioItem
from services import MatchingService

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

def test_explainable_matching_scoring(app):
    # Setup test brand & creator
    u_b = User(email='b@test.com', role='brand')
    u_b.set_password('Password123!')
    u_c = User(email='c@test.com', role='creator')
    u_c.set_password('Password123!')
    db.session.add_all([u_b, u_c])
    db.session.flush()

    creator = CreatorProfile(
        user_id=u_c.id,
        display_name='Test Creator',
        skills='Runway Gen-3, Midjourney v6',
        specialization='Commercial Ads',
        ai_tools='Runway Gen-3, Midjourney v6',
        availability_status='Available',
        hourly_rate_min=500.0,
        hourly_rate_max=1200.0,
        portfolio_completeness=85
    )
    db.session.add(creator)
    db.session.flush()

    brief = CreativeBrief(
        brand_id=1,
        title='Luxury Commercial',
        description='Looking for Runway Gen-3 macro video.',
        product_or_service='Serum',
        content_category='Commercial Ads',
        content_type='AI Video Ad',
        required_skills='Runway Gen-3, Midjourney v6',
        preferred_ai_tools='Runway Gen-3, Midjourney v6',
        budget_min=500.0,
        budget_max=1500.0,
        status='Published'
    )
    db.session.add(brief)
    db.session.commit()

    results = MatchingService.match_creators_for_brief(brief, creators=[creator])
    assert len(results) == 1
    top_match = results[0]
    assert top_match['score'] >= 70
    assert 'breakdown' in top_match
    assert 'strengths' in top_match
    assert len(top_match['strengths']) > 0
