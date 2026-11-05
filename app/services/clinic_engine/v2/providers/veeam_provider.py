from typing import List

from app.connectors.base import NormalizedEvent
from app.services.clinic_engine.v2.schema import Evidence, EvidenceKind
from .base import EvidenceProvider

class VeeamProvider(EvidenceProvider):
    @classmethod
    def connector_type(cls) -> str:
        return 'veeam'
    
    @classmethod
    def provides(cls) -> List[EvidenceKind]:
        return [EvidenceKind.BACKUP_STATUS]
    
    @classmethod
    def extract(cls, events: List[NormalizedEvent]) -> List[Evidence]:
        evidences = []
        for event in events:
            if event.event_type == 'veeam.backup_job':
                payload = event.payload
                evidences.append(Evidence(
                    kind=EvidenceKind.BACKUP_STATUS,
                    source_connector=cls.connector_type(),
                    source_id=event.source_event_id,
                    organization_id=event.organization_id,
                    payload={
                        'system_name': payload.get('system_name'),
                        'last_successful_backup': payload.get('last_successful_backup'),
                        'backup_type': payload.get('backup_type')
                    }
                ))
        return evidences
