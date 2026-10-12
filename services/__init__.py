# Services module initialization
from services.ai_service import AIService
from services.matching_service import MatchingService
from services.licensing_service import LicensingService
from services.verification_service import VerificationService
from services.notification_service import NotificationService
from services.portfolio_service import PortfolioService

__all__ = [
    'AIService',
    'MatchingService',
    'LicensingService',
    'VerificationService',
    'NotificationService',
    'PortfolioService'
]
