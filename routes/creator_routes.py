from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from models import db, User, CreatorProfile, PortfolioItem, PortfolioTool, CreativeBrief, Application, Project, SavedCampaign, SavedCreator
from routes.auth_routes import creator_required
from services import AIService, VerificationService, PortfolioService, LicensingService

creator_bp = Blueprint('creator', __name__)

@creator_bp.route('/creator/dashboard')
@creator_required
def dashboard():
    profile = current_user.creator_profile
    if not profile:
        profile = CreatorProfile(user_id=current_user.id, display_name=current_user.email.split('@')[0])
        db.session.add(profile)
        db.session.commit()

    completeness = profile.calculate_completeness()
    portfolio_items = profile.portfolio_items.order_by(PortfolioItem.created_at.desc()).all()
    portfolio_count = len(portfolio_items)
    
    # Applications
    applications = profile.applications.order_by(Application.submitted_at.desc()).all()
    apps_count = len(applications)
    invitations_count = profile.applications.filter_by(is_invitation=True).count()
    
    # Projects
    active_projects = profile.projects.filter(Project.status.in_(['In Progress', 'In Review', 'Revisions Requested'])).all()
    completed_projects_count = profile.projects.filter_by(status='Completed').count()
    
    # Saved Campaigns
    saved_campaigns = profile.saved_campaigns.all()

    # Recommended campaigns (based on creator skills/category)
    c_skills = profile.get_skills_list()
    c_categories = profile.get_categories_list()
    all_published_briefs = CreativeBrief.query.filter_by(status='Published').order_by(CreativeBrief.created_at.desc()).limit(6).all()
    
    # AI Portfolio suggestions
    ai_portfolio_analysis = AIService.analyze_creator_portfolio(profile, portfolio_items)

    # Chart.js data: Application statuses
    app_status_counts = {
        'Submitted': 0,
        'Shortlisted': 0,
        'Accepted': 0,
        'Rejected': 0
    }
    for app in applications:
        if app.status in app_status_counts:
            app_status_counts[app.status] += 1

    return render_template('creator_dashboard.html',
                           profile=profile,
                           completeness=completeness,
                           portfolio_items=portfolio_items,
                           portfolio_count=portfolio_count,
                           applications=applications[:5],
                           apps_count=apps_count,
                           invitations_count=invitations_count,
                           active_projects=active_projects,
                           completed_projects_count=completed_projects_count,
                           saved_campaigns=saved_campaigns,
                           recommended_briefs=all_published_briefs,
                           ai_portfolio_analysis=ai_portfolio_analysis,
                           app_status_counts=app_status_counts)

@creator_bp.route('/creator/profile/edit', methods=['GET', 'POST'])
@creator_required
def edit_profile():
    profile = current_user.creator_profile
    if request.method == 'POST':
        profile.display_name = request.form.get('display_name', profile.display_name).strip()
        profile.headline = request.form.get('headline', profile.headline).strip()
        profile.bio = request.form.get('bio', profile.bio).strip()
        profile.skills = request.form.get('skills', profile.skills).strip()
        profile.specialization = request.form.get('specialization', profile.specialization).strip()
        profile.experience_level = request.form.get('experience_level', profile.experience_level)
        profile.ai_tools = request.form.get('ai_tools', profile.ai_tools).strip()
        profile.content_categories = request.form.get('content_categories', profile.content_categories).strip()
        profile.project_types = request.form.get('project_types', profile.project_types).strip()
        profile.availability_status = request.form.get('availability_status', profile.availability_status)
        profile.hourly_rate_min = float(request.form.get('hourly_rate_min', profile.hourly_rate_min or 250))
        profile.hourly_rate_max = float(request.form.get('hourly_rate_max', profile.hourly_rate_max or 1500))
        profile.preferred_rate_unit = request.form.get('preferred_rate_unit', profile.preferred_rate_unit)
        profile.languages = request.form.get('languages', profile.languages).strip()
        profile.location = request.form.get('location', profile.location).strip()
        profile.website = request.form.get('website', profile.website).strip()
        profile.contact_preferences = request.form.get('contact_preferences', profile.contact_preferences).strip()

        # Handle avatar upload
        avatar_file = request.files.get('avatar_file')
        if avatar_file and avatar_file.filename:
            avatar_url = PortfolioService.save_uploaded_media(avatar_file, subfolder='avatars')
            if avatar_url:
                current_user.avatar_url = avatar_url

        profile.calculate_completeness()
        db.session.commit()
        flash('Creator profile successfully updated.', 'success')
        return redirect(url_for('creator.dashboard'))

    return render_template('creator_profile_edit.html', profile=profile)

