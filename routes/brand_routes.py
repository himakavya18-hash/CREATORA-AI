from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, User, BrandProfile, CreatorProfile, CreativeBrief, Application, Project, SavedCreator
from routes.auth_routes import brand_required
from services import PortfolioService

brand_bp = Blueprint('brand', __name__)

@brand_bp.route('/brand/dashboard')
@brand_required
def dashboard():
    profile = current_user.brand_profile
    if not profile:
        profile = BrandProfile(user_id=current_user.id, company_name=current_user.email.split('@')[0])
        db.session.add(profile)
        db.session.commit()

    briefs = profile.briefs.order_by(CreativeBrief.created_at.desc()).all()
    briefs_count = len(briefs)
    draft_briefs_count = profile.briefs.filter_by(status='Draft').count()
    published_briefs_count = profile.briefs.filter_by(status='Published').count()

    # Total applications across all brand briefs
    brief_ids = [b.id for b in briefs]
    if brief_ids:
        all_apps = Application.query.filter(Application.brief_id.in_(brief_ids)).order_by(Application.submitted_at.desc()).all()
    else:
        all_apps = []

    apps_count = len(all_apps)
    shortlisted_apps_count = sum(1 for a in all_apps if a.status == 'Shortlisted')

    # Projects
    active_projects = profile.projects.filter(Project.status.in_(['In Progress', 'In Review', 'Revisions Requested'])).all()
    completed_projects_count = profile.projects.filter_by(status='Completed').count()

    # Saved creators
    saved_creators = profile.saved_creators.all()

    # Top recommended creators
    recommended_creators = CreatorProfile.query.filter_by(availability_status='Available').order_by(CreatorProfile.portfolio_completeness.desc()).limit(4).all()

    # Analytics for Chart.js
    brief_status_counts = {
        'Published': published_briefs_count,
        'Draft': draft_briefs_count,
        'Paused': profile.briefs.filter_by(status='Paused').count(),
        'Closed': profile.briefs.filter_by(status='Closed').count()
    }

    return render_template('brand_dashboard.html',
                           profile=profile,
                           briefs=briefs,
                           briefs_count=briefs_count,
                           draft_briefs_count=draft_briefs_count,
                           published_briefs_count=published_briefs_count,
                           all_apps=all_apps[:6],
                           apps_count=apps_count,
                           shortlisted_apps_count=shortlisted_apps_count,
                           active_projects=active_projects,
                           completed_projects_count=completed_projects_count,
                           saved_creators=saved_creators,
                           recommended_creators=recommended_creators,
                           brief_status_counts=brief_status_counts)

@brand_bp.route('/brand/profile/edit', methods=['GET', 'POST'])
@brand_required
def edit_profile():
    profile = current_user.brand_profile
    if request.method == 'POST':
        profile.company_name = request.form.get('company_name', profile.company_name).strip()
        profile.industry = request.form.get('industry', profile.industry).strip()
        profile.description = request.form.get('description', profile.description).strip()
        profile.website = request.form.get('website', profile.website).strip()
        profile.contact_email = request.form.get('contact_email', profile.contact_email).strip()
        profile.target_audience = request.form.get('target_audience', profile.target_audience).strip()
        profile.preferred_formats = request.form.get('preferred_formats', profile.preferred_formats).strip()
        profile.brand_style = request.form.get('brand_style', profile.brand_style).strip()

        logo_file = request.files.get('logo_file')
        if logo_file and logo_file.filename:
            logo_url = PortfolioService.save_uploaded_media(logo_file, subfolder='avatars')
            if logo_url:
                profile.logo_url = logo_url

        db.session.commit()
        flash('Brand profile updated successfully.', 'success')
        return redirect(url_for('brand.dashboard'))

    return render_template('brand_profile_edit.html', profile=profile)

@brand_bp.route('/brand/saved-creators')
@brand_required
def saved_creators():
    profile = current_user.brand_profile
    saved_list = profile.saved_creators.all()
    return render_template('saved_creators.html', saved_list=saved_list)

@brand_bp.route('/brand/save-creator/<int:creator_id>', methods=['POST'])
@brand_required
def toggle_save_creator(creator_id):
    profile = current_user.brand_profile
    creator = CreatorProfile.query.get_or_404(creator_id)

    existing = SavedCreator.query.filter_by(brand_id=profile.id, creator_id=creator.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        is_saved = False
        msg = f"Removed {creator.display_name} from saved creators."
    else:
        new_save = SavedCreator(brand_id=profile.id, creator_id=creator.id)
        db.session.add(new_save)
        db.session.commit()
        is_saved = True
        msg = f"Saved {creator.display_name} to your shortlist."

    if request.is_json:
        return jsonify({'success': True, 'is_saved': is_saved, 'message': msg})

    flash(msg, 'info')
    return redirect(request.referrer or url_for('creator.list_creators'))
