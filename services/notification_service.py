from datetime import datetime
from models import db, Notification

class NotificationService:
    @classmethod
    def send_notification(cls, user_id, title, message, link='#', notification_type='system'):
        """Creates an in-app notification for a user."""
        try:
            notif = Notification(
                user_id=user_id,
                title=title,
                message=message,
                link=link,
                notification_type=notification_type,
                is_read=False,
                created_at=datetime.utcnow()
            )
            db.session.add(notif)
            db.session.commit()
            return notif
        except Exception as e:
            db.session.rollback()
            return None

    @classmethod
    def mark_all_read(cls, user_id):
        Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
        db.session.commit()

    @classmethod
    def get_user_notifications(cls, user_id, limit=30):
        return Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).limit(limit).all()