@creator_bp.route('/creators')
def list_creators():
    """Smart Creator Search and Filtering."""
    query = request.args.get('q', '').strip()
    skill_filter = request.args.get('skill', '').strip()
    specialization_filter = request.args.get('specialization', '').strip()
    tool_filter = request.args.get('tool', '').strip()
    category_filter = request.args.get('category', '').strip()
    exp_filter = request.args.get('experience', '').strip()
    avail_filter = request.args.get('availability', '').strip()
    verified_only = request.args.get('verified', '').lower() == 'true'
    sort_by = request.args.get('sort', 'relevance')
    page = request.args.get('page', 1, type=int)

    base_query = CreatorProfile.query.join(User).filter(User.is_active == True)

    if query:
        search_fmt = f"%{query}%"
        base_query = base_query.filter(
            (CreatorProfile.display_name.ilike(search_fmt)) |
            (CreatorProfile.headline.ilike(search_fmt)) |
            (CreatorProfile.bio.ilike(search_fmt)) |
            (CreatorProfile.skills.ilike(search_fmt))
        )

    if skill_filter:
        base_query = base_query.filter(CreatorProfile.skills.ilike(f"%{skill_filter}%"))
    if specialization_filter:
        base_query = base_query.filter(CreatorProfile.specialization.ilike(f"%{specialization_filter}%"))
    if tool_filter:
        base_query = base_query.filter(CreatorProfile.ai_tools.ilike(f"%{tool_filter}%"))
    if category_filter:
        base_query = base_query.filter(CreatorProfile.content_categories.ilike(f"%{category_filter}%"))
    if exp_filter:
        base_query = base_query.filter(CreatorProfile.experience_level == exp_filter)
    if avail_filter:
        base_query = base_query.filter(CreatorProfile.availability_status == avail_filter)
    if verified_only:
        base_query = base_query.filter(CreatorProfile.verification_status == 'Verified')

    # Sorting
    if sort_by == 'rate_low':
        base_query = base_query.order_by(CreatorProfile.hourly_rate_min.asc())
    elif sort_by == 'rate_high':
        base_query = base_query.order_by(CreatorProfile.hourly_rate_max.desc())
    elif sort_by == 'newest':
        base_query = base_query.order_by(CreatorProfile.created_at.desc())
    elif sort_by == 'completeness':
        base_query = base_query.order_by(CreatorProfile.portfolio_completeness.desc())
    else:
        # Relevance: verified first, then updated recently
        base_query = base_query.order_by(
            CreatorProfile.verification_status == 'Verified',
            CreatorProfile.updated_at.desc()
        )

    creators_paginated = base_query.paginate(page=page, per_page=9, error_out=False)

    saved_creator_ids = []
    if current_user.is_authenticated and current_user.is_brand and current_user.brand_profile:
        saved_creator_ids = [s.creator_id for s in current_user.brand_profile.saved_creators]

    return render_template('creator_search.html',
                           creators=creators_paginated,
                           saved_creator_ids=saved_creator_ids,
                           query=query,
                           skill_filter=skill_filter,
                           specialization_filter=specialization_filter,
                           tool_filter=tool_filter,
                           category_filter=category_filter,
                           exp_filter=exp_filter,
                           avail_filter=avail_filter,
                           verified_only=verified_only,
                           sort_by=sort_by)

