from typing import List
from app.services.clinic_engine.v2.schema import Evidence, EvidenceKind, RawEvent
from .base import EvidenceProvider

class WazuhProvider(EvidenceProvider):
    @classmethod
    def connector_type(cls) -> str:
        return 'wazuh'
    
    @classmethod
    def provides(cls) -> List[EvidenceKind]:
        return [
            EvidenceKind.DEVICE_SECURITY_STATUS,
            EvidenceKind.VULNERABILITY_SCAN,
            EvidenceKind.SECURITY_ALERT
        ]
    
    @classmethod
    def extract(cls, events: List[RawEvent]) -> List[Evidence]:
        evidences = []
        
        for event in events:
            payload = event.payload
            org_id = event.organization_id
            
            if event.event_type == 'wazuh.agent_status':
                agent_id = payload.get('agent_id')
                evidences.append(Evidence(
                    kind=EvidenceKind.DEVICE_SECURITY_STATUS,
                    source_connector=cls.connector_type(),
                    source_id=agent_id,
                    organization_id=org_id,
                    payload={
                        'device_id': agent_id,
                        'device_name': payload.get('name'),
                        'status': payload.get('status'),
                        'os': payload.get('os'),
                        'agent_version': payload.get('version')
                    }
                ))
                
            elif event.event_type == 'wazuh.vulnerability':
                agent_id = payload.get('agent_id')
                cve = payload.get('cve')
                source_id = f"{agent_id}_{cve}" if agent_id and cve else None
                evidences.append(Evidence(
                    kind=EvidenceKind.VULNERABILITY_SCAN,
                    source_connector=cls.connector_type(),
                    source_id=source_id,
                    organization_id=org_id,
                    payload={
                        'device_id': agent_id,
                        'cve': cve,
                        'vulnerability_name': payload.get('name'),
                        'severity': payload.get('severity'),
                        'affected_version': payload.get('version')
                    }
                ))
                
            elif event.event_type == 'wazuh.alert':
                alert_id = payload.get('alert_id')
                evidences.append(Evidence(
                    kind=EvidenceKind.SECURITY_ALERT,
                    source_connector=cls.connector_type(),
                    source_id=alert_id,
                    organization_id=org_id,
                    payload={
                        'alert_id': alert_id,
                        'title': payload.get('title') or payload.get('description'),
                        'severity': payload.get('severity'),
                        'rule_id': payload.get('rule_id'),
                        'device_id': payload.get('device_id') or payload.get('agent_id')
                    }
                ))
                
        return evidences
