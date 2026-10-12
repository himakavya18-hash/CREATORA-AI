import io
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort, send_file
from flask_login import login_required, current_user
from models import db, CreativeBrief, BriefRequirement, SavedCampaign, Application
from routes.auth_routes import brand_required, creator_required
from services import AIService

brief_bp = Blueprint('brief', __name__)

@brief_bp.route('/briefs')
def list_briefs():
    query = request.args.get('q', '').strip()
    category_filter = request.args.get('category', '').strip()
    type_filter = request.args.get('type', '').strip()
    platform_filter = request.args.get('platform', '').strip()
    page = request.args.get('page', 1, type=int)

    base_query = CreativeBrief.query.filter_by(status='Published')

    if query:
        search_fmt = f"%{query}%"
        base_query = base_query.filter(
            (CreativeBrief.title.ilike(search_fmt)) |
            (CreativeBrief.description.ilike(search_fmt)) |
            (CreativeBrief.product_or_service.ilike(search_fmt)) |
            (CreativeBrief.required_skills.ilike(search_fmt))
        )

    if category_filter:
        base_query = base_query.filter(CreativeBrief.content_category.ilike(f"%{category_filter}%"))
    if type_filter:
        base_query = base_query.filter(CreativeBrief.content_type.ilike(f"%{type_filter}%"))
    if platform_filter:
        base_query = base_query.filter(CreativeBrief.preferred_platform.ilike(f"%{platform_filter}%"))

    briefs_paginated = base_query.order_by(CreativeBrief.created_at.desc()).paginate(page=page, per_page=9, error_out=False)

    saved_brief_ids = []
    if current_user.is_authenticated and current_user.is_creator and current_user.creator_profile:
        saved_brief_ids = [s.brief_id for s in current_user.creator_profile.saved_campaigns]

    return render_template('campaign_list.html',
                           briefs=briefs_paginated,
                           saved_brief_ids=saved_brief_ids,
                           query=query,
                           category_filter=category_filter,
                           type_filter=type_filter,
                           platform_filter=platform_filter)

@brief_bp.route('/briefs/new', methods=['GET', 'POST'])
@brand_required
def create_brief():
    profile = current_user.brand_profile
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        product_or_service = request.form.get('product_or_service', '').strip()
        objective = request.form.get('objective', 'Brand Awareness').strip()
        target_audience = request.form.get('target_audience', '').strip()
        content_category = request.form.get('content_category', 'Commercial Ads').strip()
        content_type = request.form.get('content_type', 'AI Video Ad').strip()
        creative_style = request.form.get('creative_style', '').strip()
        preferred_platform = request.form.get('preferred_platform', '').strip()
        video_duration = request.form.get('video_duration', '15-30 seconds').strip()
        aspect_ratio = request.form.get('aspect_ratio', '9:16 (Vertical)').strip()
        resolution = request.form.get('resolution', '1080x1920 (HD)').strip()
        deliverables_count = int(request.form.get('deliverables_count', 1))
        required_skills = request.form.get('required_skills', '').strip()
        preferred_ai_tools = request.form.get('preferred_ai_tools', '').strip()
        budget_min = float(request.form.get('budget_min', 500))
        budget_max = float(request.form.get('budget_max', 1500))
        currency = request.form.get('currency', 'USD').strip()
        delivery_schedule = request.form.get('delivery_schedule', '').strip()
        commercial_use_required = bool(request.form.get('commercial_use_required', True))
        usage_duration = request.form.get('usage_duration', '').strip()
        permitted_platforms = request.form.get('permitted_platforms', '').strip()
        acceptance_criteria = request.form.get('acceptance_criteria', '').strip()
        review_stages = int(request.form.get('review_stages', 2))
        status = request.form.get('status', 'Published')

        if not title or not description or not product_or_service:
            flash('Title, product/service, and description are mandatory.', 'danger')
            return render_template('campaign_form.html', brief=None)

        brief = CreativeBrief(
            brand_id=profile.id,
            title=title,
            description=description,
            product_or_service=product_or_service,
            objective=objective,
            target_audience=target_audience,
            content_category=content_category,
            content_type=content_type,
            creative_style=creative_style,
            preferred_platform=preferred_platform,
            video_duration=video_duration,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            deliverables_count=deliverables_count,
            required_skills=required_skills,
            preferred_ai_tools=preferred_ai_tools,
            budget_min=budget_min,
            budget_max=budget_max,
            currency=currency,
            delivery_schedule=delivery_schedule,
            commercial_use_required=commercial_use_required,
            usage_duration=usage_duration,
            permitted_platforms=permitted_platforms,
            acceptance_criteria=acceptance_criteria,
            review_stages=review_stages,
            status=status
        )
        db.session.add(brief)
        db.session.commit()

        flash(f"Campaign brief '{brief.title}' has been successfully {status.lower()}!", 'success')
        return redirect(url_for('brief.view_brief', brief_id=brief.id))

    return render_template('campaign_form.html', brief=None)