@creator_bp.route('/creator/<int:creator_id>')
def public_profile(creator_id):
    creator = CreatorProfile.query.get_or_404(creator_id)
    items = creator.portfolio_items.filter_by(is_public=True).order_by(PortfolioItem.is_featured.desc(), PortfolioItem.created_at.desc()).all()
    
    # Check if saved by current brand
    is_saved = False
    if current_user.is_authenticated and current_user.is_brand and current_user.brand_profile:
        is_saved = SavedCreator.query.filter_by(brand_id=current_user.brand_profile.id, creator_id=creator.id).first() is not None

    # Available briefs of current brand to invite creator
    brand_briefs = []
    if current_user.is_authenticated and current_user.is_brand and current_user.brand_profile:
        brand_briefs = CreativeBrief.query.filter_by(brand_id=current_user.brand_profile.id, status='Published').all()

    return render_template('creator_profile.html',
                           creator=creator,
                           items=items,
                           is_saved=is_saved,
                           brand_briefs=brand_briefs)

@creator_bp.route('/creator/verification', methods=['GET', 'POST'])
@creator_required
def verification():
    profile = current_user.creator_profile
    latest_record = profile.verification_records.order_by(db.desc('id')).first()

    if request.method == 'POST':
        evidence_links = request.form.get('evidence_links', '').strip()
        workflow_info = request.form.get('workflow_info', '').strip()
        references = request.form.get('references', '').strip()
        docs = request.form.get('docs', '').strip()

        if not evidence_links or not workflow_info:
            flash('Please provide both portfolio evidence links and workflow documentation.', 'danger')
            return redirect(url_for('creator.verification'))

        VerificationService.submit_verification_request(
            creator_id=profile.id,
            evidence_links=evidence_links,
            workflow_info=workflow_info,
            references=references,
            docs=docs
        )
        flash('Verification request submitted successfully. Our moderation team will review your evidence.', 'success')
        return redirect(url_for('creator.verification'))

    return render_template('verification.html', profile=profile, record=latest_record)

# ==========================================
# PORTFOLIO ROUTES
# ==========================================
@creator_bp.route('/creator/portfolio/new', methods=['GET', 'POST'])
@creator_required
def add_portfolio_item():
    profile = current_user.creator_profile
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', 'Commercial Ads').strip()
        tags = request.form.get('tags', '').strip()
        media_type = request.form.get('media_type', 'image')
        ai_tools_used = request.form.get('ai_tools_used', '').strip()
        models_used = request.form.get('models_used', '').strip()
        workflow_stages = request.form.get('workflow_stages', '').strip()
        output_format = request.form.get('output_format', 'PNG').strip()
        aspect_ratio = request.form.get('aspect_ratio', '16:9').strip()
        resolution = request.form.get('resolution', '1080p').strip()
        intended_use = request.form.get('intended_use', 'Commercial Campaign').strip()
        asset_sources = request.form.get('asset_sources', '').strip()
        licensing_declaration = request.form.get('licensing_declaration', '').strip()
        ownership_declaration = request.form.get('ownership_declaration', '').strip()
        is_featured = bool(request.form.get('is_featured'))
        is_public = bool(request.form.get('is_public', True))

        # Media handling: file upload OR direct external media url
        media_file = request.files.get('media_file')
        media_url = request.form.get('media_url_input', '').strip()

        if media_file and media_file.filename:
            uploaded_url = PortfolioService.save_uploaded_media(media_file, subfolder='portfolios')
            if uploaded_url:
                media_url = uploaded_url

        if not media_url:
            # Fallback high quality placeholder if demoing without file
            media_url = 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1200&q=80'

        if not title or not description:
            flash('Title and description are required.', 'danger')
            return render_template('portfolio_form.html')

        item = PortfolioItem(
            creator_id=profile.id,
            title=title,
            description=description,
            category=category,
            tags=tags,
            media_type=media_type,
            media_url=media_url,
            thumbnail_url=media_url,
            ai_tools_used=ai_tools_used,
            models_used=models_used,
            workflow_stages=workflow_stages,
            output_format=output_format,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            intended_use=intended_use,
            asset_sources=asset_sources,
            licensing_declaration=licensing_declaration,
            ownership_declaration=ownership_declaration,
            is_featured=is_featured,
            is_public=is_public
        )
        db.session.add(item)
        db.session.flush()

        # Add initial tool pipeline breakdown
        if ai_tools_used:
            for t_name in ai_tools_used.split(','):
                t_clean = t_name.strip()
                if t_clean:
                    p_tool = PortfolioTool(
                        portfolio_item_id=item.id,
                        tool_name=t_clean,
                        role_in_pipeline='Generation & Pipeline',
                        prompt_notes=f'Configured for {output_format} output.'
                    )
                    db.session.add(p_tool)

        profile.calculate_completeness()
        db.session.commit()
        flash('Portfolio project published successfully!', 'success')
        return redirect(url_for('creator.dashboard'))

    return render_template('portfolio_form.html', item=None)

