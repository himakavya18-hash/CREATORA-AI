from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from models import db, Message, User, Project
from services import NotificationService

messaging_bp = Blueprint('messaging', __name__)

@messaging_bp.route('/messages')
@login_required
def inbox():
    # Find distinct users that current user has exchanged messages with
    sent = db.session.query(Message.receiver_id).filter_by(sender_id=current_user.id)
    recv = db.session.query(Message.sender_id).filter_by(receiver_id=current_user.id)
    contact_ids = set([r[0] for r in sent.union(recv).all()])

    contacts = User.query.filter(User.id.in_(contact_ids)).all() if contact_ids else []

    # Get latest message per contact
    conversations = []
    for c in contacts:
        latest = Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.receiver_id == c.id)) |
            ((Message.sender_id == c.id) & (Message.receiver_id == current_user.id))
        ).order_by(Message.created_at.desc()).first()
        unread_count = Message.query.filter_by(sender_id=c.id, receiver_id=current_user.id, is_read=False).count()
        conversations.append({
            'contact': c,
            'latest_message': latest,
            'unread_count': unread_count
        })

    conversations.sort(key=lambda x: x['latest_message'].created_at if x['latest_message'] else datetime.min, reverse=True)

    return render_template('messages_inbox.html', conversations=conversations, active_contact=None, messages=[])

@messaging_bp.route('/messages/<int:other_user_id>')
@login_required
def conversation(other_user_id):
    if other_user_id == current_user.id:
        return redirect(url_for('messaging.inbox'))

    other_user = User.query.get_or_404(other_user_id)

    # Mark incoming messages as read
    Message.query.filter_by(sender_id=other_user.id, receiver_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()

    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == other_user.id)) |
        ((Message.sender_id == other_user.id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at.asc()).all()

    # Recompute conversations list
    sent = db.session.query(Message.receiver_id).filter_by(sender_id=current_user.id)
    recv = db.session.query(Message.sender_id).filter_by(receiver_id=current_user.id)
    contact_ids = set([r[0] for r in sent.union(recv).all()])
    contact_ids.add(other_user.id)

    contacts = User.query.filter(User.id.in_(contact_ids)).all()
    conversations = []
    for c in contacts:
        latest = Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.receiver_id == c.id)) |
            ((Message.sender_id == c.id) & (Message.receiver_id == current_user.id))
        ).order_by(Message.created_at.desc()).first()
        unread_count = Message.query.filter_by(sender_id=c.id, receiver_id=current_user.id, is_read=False).count()
        conversations.append({
            'contact': c,
            'latest_message': latest,
            'unread_count': unread_count
        })
    conversations.sort(key=lambda x: x['latest_message'].created_at if x['latest_message'] else datetime.min, reverse=True)

    project_id = request.args.get('project_id', type=int)

    return render_template('messages_inbox.html',
                           conversations=conversations,
                           active_contact=other_user,
                           messages=messages,
                           project_id=project_id)

@messaging_bp.route('/messages/send', methods=['POST'])
@login_required
def send_message():
    receiver_id = request.form.get('receiver_id', type=int)
    content = request.form.get('content', '').strip()
    project_id = request.form.get('project_id', type=int)

    if not receiver_id or not content:
        flash('Message cannot be empty.', 'warning')
        return redirect(request.referrer or url_for('messaging.inbox'))

    msg = Message(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        project_id=project_id,
        content=content
    )
    db.session.add(msg)
    db.session.commit()

    # Notify recipient
    sender_name = current_user.creator_profile.display_name if current_user.is_creator else (current_user.brand_profile.company_name if current_user.is_brand else current_user.email)
    NotificationService.send_notification(
        user_id=receiver_id,
        title=f"New Message from {sender_name}",
        message=f"{content[:80]}...",
        link=url_for('messaging.conversation', other_user_id=current_user.id),
        notification_type='message'
    )

    return redirect(request.referrer or url_for('messaging.conversation', other_user_id=receiver_id))