@brief_bp.route('/briefs/ai-builder', methods=['GET', 'POST'])
@brand_required
def ai_builder():
    """AI Brief Builder converting user prompt into structured campaign brief."""
    if request.method == 'POST':
        prompt_text = request.form.get('prompt', '').strip()
        if not prompt_text:
            flash('Please describe your campaign concept.', 'warning')
            return render_template('ai_brief_builder.html')

        ai_brief_result = AIService.generate_campaign_brief(prompt_text)
        return render_template('campaign_form.html', brief=None, ai_data=ai_brief_result)

    return render_template('ai_brief_builder.html')

@brief_bp.route('/api/briefs/ai-generate', methods=['POST'])
@brand_required
def api_ai_generate():
    data = request.get_json() or {}
    prompt_text = data.get('prompt', '').strip()
    if not prompt_text:
        return jsonify({'success': False, 'error': 'Prompt is required.'}), 400

    result = AIService.generate_campaign_brief(prompt_text)
    return jsonify({'success': True, 'brief': result})

@brief_bp.route('/briefs/<int:brief_id>')
def view_brief(brief_id):
    brief = CreativeBrief.query.get_or_404(brief_id)
    
    # Check if creator already applied
    has_applied = False
    existing_application = None
    if current_user.is_authenticated and current_user.is_creator and current_user.creator_profile:
        existing_application = Application.query.filter_by(brief_id=brief.id, creator_id=current_user.creator_profile.id).first()
        has_applied = existing_application is not None

    # Check if saved
    is_saved = False
    if current_user.is_authenticated and current_user.is_creator and current_user.creator_profile:
        is_saved = SavedCampaign.query.filter_by(creator_id=current_user.creator_profile.id, brief_id=brief.id).first() is not None

    applications = []
    if current_user.is_authenticated and current_user.is_brand and brief.brand_id == current_user.brand_profile.id:
        applications = brief.applications.order_by(Application.submitted_at.desc()).all()

    return render_template('campaign_detail.html',
                           brief=brief,
                           has_applied=has_applied,
                           existing_application=existing_application,
                           is_saved=is_saved,
                           applications=applications)

@brief_bp.route('/briefs/<int:brief_id>/edit', methods=['GET', 'POST'])
@brand_required
def edit_brief(brief_id):
    profile = current_user.brand_profile
    brief = CreativeBrief.query.filter_by(id=brief_id, brand_id=profile.id).first_or_404()

    if request.method == 'POST':
        brief.title = request.form.get('title', brief.title).strip()
        brief.description = request.form.get('description', brief.description).strip()
        brief.product_or_service = request.form.get('product_or_service', brief.product_or_service).strip()
        brief.objective = request.form.get('objective', brief.objective).strip()
        brief.target_audience = request.form.get('target_audience', brief.target_audience).strip()
        brief.content_category = request.form.get('content_category', brief.content_category).strip()
        brief.content_type = request.form.get('content_type', brief.content_type).strip()
        brief.creative_style = request.form.get('creative_style', brief.creative_style).strip()
        brief.preferred_platform = request.form.get('preferred_platform', brief.preferred_platform).strip()
        brief.video_duration = request.form.get('video_duration', brief.video_duration).strip()
        brief.aspect_ratio = request.form.get('aspect_ratio', brief.aspect_ratio).strip()
        brief.resolution = request.form.get('resolution', brief.resolution).strip()
        brief.deliverables_count = int(request.form.get('deliverables_count', brief.deliverables_count))
        brief.required_skills = request.form.get('required_skills', brief.required_skills).strip()
        brief.preferred_ai_tools = request.form.get('preferred_ai_tools', brief.preferred_ai_tools).strip()
        brief.budget_min = float(request.form.get('budget_min', brief.budget_min))
        brief.budget_max = float(request.form.get('budget_max', brief.budget_max))
        brief.delivery_schedule = request.form.get('delivery_schedule', brief.delivery_schedule).strip()
        brief.acceptance_criteria = request.form.get('acceptance_criteria', brief.acceptance_criteria).strip()
        brief.review_stages = int(request.form.get('review_stages', brief.review_stages))
        brief.status = request.form.get('status', brief.status)
        brief.updated_at = datetime.utcnow()

        db.session.commit()
        flash('Campaign brief updated successfully.', 'success')
        return redirect(url_for('brief.view_brief', brief_id=brief.id))

    return render_template('campaign_form.html', brief=brief)

