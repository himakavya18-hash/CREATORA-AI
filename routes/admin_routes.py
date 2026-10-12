from datetime import datetime
import hmac
from flask import Blueprint, current_app, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import current_user, login_user
from models import db, User, CreatorProfile, BrandProfile, CreativeBrief, Project, VerificationRecord, Report, AuditLog
from routes.auth_routes import admin_required
from services import VerificationService, NotificationService

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard') if current_user.is_admin else url_for('auth.home'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email, role='admin').first()
        if not user or not user.check_password(request.form.get('password', '')) or not user.is_active:
            flash('Invalid administrator email or password.', 'danger')
            return render_template('admin_login.html')
        user.last_login = datetime.utcnow()
        db.session.commit()
        login_user(user, remember=bool(request.form.get('remember')))
        db.session.add(AuditLog(user_id=user.id, action='ADMIN_LOGIN', resource_type='User',
                                resource_id=user.id, details=f'Administrator logged in from {request.remote_addr}.',
                                ip_address=request.remote_addr or '127.0.0.1'))
        db.session.commit()
        return redirect(url_for('admin.dashboard'))
    return render_template('admin_login.html')


@admin_bp.route('/admin/register', methods=['GET', 'POST'])
def register():
    is_existing_admin = current_user.is_authenticated and current_user.is_admin

    # If logged in as creator or brand, redirect with explanation
    if current_user.is_authenticated and not current_user.is_admin:
        flash('You are signed in as a standard user. Sign out to access administrator registration.', 'warning')
        return redirect(url_for('auth.home'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        submitted_key = request.form.get('registration_key', '').strip()

        # If not logged in as an existing admin, require the secret registration key
        if not is_existing_admin:
            expected_key = current_app.config.get('ADMIN_REGISTRATION_KEY', 'creatora-admin-2025')
            if not submitted_key or not hmac.compare_digest(expected_key, submitted_key):
                flash('The administrator registration key is invalid. Please provide the correct secret key.', 'danger')
                return render_template('admin_register.html', is_existing_admin=is_existing_admin)

        if not email or '@' not in email:
            flash('Enter a valid email address.', 'danger')
            return render_template('admin_register.html', is_existing_admin=is_existing_admin)

        if len(password) < 8:
            flash('Administrator passwords must be at least 8 characters long.', 'danger')
            return render_template('admin_register.html', is_existing_admin=is_existing_admin)

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('admin_register.html', is_existing_admin=is_existing_admin)

        if User.query.filter_by(email=email).first():
            flash('An account with that email already exists.', 'danger')
            return render_template('admin_register.html', is_existing_admin=is_existing_admin)

        user = User(email=email, role='admin', is_verified=True, is_active=True)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        actor_id = current_user.id if current_user.is_authenticated else user.id
        db.session.add(AuditLog(
            user_id=actor_id,
            action='ADMIN_REGISTER',
            resource_type='User',
            resource_id=user.id,
            details=f'Administrator account registered: {email}',
            ip_address=request.remote_addr or '127.0.0.1'
        ))
        db.session.commit()

        flash('Administrator account created successfully! Please sign in.', 'success')
        return redirect(url_for('admin.login'))

    return render_template('admin_register.html', is_existing_admin=is_existing_admin)

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
