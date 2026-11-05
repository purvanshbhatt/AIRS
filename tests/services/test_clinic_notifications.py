import pytest
from app.services.clinic_engine.notifications import NotificationService, EmailNotificationProvider
from app.services.clinic_engine.morning_check import MorningCheck

def test_notification_service():
    service = NotificationService()
    email_provider = EmailNotificationProvider()
    service.register_provider(email_provider)
    
    check = MorningCheck(
        id="test",
        date="2023-10-27",
        status="SAFE",
        moments=[],
        generated_at="2023-10-27T00:00:00Z"
    )
    
    # Should not raise any exceptions
    service.notify_all("doctor@clinic.com", check)
