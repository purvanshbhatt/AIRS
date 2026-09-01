from typing import List
from app.services.clinic_engine.v2.schema import Evidence, EvidenceKind, RawEvent
from .base import EvidenceProvider

class MicrosoftProvider(EvidenceProvider):
    @classmethod
    def connector_type(cls) -> str:
        return 'microsoft'
    
    @classmethod
    def provides(cls) -> List[EvidenceKind]:
        return [
            EvidenceKind.USER_ACCOUNT_STATUS,
            EvidenceKind.DEVICE_SECURITY_STATUS,
            EvidenceKind.SECURITY_ALERT
        ]
    
    @classmethod
    def extract(cls, events: List[RawEvent]) -> List[Evidence]:
        evidences = []
        for event in events:
            if event.event_type != 'microsoft.telemetry':
                continue
                
            payload = event.payload
            org_id = event.organization_id
            
            for user in payload.get('entra_users', []):
                # Map fields for capability consumption
                mapped_user = dict(user)
                if 'user_principal_name' in user and 'display_name' not in user:
                    mapped_user['display_name'] = user['user_principal_name']
                if 'account_enabled' not in user:
                    mapped_user['account_enabled'] = True
                    
                evidences.append(Evidence(
                    kind=EvidenceKind.USER_ACCOUNT_STATUS,
                    source_connector=cls.connector_type(),
                    source_id=user.get('user_id'),
                    organization_id=org_id,
                    payload=mapped_user
                ))
                
            for device in payload.get('intune_devices', []):
                mapped_device = dict(device)
                if 'bitlocker_status' in device:
                    mapped_device['is_encrypted'] = device['bitlocker_status'] == 'encrypted'
                    
                evidences.append(Evidence(
                    kind=EvidenceKind.DEVICE_SECURITY_STATUS,
                    source_connector=cls.connector_type(),
                    source_id=device.get('device_id'),
                    organization_id=org_id,
                    payload=mapped_device
                ))
                
            for alert in payload.get('defender_alerts', []):
                evidences.append(Evidence(
                    kind=EvidenceKind.SECURITY_ALERT,
                    source_connector=cls.connector_type(),
                    source_id=alert.get('alert_id'),
                    organization_id=org_id,
                    payload=alert
                ))
                
        return evidences
