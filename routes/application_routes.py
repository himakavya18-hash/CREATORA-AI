from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from models import db, CreativeBrief, CreatorProfile, Application, Project, ProjectMilestone
from routes.auth_routes import creator_required, brand_required
from services import AIService, NotificationService

app_bp = Blueprint('application', __name__)

@app_bp.route('/briefs/<int:brief_id>/apply', methods=['GET', 'POST'])
@creator_required
def apply_to_brief(brief_id):
    profile = current_user.creator_profile
    brief = CreativeBrief.query.get_or_404(brief_id)

    if brief.status != 'Published':
        flash('This campaign is not currently accepting applications.', 'warning')
        return redirect(url_for('brief.view_brief', brief_id=brief.id))

    existing = Application.query.filter_by(brief_id=brief.id, creator_id=profile.id).first()
    if existing and not existing.is_invitation:
        flash('You have already submitted an application for this campaign brief.', 'info')
        return redirect(url_for('brief.view_brief', brief_id=brief.id))

    if request.method == 'POST':
        proposal_text = request.form.get('proposal_text', '').strip()
        proposed_budget = float(request.form.get('proposed_budget', brief.budget_min))
        estimated_delivery_days = int(request.form.get('estimated_delivery_days', 7))

        if not proposal_text:
            flash('Please articulate your proposal and creative approach.', 'danger')
            return render_template('application_form.html', brief=brief, profile=profile, existing=existing)

        if existing and existing.is_invitation:
            existing.proposal_text = proposal_text
            existing.proposed_budget = proposed_budget
            existing.estimated_delivery_days = estimated_delivery_days
            existing.status = 'Submitted'
            existing.updated_at = datetime.utcnow()
            app_record = existing
        else:
            app_record = Application(
                brief_id=brief.id,
                creator_id=profile.id,
                proposal_text=proposal_text,
                proposed_budget=proposed_budget,
                estimated_delivery_days=estimated_delivery_days,
                status='Submitted'
            )
            db.session.add(app_record)

        db.session.commit()

        # Notify brand
        brand_user_id = brief.brand.user_id
        NotificationService.send_notification(
            user_id=brand_user_id,
            title=f"New Application for '{brief.title}'",
            message=f"{profile.display_name} submitted a proposal (₹{proposed_budget:,.0f}).",
            link=url_for('brief.view_brief', brief_id=brief.id),
            notification_type='application'
        )

        flash('Your proposal was successfully submitted to the brand!', 'success')
        return redirect(url_for('brief.view_brief', brief_id=brief.id))

    return render_template('application_form.html', brief=brief, profile=profile, existing=existing)

@app_bp.route('/applications')
@login_required
def my_applications():
    if current_user.is_creator:
        profile = current_user.creator_profile
        applications = profile.applications.order_by(Application.submitted_at.desc()).all()
        return render_template('applications_creator.html', applications=applications)
    elif current_user.is_brand:
        profile = current_user.brand_profile
        brief_ids = [b.id for b in profile.briefs]
        applications = Application.query.filter(Application.brief_id.in_(brief_ids)).order_by(Application.submitted_at.desc()).all() if brief_ids else []
        return render_template('applications_brand.html', applications=applications)
    else:
        abort(403)