@brief_bp.route('/briefs/<int:brief_id>/status/<new_status>', methods=['POST'])
@brand_required
def update_status(brief_id, new_status):
    profile = current_user.brand_profile
    brief = CreativeBrief.query.filter_by(id=brief_id, brand_id=profile.id).first_or_404()
    if new_status in ['Draft', 'Published', 'Paused', 'Closed']:
        brief.status = new_status
        db.session.commit()
        flash(f"Campaign status updated to {new_status}.", 'info')
    return redirect(url_for('brief.view_brief', brief_id=brief.id))

@brief_bp.route('/briefs/<int:brief_id>/save', methods=['POST'])
@creator_required
def toggle_save_brief(brief_id):
    profile = current_user.creator_profile
    brief = CreativeBrief.query.get_or_404(brief_id)

    existing = SavedCampaign.query.filter_by(creator_id=profile.id, brief_id=brief.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        msg = f"Removed '{brief.title}' from saved campaigns."
        is_saved = False
    else:
        new_save = SavedCampaign(creator_id=profile.id, brief_id=brief.id)
        db.session.add(new_save)
        db.session.commit()
        msg = f"Saved '{brief.title}' to your bookmarks."
        is_saved = True

    if request.is_json:
        return jsonify({'success': True, 'is_saved': is_saved, 'message': msg})

    flash(msg, 'info')
    return redirect(request.referrer or url_for('brief.view_brief', brief_id=brief.id))

@brief_bp.route('/briefs/<int:brief_id>/pdf')
def export_brief_pdf(brief_id):
    """Exports campaign brief as a clean professional PDF using ReportLab."""
    brief = CreativeBrief.query.get_or_404(brief_id)

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=22,
            textColor=colors.HexColor('#6366F1'),
            spaceAfter=12
        )
        body_style = styles['Normal']
        body_style.fontSize = 10
        body_style.leading = 14

        story = []
        story.append(Paragraph(f"Creatora AI — Campaign Brief Specification", title_style))
        story.append(Paragraph(f"<b>Campaign:</b> {brief.title}", styles['Heading2']))
        story.append(Paragraph(f"<b>Brand:</b> {brief.brand.company_name} | <b>Status:</b> {brief.status} | <b>Created:</b> {brief.created_at.strftime('%Y-%m-%d')}", body_style))
        story.append(Spacer(1, 15))

        story.append(Paragraph("<b>Campaign Overview & Scope</b>", styles['Heading3']))
        story.append(Paragraph(brief.description, body_style))
        story.append(Spacer(1, 15))

        data = [
            ['Product / Service', brief.product_or_service],
            ['Campaign Objective', brief.objective],
            ['Content Category', brief.content_category],
            ['Content Type', brief.content_type],
            ['Creative Style', brief.creative_style],
            ['Target Audience', brief.target_audience],
            ['Platform & Format', f"{brief.preferred_platform} ({brief.aspect_ratio})"],
            ['Deliverables Count', str(brief.deliverables_count)],
            ['Required AI Skills', brief.required_skills or 'Standard AI pipeline'],
            ['Preferred AI Tools', brief.preferred_ai_tools or 'Generative video/stills'],
            ['Budget Range', f"${brief.budget_min:,.0f} - ${brief.budget_max:,.0f} {brief.currency}"],
            ['Delivery Schedule', brief.delivery_schedule or 'Standard 7 days'],
            ['Commercial Rights', 'Required — Full Paid Advertising' if brief.commercial_use_required else 'Organic only']
        ]

        t = Table(data, colWidths=[160, 370])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#F3F4F6')),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#1F2937')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB'))
        ]))
        story.append(t)
        story.append(Spacer(1, 15))

        story.append(Paragraph("<b>Acceptance Criteria:</b>", styles['Heading3']))
        story.append(Paragraph(brief.acceptance_criteria or 'High resolution deliverable, prompt consistency, and client satisfaction.', body_style))

        doc.build(story)
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"creatora_brief_{brief.id}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        flash(f'PDF generation error: {e}', 'warning')
        return redirect(url_for('brief.view_brief', brief_id=brief.id))
