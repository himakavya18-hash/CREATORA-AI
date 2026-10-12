from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Notification
from services import NotificationService

notif_bp = Blueprint('notification', __name__)

@notif_bp.route('/notifications')
@login_required
def list_notifications():
    notifications = NotificationService.get_user_notifications(current_user.id, limit=50)
    return render_template('notifications.html', notifications=notifications)

@notif_bp.route('/notifications/read/<int:notif_id>', methods=['POST'])
@login_required
def mark_read(notif_id):
    notif = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first_or_404()
    notif.is_read = True
    db.session.commit()
    return jsonify({'success': True})

@notif_bp.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_read():
    NotificationService.mark_all_read(current_user.id)
    flash('All notifications marked as read.', 'info')
    return redirect(url_for('notification.list_notifications'))