@app_bp.route('/applications/<int:app_id>/status/<new_status>', methods=['POST'])
@login_required
def update_application_status(app_id, new_status):
    app_record = Application.query.get_or_404(app_id)
    brief = app_record.brief
    creator = app_record.creator

    # Authorization checks
    if current_user.is_brand:
        if brief.brand_id != current_user.brand_profile.id:
            abort(403)
        if new_status not in ['Shortlisted', 'Accepted', 'Rejected']:
            flash('Invalid status update.', 'danger')
            return redirect(request.referrer or url_for('application.my_applications'))

        app_record.status = new_status
        app_record.updated_at = datetime.utcnow()

        # When brand accepts, initialize a Project Collaboration Workspace!
        if new_status == 'Accepted':
            # Check if project already exists
            existing_project = Project.query.filter_by(brief_id=brief.id, creator_id=creator.id).first()
            if not existing_project:
                deadline_date = datetime.utcnow() + timedelta(days=app_record.estimated_delivery_days)
                new_project = Project(
                    brief_id=brief.id,
                    brand_id=brief.brand_id,
                    creator_id=creator.id,
                    agreed_budget=app_record.proposed_budget,
                    currency=brief.currency,
                    agreed_deadline=deadline_date,
                    status='In Progress'
                )
                db.session.add(new_project)
                db.session.flush()

                # Add default milestones
                m1 = ProjectMilestone(
                    project_id=new_project.id,
                    title='Concept & Styleframes',
                    description='Moodboards, seed prompts, and initial visual frames.',
                    due_date=datetime.utcnow() + timedelta(days=max(1, app_record.estimated_delivery_days // 3)),
                    status='Pending',
                    order_index=1
                )
                m2 = ProjectMilestone(
                    project_id=new_project.id,
                    title='First Draft Cut',
                    description='High-definition video/image render draft for review.',
                    due_date=datetime.utcnow() + timedelta(days=max(2, (app_record.estimated_delivery_days * 2) // 3)),
                    status='Pending',
                    order_index=2
                )
                m3 = ProjectMilestone(
                    project_id=new_project.id,
                    title='Final Master Delivery',
                    description='Upscaled master exports, license documentation, and final approval.',
                    due_date=deadline_date,
                    status='Pending',
                    order_index=3
                )
                db.session.add_all([m1, m2, m3])

            NotificationService.send_notification(
                user_id=creator.user_id,
                title="Proposal Accepted! Project Created 🎉",
                message=f"Brand {brief.brand.company_name} accepted your proposal for '{brief.title}'. Your project collaboration workspace is live!",
                link=url_for('project.list_projects'),
                notification_type='approval'
            )
            flash(f"Application accepted! A project collaboration workspace has been initialized with {creator.display_name}.", 'success')
        elif new_status == 'Shortlisted':
            NotificationService.send_notification(
                user_id=creator.user_id,
                title="Application Shortlisted ⭐",
                message=f"You have been shortlisted by {brief.brand.company_name} for '{brief.title}'.",
                link=url_for('application.my_applications'),
                notification_type='application'
            )
            flash(f"Creator {creator.display_name} has been shortlisted.", 'info')
        elif new_status == 'Rejected':
            NotificationService.send_notification(
                user_id=creator.user_id,
                title="Application Update",
                message=f"Your proposal for '{brief.title}' was not selected this time.",
                link=url_for('application.my_applications'),
                notification_type='application'
            )
            flash(f"Application marked as rejected.", 'info')

    elif current_user.is_creator:
        if app_record.creator_id != current_user.creator_profile.id:
            abort(403)
        if new_status == 'Withdrawn':
            app_record.status = 'Withdrawn'
            app_record.updated_at = datetime.utcnow()
            flash('Application withdrawn.', 'info')

    db.session.commit()
    return redirect(request.referrer or url_for('application.my_applications'))

@app_bp.route('/api/ai-proposal', methods=['POST'])
@creator_required
def api_generate_proposal():
    data = request.get_json() or {}
    brief_id = data.get('brief_id')
    brief = CreativeBrief.query.get_or_404(brief_id)
    profile = current_user.creator_profile

    brief_data = {
        'title': brief.title,
        'description': brief.description,
        'deliverables_count': brief.deliverables_count,
        'creative_style': brief.creative_style,
        'preferred_platform': brief.preferred_platform,
        'product_or_service': brief.product_or_service,
        'budget_min': brief.budget_min,
        'budget_max': brief.budget_max,
        'aspect_ratio': brief.aspect_ratio,
        'resolution': brief.resolution,
        'review_stages': brief.review_stages
    }

    result = AIService.generate_creator_proposal(brief_data, profile)
    return jsonify({'success': True, 'proposal': result})
