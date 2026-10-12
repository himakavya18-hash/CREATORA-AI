from functools import wraps
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, CreatorProfile, BrandProfile, Report, AuditLog, CreativeBrief, PortfolioItem
from services import NotificationService

auth_bp = Blueprint('auth', __name__)

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            if current_user.role not in allowed_roles and not current_user.is_admin:
                flash('You do not have permission to access that resource.', 'danger')
                return redirect(url_for('auth.home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def creator_required(f):
    return role_required('creator')(f)

def brand_required(f):
    return role_required('brand')(f)

def admin_required(f):
    return role_required('admin')(f)

# Landing Page
@auth_bp.route('/')
def home():
    if current_user.is_authenticated:
        if current_user.is_creator:
            return redirect(url_for('creator.dashboard'))
        elif current_user.is_brand:
            return redirect(url_for('brand.dashboard'))
        elif current_user.is_admin:
            return redirect(url_for('admin.dashboard'))

    # Public landing page showcase metrics & featured items
    creators_count = CreatorProfile.query.count()
    briefs_count = CreativeBrief.query.filter_by(status='Published').count()
    portfolio_count = PortfolioItem.query.filter_by(is_public=True).count()
    featured_creators = CreatorProfile.query.limit(4).all()
    recent_briefs = CreativeBrief.query.filter_by(status='Published').order_by(CreativeBrief.created_at.desc()).limit(3).all()

    return render_template('index.html',
                           creators_count=creators_count,
                           briefs_count=briefs_count,
                           portfolio_count=portfolio_count,
                           featured_creators=featured_creators,
                           recent_briefs=recent_briefs)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('auth.home'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'creator').strip().lower()
        display_name = request.form.get('display_name', '').strip()
        company_name = request.form.get('company_name', '').strip()

        # Validation
        if not email or '@' not in email:
            flash('Please provide a valid email address.', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        if role not in ['creator', 'brand']:
            flash('Invalid account role specified.', 'danger')
            return render_template('register.html')

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('An account with this email already exists. Please log in.', 'warning')
            return redirect(url_for('auth.login'))

        # Create user
        user = User(email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        if role == 'creator':
            c_name = display_name if display_name else email.split('@')[0].capitalize()
            profile = CreatorProfile(
                user_id=user.id,
                display_name=c_name,
                headline='AI Content Creator & Prompt Engineer',
                bio='Passionate about generative AI pipelines, photorealistic image synthesis, and AI video production.'
            )
            db.session.add(profile)
        elif role == 'brand':
            b_name = company_name if company_name else f"{email.split('@')[0].capitalize()} Media"
            profile = BrandProfile(
                user_id=user.id,
                company_name=b_name,
                description='Forward-thinking brand commissioning AI creative campaigns.'
            )
            db.session.add(profile)

        # Audit log
        log = AuditLog(
            user_id=user.id,
            action='USER_REGISTER',
            resource_type='User',
            resource_id=user.id,
            details=f"New {role} account registered: {email}",
            ip_address=request.remote_addr or '127.0.0.1'
        )
        db.session.add(log)
        db.session.commit()

        # Welcome notification
        NotificationService.send_notification(
            user.id,
            'Welcome to Creatora AI!',
            'Your account has been created. Start by setting up your profile details.',
            link=url_for('creator.edit_profile' if role == 'creator' else 'brand.edit_profile'),
            notification_type='system'
        )

        login_user(user)
        flash('Registration successful! Welcome to Creatora AI.', 'success')

        if role == 'creator':
            return redirect(url_for('creator.dashboard'))
        else:
            return redirect(url_for('brand.dashboard'))

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.home'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('login.html')

        if not user.is_active:
            flash('This account has been suspended. Please contact platform administration.', 'danger')
            return render_template('login.html')

        user.last_login = datetime.utcnow()
        db.session.commit()

        login_user(user, remember=remember)

        # Audit log
        log = AuditLog(
            user_id=user.id,
            action='USER_LOGIN',
            resource_type='User',
            resource_id=user.id,
            details=f"User logged in from {request.remote_addr}",
            ip_address=request.remote_addr or '127.0.0.1'
        )
        db.session.add(log)
        db.session.commit()

        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)

        if user.is_creator:
            return redirect(url_for('creator.dashboard'))
        elif user.is_brand:
            return redirect(url_for('brand.dashboard'))
        elif user.is_admin:
            return redirect(url_for('admin.dashboard'))

        return redirect(url_for('auth.home'))

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.home'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()
        # For security, always show success message even if email doesn't exist
        flash('If that email exists in our system, password reset instructions have been dispatched.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('forgot_password.html')

@auth_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'change_password':
            old_pass = request.form.get('old_password')
            new_pass = request.form.get('new_password')
            confirm_pass = request.form.get('confirm_password')

            if not current_user.check_password(old_pass):
                flash('Current password is incorrect.', 'danger')
            elif len(new_pass) < 6:
                flash('New password must be at least 6 characters long.', 'danger')
            elif new_pass != confirm_pass:
                flash('New passwords do not match.', 'danger')
            else:
                current_user.set_password(new_pass)
                db.session.commit()
                flash('Password updated successfully.', 'success')

        elif action == 'update_email':
            new_email = request.form.get('email', '').strip().lower()
            if not new_email or '@' not in new_email:
                flash('Invalid email address.', 'danger')
            else:
                existing = User.query.filter_by(email=new_email).first()
                if existing and existing.id != current_user.id:
                    flash('That email is already registered to another account.', 'danger')
                else:
                    current_user.email = new_email
                    db.session.commit()
                    flash('Email updated successfully.', 'success')

        return redirect(url_for('auth.settings'))

    return render_template('settings.html')

@auth_bp.route('/settings/delete-account', methods=['POST'])
@login_required
def delete_account():
    user = current_user
    logout_user()
    db.session.delete(user)
    db.session.commit()
    flash('Your account and associated data have been permanently deleted.', 'info')
    return redirect(url_for('auth.home'))

@auth_bp.route('/report', methods=['POST'])
@login_required
def submit_report():
    target_type = request.form.get('target_type')
    target_id = request.form.get('target_id', type=int)
    reason = request.form.get('reason')
    details = request.form.get('details', '')
    reported_user_id = request.form.get('reported_user_id', type=int)

    if not target_type or not target_id or not reason:
        flash('Incomplete report submission.', 'danger')
        return redirect(request.referrer or url_for('auth.home'))

    report = Report(
        reporter_user_id=current_user.id,
        reported_user_id=reported_user_id,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        details=details
    )
    db.session.add(report)
    db.session.commit()

    flash('Thank you. Your report has been submitted to platform administrators for review.', 'success')
    return redirect(request.referrer or url_for('auth.home'))
