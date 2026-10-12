from datetime import datetime
from models import db, VerificationRecord, CreatorProfile, AuditLog

class VerificationService:
    @classmethod
    def submit_verification_request(cls, creator_id, evidence_links, workflow_info, references='', docs=''):
        """Creates or updates a creator verification submission."""
        record = VerificationRecord.query.filter_by(creator_id=creator_id).order_by(VerificationRecord.id.desc()).first()
        
        if not record or record.status in ['Rejected', 'Additional Evidence Required', 'Not Submitted']:
            record = VerificationRecord(
                creator_id=creator_id,
                portfolio_evidence_links=evidence_links,
                tools_workflow_info=workflow_info,
                past_references=references,
                supporting_documents=docs,
                status='Pending Review'
            )
            db.session.add(record)
        else:
            # Update existing pending record
            record.portfolio_evidence_links = evidence_links
            record.tools_workflow_info = workflow_info
            record.past_references = references
            record.supporting_documents = docs
            record.status = 'Pending Review'
            record.updated_at = datetime.utcnow()

        # Update profile status
        creator = CreatorProfile.query.get(creator_id)
        if creator:
            creator.verification_status = 'Pending Review'

        db.session.commit()
        return record

    @classmethod
    def review_verification(cls, record_id, reviewer_user, new_status, notes=''):
        """Administrator reviews a creator's verification request."""
        record = VerificationRecord.query.get_or_404(record_id)
        record.status = new_status
        record.reviewer_id = reviewer_user.id
        record.reviewer_notes = notes
        record.reviewed_at = datetime.utcnow()
        record.updated_at = datetime.utcnow()

        creator = CreatorProfile.query.get(record.creator_id)
        if creator:
            creator.verification_status = new_status
            if new_status == 'Verified' and creator.user:
                creator.user.is_verified = True
            elif new_status != 'Verified' and creator.user:
                creator.user.is_verified = False

        # Add audit log
        log = AuditLog(
            user_id=reviewer_user.id,
            action=f"CREATOR_VERIFICATION_{new_status.upper().replace(' ', '_')}",
            resource_type='CreatorProfile',
            resource_id=record.creator_id,
            details=f"Admin {reviewer_user.email} changed verification to {new_status}. Notes: {notes}"
        )
        db.session.add(log)
        db.session.commit()
        return record
