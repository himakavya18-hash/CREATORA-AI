from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from models import db, User, CreatorProfile, BrandProfile, CreativeBrief, Project, VerificationRecord, Report, AuditLog
from routes.auth_routes import admin_required
from services import VerificationService, NotificationService

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/dashboard')
@admin_required
def dashboard():
    total_users = User.query.count()
    total_creators = CreatorProfile.query.count()
    total_brands = BrandProfile.query.count()
    total_briefs = CreativeBrief.query.count()
    total_projects = Project.query.count()
    completed_projects = Project.query.filter_by(status='Completed').count()

    # Pending verifications
    pending_verifications = VerificationRecord.query.filter_by(status='Pending Review').order_by(VerificationRecord.created_at.desc()).all()

    # Reports
    pending_reports = Report.query.filter_by(status='Pending').order_by(Report.created_at.desc()).all()

    # Recent Audit Logs
    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(15).all()

    # All users
    all_users = User.query.order_by(User.created_at.desc()).limit(20).all()

    return render_template('admin_dashboard.html',
                           total_users=total_users,
                           total_creators=total_creators,
                           total_brands=total_brands,
                           total_briefs=total_briefs,
                           total_projects=total_projects,
                           completed_projects=completed_projects,
                           pending_verifications=pending_verifications,
                           pending_reports=pending_reports,
                           recent_logs=recent_logs,
                           all_users=all_users)

@admin_bp.route('/admin/verifications/<int:record_id>/review', methods=['POST'])
@admin_required
def review_verification(record_id):
    new_status = request.form.get('status')
    notes = request.form.get('notes', '').strip()

    if new_status not in ['Verified', 'Rejected', 'Additional Evidence Required']:
        flash('Invalid verification status.', 'danger')
        return redirect(url_for('admin.dashboard'))

    record = VerificationService.review_verification(
        record_id=record_id,
        reviewer_user=current_user,
        new_status=new_status,
        notes=notes
    )

    # Notify creator
    creator = CreatorProfile.query.get(record.creator_id)
    if creator and creator.user:
        badge_msg = "Your profile is now verified! 🏅" if new_status == 'Verified' else f"Verification status: {new_status}"
        NotificationService.send_notification(
            user_id=creator.user.id,
            title=f"Verification Decision: {new_status}",
            message=f"{badge_msg}. Moderator Note: {notes or 'No notes provided.'}",
            link=url_for('creator.verification'),
            notification_type='system'
        )

    flash(f"Verification review recorded: {new_status}.", 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/admin/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Cannot suspend your own administrator account.', 'danger')
        return redirect(url_for('admin.dashboard'))

    user.is_active = not user.is_active
    db.session.commit()

    action = "RESTORED" if user.is_active else "SUSPENDED"
    log = AuditLog(
        user_id=current_user.id,
        action=f"USER_{action}",
        resource_type='User',
        resource_id=user.id,
        details=f"Admin {current_user.email} toggled status of user {user.email} to active={user.is_active}."
    )
    db.session.add(log)
    db.session.commit()

    flash(f"User {user.email} has been {action.lower()}.", 'info')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/admin/reports/<int:report_id>/resolve', methods=['POST'])
@admin_required
def resolve_report(report_id):
    report = Report.query.get_or_404(report_id)
    new_status = request.form.get('status', 'Action Taken')
    admin_action_notes = request.form.get('admin_action_notes', '')

    report.status = new_status
    log = AuditLog(
        user_id=current_user.id,
        action="REPORT_RESOLVED",
        resource_type='Report',
        resource_id=report.id,
        details=f"Admin {current_user.email} marked report #{report.id} as {new_status}. Notes: {admin_action_notes}"
    )
    db.session.add(log)
    db.session.commit()

    flash(f"Report #{report.id} updated to {new_status}.", 'info')
    return redirect(url_for('admin.dashboard'))
