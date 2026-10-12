from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from models import db, CreativeBrief, CreatorProfile, Application, RecommendationFeedback, SavedCreator
from routes.auth_routes import brand_required
from services import MatchingService, NotificationService

matching_bp = Blueprint('matching', __name__)

@matching_bp.route('/briefs/<int:brief_id>/match')
@brand_required
def match_creators(brief_id):
    profile = current_user.brand_profile
    brief = CreativeBrief.query.filter_by(id=brief_id, brand_id=profile.id).first_or_404()

    # Query params for interactive weight / eligibility adjustments
    availability_filter = request.args.get('availability', '')
    verified_only = request.args.get('verified_only', '').lower() == 'true'
    max_rate = request.args.get('max_rate', '')

    filters = {}
    if availability_filter:
        filters['availability'] = availability_filter
    if verified_only:
        filters['verification_only'] = True
    if max_rate:
        try:
            filters['max_rate'] = float(max_rate)
        except ValueError:
            pass

    # Dynamic weights if brand adjusted sliders
    weights = dict(MatchingService.DEFAULT_WEIGHTS)
    if 'w_skills' in request.args:
        try:
            weights['skills'] = float(request.args.get('w_skills', 0.25))
            weights['portfolio'] = float(request.args.get('w_portfolio', 0.25))
            weights['specialization'] = float(request.args.get('w_specialization', 0.15))
            weights['tools'] = float(request.args.get('w_tools', 0.10))
            weights['format'] = float(request.args.get('w_format', 0.10))
            weights['budget'] = float(request.args.get('w_budget', 0.10))
            weights['availability'] = float(request.args.get('w_availability', 0.05))
            # Normalize sum to 1.0
            total_w = sum(weights.values())
            if total_w > 0:
                weights = {k: v / total_w for k, v in weights.items()}
        except Exception:
            weights = MatchingService.DEFAULT_WEIGHTS

    matched_results = MatchingService.match_creators_for_brief(brief, weights=weights, filters=filters)

    # Check which creators are already invited or applied
    existing_applications = {app.creator_id: app for app in brief.applications.all()}
    saved_creator_ids = [s.creator_id for s in profile.saved_creators]

    return render_template('matching_results.html',
                           brief=brief,
                           matched_results=matched_results,
                           existing_applications=existing_applications,
                           saved_creator_ids=saved_creator_ids,
                           weights=weights,
                           filters=filters)

@matching_bp.route('/briefs/<int:brief_id>/invite/<int:creator_id>', methods=['POST'])
@brand_required
def invite_creator(brief_id, creator_id):
    profile = current_user.brand_profile
    brief = CreativeBrief.query.filter_by(id=brief_id, brand_id=profile.id).first_or_404()
    creator = CreatorProfile.query.get_or_404(creator_id)

    # Check existing application or invitation
    existing = Application.query.filter_by(brief_id=brief.id, creator_id=creator.id).first()
    if existing:
        flash(f"{creator.display_name} has already applied or been invited to this campaign.", 'info')
        return redirect(url_for('matching.match_creators', brief_id=brief.id))

    invitation = Application(
        brief_id=brief.id,
        creator_id=creator.id,
        proposal_text=f"Direct brand invitation from {profile.company_name} for '{brief.title}'.",
        proposed_budget=brief.budget_max,
        estimated_delivery_days=7,
        status='Submitted',
        is_invitation=True
    )
    db.session.add(invitation)
    db.session.commit()

    # Notify creator
    NotificationService.send_notification(
        user_id=creator.user_id,
        title=f"Campaign Invitation from {profile.company_name}!",
        message=f"You have been personally invited to collaborate on '{brief.title}'. Check the campaign and submit your custom proposal.",
        link=url_for('brief.view_brief', brief_id=brief.id),
        notification_type='invitation'
    )

    flash(f"Invitation successfully dispatched to {creator.display_name}!", 'success')
    return redirect(url_for('matching.match_creators', brief_id=brief.id))

@matching_bp.route('/api/matching-feedback', methods=['POST'])
@brand_required
def submit_feedback():
    data = request.get_json() or {}
    creator_id = data.get('creator_id')
    brief_id = data.get('brief_id')
    rating = data.get('rating', 5)
    helpful = data.get('helpful', True)
    feedback_text = data.get('feedback_text', '')

    if not creator_id:
        return jsonify({'success': False, 'error': 'Creator ID required.'}), 400

    fb = RecommendationFeedback(
        brand_id=current_user.brand_profile.id,
        creator_id=creator_id,
        brief_id=brief_id,
        rating=int(rating),
        helpful=bool(helpful),
        feedback_text=feedback_text
    )
    db.session.add(fb)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Thank you! Your feedback helps refine our AI matching weights.'})