@creator_bp.route('/creator/portfolio/<int:item_id>/edit', methods=['GET', 'POST'])
@creator_required
def edit_portfolio_item(item_id):
    profile = current_user.creator_profile
    item = PortfolioItem.query.filter_by(id=item_id, creator_id=profile.id).first_or_404()

    if request.method == 'POST':
        item.title = request.form.get('title', item.title).strip()
        item.description = request.form.get('description', item.description).strip()
        item.category = request.form.get('category', item.category).strip()
        item.tags = request.form.get('tags', item.tags).strip()
        item.media_type = request.form.get('media_type', item.media_type)
        item.ai_tools_used = request.form.get('ai_tools_used', item.ai_tools_used).strip()
        item.models_used = request.form.get('models_used', item.models_used).strip()
        item.workflow_stages = request.form.get('workflow_stages', item.workflow_stages).strip()
        item.output_format = request.form.get('output_format', item.output_format).strip()
        item.aspect_ratio = request.form.get('aspect_ratio', item.aspect_ratio).strip()
        item.resolution = request.form.get('resolution', item.resolution).strip()
        item.intended_use = request.form.get('intended_use', item.intended_use).strip()
        item.asset_sources = request.form.get('asset_sources', item.asset_sources).strip()
        item.licensing_declaration = request.form.get('licensing_declaration', item.licensing_declaration).strip()
        item.ownership_declaration = request.form.get('ownership_declaration', item.ownership_declaration).strip()
        item.is_featured = bool(request.form.get('is_featured'))
        item.is_public = bool(request.form.get('is_public'))

        media_file = request.files.get('media_file')
        if media_file and media_file.filename:
            uploaded_url = PortfolioService.save_uploaded_media(media_file, subfolder='portfolios')
            if uploaded_url:
                item.media_url = uploaded_url
                item.thumbnail_url = uploaded_url

        item.updated_at = datetime.utcnow()
        profile.calculate_completeness()
        db.session.commit()
        flash('Portfolio item updated successfully.', 'success')
        return redirect(url_for('creator.dashboard'))

    return render_template('portfolio_form.html', item=item)

@creator_bp.route('/creator/portfolio/<int:item_id>/delete', methods=['POST'])
@creator_required
def delete_portfolio_item(item_id):
    profile = current_user.creator_profile
    item = PortfolioItem.query.filter_by(id=item_id, creator_id=profile.id).first_or_404()
    db.session.delete(item)
    profile.calculate_completeness()
    db.session.commit()
    flash('Portfolio item removed.', 'info')
    return redirect(url_for('creator.dashboard'))

@creator_bp.route('/creator/portfolio/<int:item_id>')
def view_portfolio_item(item_id):
    item = PortfolioItem.query.get_or_404(item_id)
    if not item.is_public and (not current_user.is_authenticated or current_user.id != item.creator.user_id):
        abort(403)
    
    # Run Commercial Usage & Licensing Assistant check
    tools_list = item.get_tools_list()
    licensing_report = LicensingService.check_commercial_compatibility(
        tools_list=tools_list,
        asset_sources=item.asset_sources,
        declaration=item.licensing_declaration,
        commercial_required=True,
        paid_ads=True
    )

    return render_template('portfolio_detail.html', item=item, licensing_report=licensing_report)

@creator_bp.route('/api/portfolio/ai-enhance', methods=['POST'])
@creator_required
def api_ai_enhance_portfolio():
    data = request.get_json() or {}
    title = data.get('title', 'AI Concept Art')
    category = data.get('category', 'Commercial')
    tools = data.get('tools', 'Midjourney v6')
    draft_notes = data.get('notes', '')

    result = AIService.enhance_portfolio_description(title, category, tools, draft_notes)
    return jsonify({'success': True, 'data': result})
