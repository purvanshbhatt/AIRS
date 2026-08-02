from abc import ABC, abstractmethod
from typing import List
from app.services.clinic_engine.morning_check import MorningCheck

class NotificationProvider(ABC):
    @abstractmethod
    def send_morning_check(self, target: str, check: MorningCheck) -> bool:
        pass

class EmailNotificationProvider(NotificationProvider):
    def send_morning_check(self, target: str, check: MorningCheck) -> bool:
        # MVP Mock implementation
        print(f"[EMAIL] Sending to {target}: Morning Check Status [{check.status}] with {len(check.moments)} moments.")
        return True

class NotificationService:
    def __init__(self):
        self.providers: List[NotificationProvider] = []
    
    def register_provider(self, provider: NotificationProvider):
        self.providers.append(provider)
        
    def notify_all(self, target: str, check: MorningCheck):
        for provider in self.providers:
            provider.send_morning_check(target, check)
