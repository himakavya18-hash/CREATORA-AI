from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from models import db, Project, ProjectMilestone, RevisionRecord, Message
from services import NotificationService, PortfolioService

project_bp = Blueprint('project', __name__)

@project_bp.route('/projects')
@login_required
def list_projects():
    if current_user.is_creator:
        profile = current_user.creator_profile
        projects = profile.projects.order_by(Project.created_at.desc()).all()
    elif current_user.is_brand:
        profile = current_user.brand_profile
        projects = profile.projects.order_by(Project.created_at.desc()).all()
    elif current_user.is_admin:
        projects = Project.query.order_by(Project.created_at.desc()).all()
    else:
        abort(403)

    return render_template('projects_list.html', projects=projects)

@project_bp.route('/projects/<int:project_id>')
@login_required
def view_workspace(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Authorization check
    is_authorized = (
        current_user.is_admin or
        (current_user.is_creator and project.creator_id == current_user.creator_profile.id) or
        (current_user.is_brand and project.brand_id == current_user.brand_profile.id)
    )
    if not is_authorized:
        abort(403)

    milestones = project.milestones.all()
    revisions = project.revisions.all()
    messages = project.messages.order_by(Message.created_at.asc()).all()

    other_user = project.brand.user if current_user.is_creator else project.creator.user

    return render_template('project_workspace.html',
                           project=project,
                           milestones=milestones,
                           revisions=revisions,
                           messages=messages,
                           other_user=other_user)

@project_bp.route('/projects/<int:project_id>/milestones/<int:milestone_id>/status', methods=['POST'])
@login_required
def update_milestone_status(project_id, milestone_id):
    project = Project.query.get_or_404(project_id)
    milestone = ProjectMilestone.query.filter_by(id=milestone_id, project_id=project.id).first_or_404()

    new_status = request.form.get('status')
    if new_status in ['Pending', 'Submitted', 'Approved']:
        milestone.status = new_status
        db.session.commit()

        # Notify other party
        target_user = project.brand.user_id if current_user.is_creator else project.creator.user_id
        NotificationService.send_notification(
            user_id=target_user,
            title=f"Milestone Updated: {milestone.title}",
            message=f"Status changed to {new_status} in Project #{project.id}.",
            link=url_for('project.view_workspace', project_id=project.id),
            notification_type='revision'
        )
        flash(f"Milestone '{milestone.title}' updated to {new_status}.", 'info')

    return redirect(url_for('project.view_workspace', project_id=project.id))

@project_bp.route('/projects/<int:project_id>/revisions/submit', methods=['POST'])
@login_required
def submit_revision(project_id):
    project = Project.query.get_or_404(project_id)
    
    milestone_id = request.form.get('milestone_id', type=int)
    notes = request.form.get('revision_notes', '').strip()
    draft_type = request.form.get('draft_type', 'video')
    external_url = request.form.get('draft_url_input', '').strip()

    draft_file = request.files.get('draft_file')
    draft_url = external_url
    if draft_file and draft_file.filename:
        uploaded_url = PortfolioService.save_uploaded_media(draft_file, subfolder='deliverables')
        if uploaded_url:
            draft_url = uploaded_url

    if not notes:
        flash('Please provide notes explaining this submission / revision request.', 'danger')
        return redirect(url_for('project.view_workspace', project_id=project.id))

    current_rev_count = project.revisions.count()
    version_num = current_rev_count + 1

    rev = RevisionRecord(
        project_id=project.id,
        milestone_id=milestone_id,
        version_number=version_num,
        requested_by_user_id=current_user.id,
        revision_notes=notes,
        draft_url=draft_url,
        draft_type=draft_type,
        status='Pending Review'
    )
    db.session.add(rev)

    # If submitted by creator, update status to In Review
    if current_user.is_creator:
        project.status = 'In Review'
    elif current_user.is_brand:
        project.status = 'Revisions Requested'

    db.session.commit()

    # Notify counterparty
    target_user_id = project.brand.user.id if current_user.is_creator else project.creator.user.id
    action_type = "Deliverable Draft Submitted" if current_user.is_creator else "Revision Requested"
    NotificationService.send_notification(
        user_id=target_user_id,
        title=f"Project #{project.id}: {action_type} (v{version_num})",
        message=f"{notes[:100]}...",
        link=url_for('project.view_workspace', project_id=project.id),
        notification_type='revision'
    )

    flash(f"Submission recorded as Version {version_num}.", 'success')
    return redirect(url_for('project.view_workspace', project_id=project.id))

@project_bp.route('/projects/<int:project_id>/approve', methods=['POST'])
@login_required
def approve_project(project_id):
    project = Project.query.get_or_404(project_id)
    if not (current_user.is_brand and project.brand_id == current_user.brand_profile.id) and not current_user.is_admin:
        abort(403)

    project.status = 'Completed'
    project.completed_at = datetime.utcnow()
    # Mark all milestones approved
    for m in project.milestones:
        m.status = 'Approved'
    db.session.commit()

    # Notify creator
    NotificationService.send_notification(
        user_id=project.creator.user.id,
        title="Project Approved & Completed! 🏆",
        message=f"Brand {project.brand.company_name} has given final approval for Project #{project.id} ({project.brief.title}). Congratulations!",
        link=url_for('project.view_workspace', project_id=project.id),
        notification_type='approval'
    )

    flash('Final approval granted! Project marked as Completed.', 'success')
    return redirect(url_for('project.view_workspace', project_id=project.id))
