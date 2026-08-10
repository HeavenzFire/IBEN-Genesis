#!/usr/bin/env python3
"""
================================================================================
SOVEREIGN ENFORCEMENT CORTEX - OPERATIONAL PIPELINE
================================================================================

A closed-loop accountability system for public records request enforcement.

Architecture:
  - LEDGER: Immutable memory of all requests and agency responses
  - ESCALATION LOG: Cryptographically-linked enforcement entries  
  - TRIGGER ENGINE: Autonomic reflex for statutory compliance monitoring

Statutory Framework:
  - 10 business day response threshold (FOIA + state equivalents)
  - Automatic presumption of public status after deadline
  - Mandatory AG/OIG escalation upon non-compliance

================================================================================
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import hmac
import os

# ============================================================================
# CONSTANTS & CONFIGURATION
# ============================================================================

class EscalationStatus(Enum):
    NONE = "None"
    OVERDUE_NOTICE = "Overdue Notice Issued"
    AG_COMPLAINT_FILED = "AG Complaint Filed"
    OIG_REFERRAL = "OIG Referral Made"
    JUDICIAL_REVIEW = "Judicial Review Petitioned"

class RequestStatus(Enum):
    PENDING = "Pending"
    PARTIAL_RESPONSE = "Partial Response Received"
    COMPLETE = "Complete"
    DENIED = "Denied"
    PRESUMED_PUBLIC = "Presumed Public (Deadline Expired)"

# Business holidays (example - should be populated per jurisdiction)
FEDERAL_HOLIDAYS_2024 = [
    datetime(2024, 1, 1),   # New Year's Day
    datetime(2024, 1, 15),  # MLK Day
    datetime(2024, 2, 19),  # Presidents Day
    datetime(2024, 5, 27),  # Memorial Day
    datetime(2024, 6, 19),  # Juneteenth
    datetime(2024, 7, 4),   # Independence Day
    datetime(2024, 9, 2),   # Labor Day
    datetime(2024, 10, 14), # Columbus Day
    datetime(2024, 11, 11), # Veterans Day
    datetime(2024, 11, 28), # Thanksgiving
    datetime(2024, 12, 25), # Christmas
]

RESPONSE_DEADLINE_DAYS = 10  # Business days


# ============================================================================
# BUSINESS DAY CALCULATOR
# ============================================================================

class BusinessDayCalculator:
    """
    Calculates business days excluding weekends and federal holidays.
    Ensures compliance checks align with statutory interpretations.
    """
    
    def __init__(self, holidays: List[datetime] = None):
        self.holidays = set(holidays) if holidays else set(FEDERAL_HOLIDAYS_2024)
    
    def is_business_day(self, date: datetime) -> bool:
        """Check if a date is a business day."""
        # Weekend check
        if date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        # Holiday check
        if date.date() in [h.date() for h in self.holidays]:
            return False
        return True
    
    def add_business_days(self, start_date: datetime, days: int) -> datetime:
        """Add N business days to a start date."""
        current = start_date
        added = 0
        while added < days:
            current += timedelta(days=1)
            if self.is_business_day(current):
                added += 1
        return current
    
    def count_business_days(self, start_date: datetime, end_date: datetime) -> int:
        """Count business days between two dates (exclusive of start, inclusive of end)."""
        if end_date <= start_date:
            return 0
        
        count = 0
        current = start_date + timedelta(days=1)
        while current <= end_date:
            if self.is_business_day(current):
                count += 1
            current += timedelta(days=1)
        return count
    
    def days_until_deadline(self, filed_date: datetime, current_date: datetime = None) -> int:
        """Calculate remaining business days until response deadline."""
        if current_date is None:
            current_date = datetime.now()
        
        deadline = self.add_business_days(filed_date, RESPONSE_DEADLINE_DAYS)
        return self.count_business_days(current_date, deadline)
    
    def is_overdue(self, filed_date: datetime, current_date: datetime = None) -> bool:
        """Check if the response deadline has passed."""
        if current_date is None:
            current_date = datetime.now()
        
        business_days_elapsed = self.count_business_days(filed_date, current_date)
        return business_days_elapsed > RESPONSE_DEADLINE_DAYS


# ============================================================================
# CRYPTOGRAPHIC UTILITIES
# ============================================================================

class CryptoSealer:
    """
    Provides cryptographic sealing for immutable audit trail.
    Each entry is cryptographically tied to the master ledger.
    """
    
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or os.urandom(32).hex()
    
    def compute_hash(self, data: str) -> str:
        """Compute SHA-256 hash of data."""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    def compute_hmac(self, data: str) -> str:
        """Compute HMAC-SHA256 of data."""
        return hmac.new(
            self.secret_key.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def seal_entry(self, entry_data: dict, previous_hash: str = "GENESIS") -> dict:
        """
        Seal an entry with cryptographic links to maintain chain of custody.
        
        Returns the sealed entry with:
          - timestamp
          - content_hash (hash of entry contents)
          - previous_hash (link to previous entry)
          - chain_hash (cumulative hash ensuring immutability)
          - signature (HMAC for authenticity)
        """
        timestamp = datetime.now().isoformat()
        
        # Create canonical JSON representation
        entry_copy = entry_data.copy()
        entry_copy['timestamp'] = timestamp
        entry_copy['previous_hash'] = previous_hash
        
        # Compute content hash
        content_json = json.dumps(entry_copy, sort_keys=True)
        content_hash = self.compute_hash(content_json)
        
        # Compute chain hash (includes previous hash for linking)
        chain_input = f"{previous_hash}:{content_hash}:{timestamp}"
        chain_hash = self.compute_hash(chain_input)
        
        # Compute signature
        signature_input = f"{content_hash}:{chain_hash}"
        signature = self.compute_hmac(signature_input)
        
        # Return sealed entry
        sealed = entry_copy.copy()
        sealed['content_hash'] = content_hash
        sealed['chain_hash'] = chain_hash
        sealed['signature'] = signature
        
        return sealed
    
    def verify_chain(self, entries: List[dict]) -> Tuple[bool, Optional[int]]:
        """
        Verify the integrity of a chain of entries.
        
        Returns (is_valid, first_invalid_index)
        """
        if not entries:
            return True, None
        
        previous_hash = "GENESIS"
        
        for i, entry in enumerate(entries):
            # Recompute expected values
            entry_copy = {k: v for k, v in entry.items() 
                         if k not in ['content_hash', 'chain_hash', 'signature']}
            entry_copy['previous_hash'] = previous_hash
            entry_copy['timestamp'] = entry['timestamp']
            
            content_json = json.dumps(entry_copy, sort_keys=True)
            expected_content_hash = self.compute_hash(content_json)
            
            chain_input = f"{previous_hash}:{expected_content_hash}:{entry['timestamp']}"
            expected_chain_hash = self.compute_hash(chain_input)
            
            signature_input = f"{expected_content_hash}:{expected_chain_hash}"
            expected_signature = self.compute_hmac(signature_input)
            
            # Verify
            if entry.get('content_hash') != expected_content_hash:
                return False, i
            if entry.get('chain_hash') != expected_chain_hash:
                return False, i
            if entry.get('signature') != expected_signature:
                return False, i
            
            previous_hash = entry['chain_hash']
        
        return True, None


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class PublicRecordsRequest:
    """Represents a single public records request."""
    request_id: str
    agency_name: str
    agency_contact: str
    request_description: str
    filed_date: datetime
    requester_name: str
    statutory_basis: str = "FOIA / State Public Records Act"
    status: RequestStatus = RequestStatus.PENDING
    escalation_status: EscalationStatus = EscalationStatus.NONE
    response_received: Optional[datetime] = None
    response_content: Optional[str] = None
    notes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['filed_date'] = self.filed_date.isoformat()
        d['response_received'] = self.response_received.isoformat() if self.response_received else None
        d['status'] = self.status.value
        d['escalation_status'] = self.escalation_status.value
        return d


@dataclass
class EscalationEntry:
    """Represents an enforcement escalation action."""
    escalation_id: str
    request_id: str
    escalation_type: EscalationStatus
    triggered_date: datetime
    statutory_citation: str
    days_overdue: int
    agency_name: str
    description: str
    legal_presumption: str = "Information legally presumed public under statutory deadline expiration"
    next_action: str = ""
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['triggered_date'] = self.triggered_date.isoformat()
        d['escalation_type'] = self.escalation_type.value
        return d


# ============================================================================
# MASTER LEDGER
# ============================================================================

class MasterLedger:
    """
    Immutable ledger capturing all public records requests and their lifecycle.
    Acts as the system's memory - every interaction is permanently recorded.
    """
    
    def __init__(self, crypto_sealer: CryptoSealer = None):
        self.sealer = crypto_sealer or CryptoSealer()
        self.requests: Dict[str, PublicRecordsRequest] = {}
        self.ledger_entries: List[dict] = []
        self.current_chain_hash = "GENESIS"
    
    def add_request(self, request: PublicRecordsRequest) -> dict:
        """Add a new request to the ledger."""
        self.requests[request.request_id] = request
        
        # Create ledger entry
        entry_data = {
            'action': 'REQUEST_FILED',
            'request': request.to_dict()
        }
        
        sealed_entry = self.sealer.seal_entry(entry_data, self.current_chain_hash)
        self.ledger_entries.append(sealed_entry)
        self.current_chain_hash = sealed_entry['chain_hash']
        
        return sealed_entry
    
    def update_request_status(self, request_id: str, 
                             new_status: RequestStatus = None,
                             escalation_status: EscalationStatus = None,
                             response_content: str = None,
                             notes: str = None) -> dict:
        """Update a request's status and record in ledger."""
        if request_id not in self.requests:
            raise ValueError(f"Request {request_id} not found in ledger")
        
        request = self.requests[request_id]
        
        if new_status:
            request.status = new_status
        if escalation_status:
            request.escalation_status = escalation_status
        if response_content:
            request.response_content = response_content
            request.response_received = datetime.now()
        if notes:
            request.notes.append(notes)
        
        # Record update in ledger
        entry_data = {
            'action': 'REQUEST_UPDATED',
            'request_id': request_id,
            'updates': {
                'status': new_status.value if new_status else None,
                'escalation_status': escalation_status.value if escalation_status else None,
            },
            'notes': notes
        }
        
        sealed_entry = self.sealer.seal_entry(entry_data, self.current_chain_hash)
        self.ledger_entries.append(sealed_entry)
        self.current_chain_hash = sealed_entry['chain_hash']
        
        return sealed_entry
    
    def get_request(self, request_id: str) -> Optional[PublicRecordsRequest]:
        """Retrieve a request from the ledger."""
        return self.requests.get(request_id)
    
    def get_pending_requests(self) -> List[PublicRecordsRequest]:
        """Get all requests that are still pending or overdue."""
        return [r for r in self.requests.values() 
                if r.status in [RequestStatus.PENDING, RequestStatus.PARTIAL_RESPONSE]]
    
    def verify_integrity(self) -> Tuple[bool, Optional[int]]:
        """Verify the cryptographic integrity of the entire ledger."""
        return self.sealer.verify_chain(self.ledger_entries)
    
    def export_audit_trail(self) -> str:
        """Export the complete audit trail as JSON."""
        return json.dumps({
            'export_timestamp': datetime.now().isoformat(),
            'total_entries': len(self.ledger_entries),
            'current_chain_hash': self.current_chain_hash,
            'entries': self.ledger_entries
        }, indent=2)


# ============================================================================
# ESCALATION LOG
# ============================================================================

class EscalationLog:
    """
    Immutable log of all enforcement escalations.
    Each entry is cryptographically linked to the master ledger.
    Documents statutory citations and legal presumptions.
    """
    
    def __init__(self, master_ledger: MasterLedger, crypto_sealer: CryptoSealer = None):
        self.master_ledger = master_ledger
        self.sealer = crypto_sealer or CryptoSealer()
        self.escalations: Dict[str, EscalationEntry] = {}
        self.log_entries: List[dict] = []
        self.current_chain_hash = "GENESIS"
    
    def create_escalation(self, request: PublicRecordsRequest,
                         escalation_type: EscalationStatus,
                         statutory_citation: str,
                         description: str,
                         next_action: str = "") -> EscalationEntry:
        """Create a new escalation entry."""
        # Calculate days overdue
        calculator = BusinessDayCalculator()
        days_overdue = calculator.count_business_days(
            request.filed_date, datetime.now()
        ) - RESPONSE_DEADLINE_DAYS
        
        escalation_id = f"ESC-{request.request_id}-{escalation_type.value.replace(' ', '-').upper()}"
        
        entry = EscalationEntry(
            escalation_id=escalation_id,
            request_id=request.request_id,
            escalation_type=escalation_type,
            triggered_date=datetime.now(),
            statutory_citation=statutory_citation,
            days_overdue=max(0, days_overdue),
            agency_name=request.agency_name,
            description=description,
            legal_presumption="Information legally presumed public under statutory deadline expiration",
            next_action=next_action
        )
        
        self.escalations[escalation_id] = entry
        
        # Create log entry with link to master ledger
        # Find the most recent ledger entry for this request
        related_ledger_hash = "LEDGER_GENESIS"
        for ledger_entry in reversed(self.master_ledger.ledger_entries):
            if ledger_entry.get('request_id') == request.request_id or \
               (ledger_entry.get('request', {}).get('request_id') == request.request_id):
                related_ledger_hash = ledger_entry['chain_hash']
                break
        
        entry_data = {
            'action': 'ESCALATION_CREATED',
            'escalation': entry.to_dict(),
            'linked_ledger_hash': related_ledger_hash
        }
        
        sealed_entry = self.sealer.seal_entry(entry_data, self.current_chain_hash)
        self.log_entries.append(sealed_entry)
        self.current_chain_hash = sealed_entry['chain_hash']
        
        # Update the request in master ledger
        self.master_ledger.update_request_status(
            request.request_id,
            escalation_status=escalation_type,
            notes=f"Escalated: {escalation_type.value} - {description}"
        )
        
        return entry
    
    def get_escalations_for_request(self, request_id: str) -> List[EscalationEntry]:
        """Get all escalations for a specific request."""
        return [e for e in self.escalations.values() if e.request_id == request_id]
    
    def get_all_escalations(self) -> List[EscalationEntry]:
        """Get all escalation entries."""
        return list(self.escalations.values())
    
    def verify_integrity(self) -> Tuple[bool, Optional[int]]:
        """Verify the cryptographic integrity of the escalation log."""
        return self.sealer.verify_chain(self.log_entries)
    
    def export_enforcement_report(self) -> str:
        """Export complete enforcement report."""
        return json.dumps({
            'report_timestamp': datetime.now().isoformat(),
            'total_escalations': len(self.escalations),
            'current_chain_hash': self.current_chain_hash,
            'escalations': [e.to_dict() for e in self.escalations.values()],
            'log_entries': self.log_entries
        }, indent=2)


# ============================================================================
# TRIGGER ENGINE
# ============================================================================

class TriggerEngine:
    """
    Autonomic reflex system for statutory compliance monitoring.
    Automatically detects overdue requests and triggers escalations.
    
    Core Logic:
      1. Business Day Calculation - filters weekends/holidays
      2. 10-Day Threshold - agencies must respond or request AG ruling
      3. Automated Promotion - transitions escalation status automatically
      4. Immutable Enforcement - cryptographically links to ledger
    """
    
    def __init__(self, master_ledger: MasterLedger, escalation_log: EscalationLog):
        self.master_ledger = master_ledger
        self.escalation_log = escalation_log
        self.calculator = BusinessDayCalculator()
        
        # Statutory citations by jurisdiction
        self.statutory_citations = {
            'federal': "5 U.S.C. § 552(a)(6)(A) - FOIA 10-business-day requirement",
            'california': "Gov. Code § 6253(c) - CPRA 10-day response requirement",
            'new_york': "Public Officers Law § 89(4)(a) - FOIL 5-business-day requirement",
            'texas': "Gov. Code § 552.221(a) - PIA 10-business-day requirement",
            'florida': "F.S. § 119.07(1)(a) - Public Records Act prompt response",
        }
        
        # Escalation templates
        self.escalation_templates = {
            EscalationStatus.OVERDUE_NOTICE: {
                'citation': self.statutory_citations['federal'],
                'description': "Agency failed to respond within statutory 10-business-day period",
                'next_action': "Await response for 5 additional days before AG complaint"
            },
            EscalationStatus.AG_COMPLAINT_FILED: {
                'citation': "5 U.S.C. § 552(a)(4)(B) - FOIA judicial review; Agency-specific AG oversight statutes",
                'description': "Formal complaint filed with Attorney General's Office of Information Policy",
                'next_action': "Track AG response; prepare for OIG referral if unresolved in 30 days"
            },
            EscalationStatus.OIG_REFERRAL: {
                'citation': "Inspector General Act Amendments; Agency-specific IG empowerment statutes",
                'description': "Referral made to agency Office of Inspector General for investigation",
                'next_action': "Monitor IG investigation; prepare judicial petition if needed"
            },
            EscalationStatus.JUDICIAL_REVIEW: {
                'citation': "5 U.S.C. § 552(a)(4)(B) - FOIA civil action in district court",
                'description': "Petition for judicial review filed in U.S. District Court",
                'next_action': "Litigation proceedings"
            }
        }
    
    def check_compliance(self, request: PublicRecordsRequest, 
                        current_date: datetime = None) -> dict:
        """
        Check compliance status for a single request.
        
        Returns dict with:
          - is_compliant: bool
          - days_elapsed: int
          - days_remaining: int (negative if overdue)
          - deadline_date: datetime
          - recommended_action: str
        """
        if current_date is None:
            current_date = datetime.now()
        
        days_elapsed = self.calculator.count_business_days(
            request.filed_date, current_date
        )
        
        deadline_date = self.calculator.add_business_days(
            request.filed_date, RESPONSE_DEADLINE_DAYS
        )
        
        days_remaining = RESPONSE_DEADLINE_DAYS - days_elapsed
        
        is_compliant = days_elapsed <= RESPONSE_DEADLINE_DAYS
        
        if is_compliant and days_remaining <= 3:
            recommended_action = f"Follow up: {days_remaining} business days remaining"
        elif not is_compliant:
            if request.escalation_status == EscalationStatus.NONE:
                recommended_action = "IMMEDIATE: Issue overdue notice"
            elif request.escalation_status == EscalationStatus.OVERDUE_NOTICE:
                recommended_action = "IMMEDIATE: File AG complaint"
            else:
                recommended_action = f"Monitor: Current escalation in progress ({request.escalation_status.value})"
        else:
            recommended_action = "No action required"
        
        return {
            'request_id': request.request_id,
            'is_compliant': is_compliant,
            'days_elapsed': days_elapsed,
            'days_remaining': days_remaining,
            'deadline_date': deadline_date.isoformat(),
            'current_status': request.status.value,
            'escalation_status': request.escalation_status.value,
            'recommended_action': recommended_action
        }
    
    def run_compliance_scan(self, current_date: datetime = None) -> List[dict]:
        """
        Scan all pending requests for compliance violations.
        Returns list of compliance reports for each request.
        """
        reports = []
        pending_requests = self.master_ledger.get_pending_requests()
        
        for request in pending_requests:
            report = self.check_compliance(request, current_date)
            reports.append(report)
        
        return reports
    
    def execute_auto_escalation(self, request: PublicRecordsRequest,
                               current_date: datetime = None) -> Optional[EscalationEntry]:
        """
        Automatically escalate a request based on its overdue status.
        
        Escalation ladder:
          - Day 11+: OVERDUE_NOTICE
          - Day 16+: AG_COMPLAINT_FILED
          - Day 46+: OIG_REFERRAL
          - Day 76+: JUDICIAL_REVIEW
        
        Returns the created escalation entry, or None if no escalation needed.
        """
        if current_date is None:
            current_date = datetime.now()
        
        days_elapsed = self.calculator.count_business_days(
            request.filed_date, current_date
        )
        
        # Determine required escalation level
        target_escalation = None
        
        if days_elapsed > 75:
            target_escalation = EscalationStatus.JUDICIAL_REVIEW
        elif days_elapsed > 45:
            target_escalation = EscalationStatus.OIG_REFERRAL
        elif days_elapsed > 15:
            target_escalation = EscalationStatus.AG_COMPLAINT_FILED
        elif days_elapsed > RESPONSE_DEADLINE_DAYS:
            target_escalation = EscalationStatus.OVERDUE_NOTICE
        
        if not target_escalation:
            return None
        
        # Check if already at or beyond this level
        current_level = list(EscalationStatus).index(request.escalation_status)
        target_level = list(EscalationStatus).index(target_escalation)
        
        if current_level >= target_level:
            return None
        
        # Get escalation template
        template = self.escalation_templates[target_escalation]
        
        # Create escalation
        escalation = self.escalation_log.create_escalation(
            request=request,
            escalation_type=target_escalation,
            statutory_citation=template['citation'],
            description=template['description'],
            next_action=template['next_action']
        )
        
        return escalation
    
    def run_full_enforcement_cycle(self, current_date: datetime = None) -> dict:
        """
        Execute complete enforcement cycle:
          1. Scan all requests for compliance
          2. Auto-escalate all overdue requests
          3. Generate enforcement summary
        
        Returns summary report.
        """
        # Step 1: Compliance scan
        compliance_reports = self.run_compliance_scan(current_date)
        
        # Step 2: Auto-escalate
        escalations_created = []
        for request in self.master_ledger.get_pending_requests():
            escalation = self.execute_auto_escalation(request, current_date)
            if escalation:
                escalations_created.append(escalation)
        
        # Step 3: Summary
        overdue_count = sum(1 for r in compliance_reports if not r['is_compliant'])
        compliant_count = len(compliance_reports) - overdue_count
        
        return {
            'scan_timestamp': (current_date or datetime.now()).isoformat(),
            'total_requests_scanned': len(compliance_reports),
            'compliant_requests': compliant_count,
            'overdue_requests': overdue_count,
            'escalations_created': len(escalations_created),
            'escalation_details': [e.to_dict() for e in escalations_created],
            'system_integrity': {
                'ledger_valid': self.master_ledger.verify_integrity()[0],
                'escalation_log_valid': self.escalation_log.verify_integrity()[0]
            }
        }


# ============================================================================
# VISUALIZATION - Pipeline Diagram Generator
# ============================================================================

class PipelineDiagramGenerator:
    """
    Generates ASCII and structured diagrams showing the enforcement pipeline flow.
    """
    
    @staticmethod
    def generate_ascii_diagram() -> str:
        """Generate ASCII art diagram of the enforcement pipeline."""
        
        diagram = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    SOVEREIGN ENFORCEMENT CORTEX - PIPELINE                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                ║
║   │   REQUEST    │────▶│    MASTER    │────▶│   TRIGGER    │                ║
║   │    FILING    │     │    LEDGER    │     │    ENGINE    │                ║
║   │              │     │              │     │              │                ║
║   │ • Timestamp  │     │ • Immutable  │     │ • Business   │                ║
║   │ • Agency ID  │     │   Memory     │     │   Day Calc   │                ║
║   │ • Description│     │ • All Requests│    │ • 10-Day     │                ║
║   │ • Statutory  │     │ • Cryptographic│   │   Threshold  │                ║
║   │   Basis      │     │   Sealing    │     │ • Auto-Promo │                ║
║   └──────────────┘     └──────────────┘     └──────┬───────┘                ║
║                                                    │                         ║
║                                                    ▼                         ║
║                                            ┌──────────────┐                  ║
║                                            │  COMPLIANCE  │                  ║
║                                            │    CHECK     │                  ║
║                                            │              │                  ║
║                                            │ Days Elapsed │                  ║
║                                            │ vs Deadline  │                  ║
║                                            └──────┬───────┘                  ║
║                                                   │                          ║
║                     ┌─────────────────────────────┼─────────────────────┐    ║
║                     │                             │                     │    ║
║                     ▼                             ▼                     ▼    ║
║              ┌──────────────┐            ┌──────────────┐       ┌──────────────┐
║              │  COMPLIANT   │            │   OVERDUE    │       │  SEVERELY    │
║              │  (≤10 days)  │            │  (11-15 days)│       │  OVERDUE     │
║              │              │            │              │       │  (>15 days)  │
║              │ • No Action  │            │ • Overdue    │       │              │
║              │ • Monitor    │            │   Notice     │       │ • AG Complaint│
║              └──────────────┘            └──────┬───────┘       └──────┬───────┘
║                                                 │                      │       ║
║                                                 ▼                      ▼       ║
║                                        ┌─────────────────────────────────┐    ║
║                                        │      ESCALATION LOG             │    ║
║                                        │                                 │    ║
║                                        │ • Cryptographically Linked      │    ║
║                                        │ • Statutory Citations           │    ║
║                                        │ • Legal Presumptions            │    ║
║                                        │ • Immutable Chain               │    ║
║                                        └────────────┬────────────────────┘    ║
║                                                     │                          ║
║                    ┌────────────────────────────────┼────────────────────┐     ║
║                    │                                │                    │     ║
║                    ▼                                ▼                    ▼     ║
║           ┌─────────────────┐           ┌─────────────────┐  ┌─────────────────┐
║           │ AG COMPLAINT    │           │ OIG REFERRAL    │  │ JUDICIAL REVIEW │
║           │                 │           │                 │  │                 │
║           │ 5 U.S.C.        │           │ IG Act          │  │ 5 U.S.C.        │
║           │ § 552(a)(4)(B)  │           │ Amendments      │  │ § 552(a)(4)(B)  │
║           └─────────────────┘           └─────────────────┘  └─────────────────┘
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  SYSTEM PROPERTIES:                                                          ║
║  • LEDGER = Memory (immutable record of all requests)                        ║
║  • ESCALATION LOG = Enforcement (cryptographically-linked actions)           ║
║  • TRIGGER ENGINE = Autonomic Reflex (automatic compliance monitoring)       ║
║                                                                              ║
║  Together: A forensic mind that acts automatically, without hesitation.      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        return diagram
    
    @staticmethod
    def generate_mermaid_diagram() -> str:
        """Generate Mermaid.js diagram for documentation."""
        
        mermaid = """
flowchart TD
    subgraph Input["Request Intake"]
        A[Public Records Request Filed] --> B[Timestamp & Agency ID]
        B --> C[Statutory Basis Assigned]
    end
    
    subgraph Ledger["Master Ledger - Memory"]
        D[Cryptographic Sealing]
        E[Immutable Entry Created]
        F[Chain Hash Updated]
    end
    
    subgraph Trigger["Trigger Engine - Autonomic Reflex"]
        G[Business Day Calculator]
        H[Days Elapsed Counter]
        I{Compliance Check}
    end
    
    subgraph Escalation["Escalation Log - Enforcement"]
        J[Overdue Notice]
        K[AG Complaint Filed]
        L[OIG Referral]
        M[Judicial Review]
    end
    
    subgraph Statutes["Statutory Framework"]
        N[5 U.S.C. § 552 - FOIA]
        O[State Public Records Acts]
        P[Inspector General Acts]
    end
    
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
    
    I -->|≤10 days| Monitor[Monitor - No Action]
    I -->|11-15 days| J
    I -->|16-45 days| K
    I -->|46-75 days| L
    I -->|>75 days| M
    
    J --> N
    K --> N
    L --> P
    M --> N
    
    style Ledger fill:#e1f5fe
    style Trigger fill:#fff3e0
    style Escalation fill:#fce4ec
    style Statutes fill:#f3e5f5
"""
        return mermaid
    
    @staticmethod
    def generate_structured_flow() -> dict:
        """Generate structured flow data for programmatic use."""
        
        return {
            "pipeline_name": "Sovereign Enforcement Cortex",
            "version": "1.0.0",
            "stages": [
                {
                    "stage_id": 1,
                    "name": "Request Filing",
                    "type": "input",
                    "actions": [
                        "Capture request metadata",
                        "Assign unique request ID",
                        "Record statutory basis",
                        "Timestamp filing"
                    ],
                    "outputs": ["PublicRecordsRequest object"]
                },
                {
                    "stage_id": 2,
                    "name": "Master Ledger",
                    "type": "storage",
                    "properties": ["immutable", "cryptographically_sealed", "append_only"],
                    "actions": [
                        "Compute content hash",
                        "Link to previous chain hash",
                        "Generate HMAC signature",
                        "Store sealed entry"
                    ],
                    "outputs": ["Sealed ledger entry", "Updated chain hash"]
                },
                {
                    "stage_id": 3,
                    "name": "Trigger Engine",
                    "type": "processor",
                    "properties": ["automated", "continuous", "business_day_aware"],
                    "actions": [
                        "Calculate business days elapsed",
                        "Compare against 10-day threshold",
                        "Determine compliance status",
                        "Select appropriate escalation level"
                    ],
                    "decision_logic": {
                        "compliant": "days_elapsed <= 10",
                        "overdue_notice": "10 < days_elapsed <= 15",
                        "ag_complaint": "15 < days_elapsed <= 45",
                        "oig_referral": "45 < days_elapsed <= 75",
                        "judicial_review": "days_elapsed > 75"
                    },
                    "outputs": ["Compliance report", "Escalation decision"]
                },
                {
                    "stage_id": 4,
                    "name": "Escalation Log",
                    "type": "enforcement",
                    "properties": ["immutable", "ledger_linked", "statutory_cited"],
                    "actions": [
                        "Create escalation entry",
                        "Link to master ledger hash",
                        "Record statutory citation",
                        "Document legal presumption",
                        "Specify next action"
                    ],
                    "escalation_types": [
                        "Overdue Notice",
                        "AG Complaint Filed",
                        "OIG Referral Made",
                        "Judicial Review Petitioned"
                    ],
                    "outputs": ["Sealed escalation entry", "Updated request status"]
                },
                {
                    "stage_id": 5,
                    "name": "Enforcement Actions",
                    "type": "output",
                    "actions": [
                        "File AG complaint",
                        "Submit OIG referral",
                        "Petition for judicial review",
                        "Generate enforcement reports"
                    ],
                    "statutory_authorities": [
                        "5 U.S.C. § 552(a)(4)(B) - Judicial Review",
                        "5 U.S.C. § 552(a)(6)(A) - Response Deadlines",
                        "Inspector General Act - OIG Authority"
                    ]
                }
            ],
            "feedback_loops": [
                {
                    "name": "Status Update Loop",
                    "from": "Escalation Log",
                    "to": "Master Ledger",
                    "purpose": "Update request escalation status in ledger"
                },
                {
                    "name": "Integrity Verification",
                    "from": "All Stages",
                    "to": "All Stages",
                    "purpose": "Cryptographic chain verification ensures immutability"
                }
            ],
            "invariants": [
                "No request can bypass the ledger",
                "No escalation can occur without ledger link",
                "Business day calculation excludes weekends and holidays",
                "Chain hashes form unbroken cryptographic sequence",
                "All timestamps are immutable once sealed"
            ]
        }


# ============================================================================
# DEMONSTRATION / MAIN
# ============================================================================

def demo_pipeline():
    """Demonstrate the complete enforcement pipeline."""
    
    print("\n" + "=" * 80)
    print("SOVEREIGN ENFORCEMENT CORTEX - DEMONSTRATION")
    print("=" * 80)
    
    # Initialize components
    sealer = CryptoSealer(secret_key="DEMO_KEY_SOVEREIGN_LOCK")
    ledger = MasterLedger(sealer)
    escalation_log = EscalationLog(ledger, sealer)
    trigger_engine = TriggerEngine(ledger, escalation_log)
    
    # Create sample requests with different filing dates
    today = datetime.now()
    
    requests = [
        PublicRecordsRequest(
            request_id="REQ-2024-001",
            agency_name="Department of Interior",
            agency_contact="foia@doi.gov",
            request_description="All communications regarding Project X 2023-2024",
            filed_date=today - timedelta(days=5),  # 5 days ago - still compliant
            requester_name="John Doe"
        ),
        PublicRecordsRequest(
            request_id="REQ-2024-002",
            agency_name="Environmental Protection Agency",
            agency_contact="foia@epa.gov",
            request_description="Water quality reports for Region 5",
            filed_date=today - timedelta(days=12),  # 12 days ago - overdue
            requester_name="Jane Smith"
        ),
        PublicRecordsRequest(
            request_id="REQ-2024-003",
            agency_name="Federal Bureau of Investigation",
            agency_contact="foiipa@fbi.gov",
            request_description="Surveillance policy documents 2020-2024",
            filed_date=today - timedelta(days=25),  # 25 days ago - AG complaint level
            requester_name="Alex Johnson"
        ),
        PublicRecordsRequest(
            request_id="REQ-2024-004",
            agency_name="Department of Defense",
            agency_contact="foia.osd.mbx@mail.mil",
            request_description="UAP incident reports Q1 2024",
            filed_date=today - timedelta(days=60),  # 60 days ago - OIG referral level
            requester_name="Sarah Williams"
        ),
    ]
    
    # File all requests in ledger
    print("\n📁 FILING REQUESTS IN MASTER LEDGER...")
    print("-" * 80)
    
    for req in requests:
        entry = ledger.add_request(req)
        print(f"✓ Filed: {req.request_id} → {req.agency_name}")
        print(f"  Ledger Hash: {entry['chain_hash'][:16]}...")
    
    # Run compliance scan
    print("\n🔍 RUNNING COMPLIANCE SCAN...")
    print("-" * 80)
    
    reports = trigger_engine.run_compliance_scan(today)
    
    for report in reports:
        status_icon = "✅" if report['is_compliant'] else "⚠️"
        print(f"{status_icon} {report['request_id']}: {report['days_elapsed']} days elapsed")
        print(f"   Status: {report['recommended_action']}")
    
    # Execute auto-escalation
    print("\n⚡ EXECUTING AUTO-ESCALATION...")
    print("-" * 80)
    
    enforcement_result = trigger_engine.run_full_enforcement_cycle(today)
    
    print(f"Requests scanned: {enforcement_result['total_requests_scanned']}")
    print(f"Overdue requests: {enforcement_result['overdue_requests']}")
    print(f"Escalations created: {enforcement_result['escalations_created']}")
    
    if enforcement_result['escalation_details']:
        print("\n📋 ESCALATION DETAILS:")
        for esc in enforcement_result['escalation_details']:
            print(f"\n  🔴 {esc['escalation_id']}")
            print(f"     Type: {esc['escalation_type']}")
            print(f"     Agency: {esc['agency_name']}")
            print(f"     Days Overdue: {esc['days_overdue']}")
            print(f"     Citation: {esc['statutory_citation'][:60]}...")
            print(f"     Next Action: {esc['next_action']}")
    
    # Verify system integrity
    print("\n🔐 VERIFYING SYSTEM INTEGRITY...")
    print("-" * 80)
    
    ledger_valid, ledger_idx = ledger.verify_integrity()
    esc_valid, esc_idx = escalation_log.verify_integrity()
    
    print(f"Master Ledger Integrity: {'✅ VALID' if ledger_valid else f'❌ INVALID at entry {ledger_idx}'}")
    print(f"Escalation Log Integrity: {'✅ VALID' if esc_valid else f'❌ INVALID at entry {esc_idx}'}")
    
    # Display pipeline diagram
    print("\n" + "=" * 80)
    print("ENFORCEMENT PIPELINE DIAGRAM")
    print("=" * 80)
    
    diagram_gen = PipelineDiagramGenerator()
    print(diagram_gen.generate_ascii_diagram())
    
    # Export audit trails
    print("\n💾 EXPORTING AUDIT TRAILS...")
    print("-" * 80)
    
    ledger_export = ledger.export_audit_trail()
    esc_export = escalation_log.export_enforcement_report()
    
    print(f"Ledger export: {len(ledger_export)} bytes")
    print(f"Escalation export: {len(esc_export)} bytes")
    
    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)
    
    return {
        'ledger': ledger,
        'escalation_log': escalation_log,
        'trigger_engine': trigger_engine,
        'enforcement_result': enforcement_result
    }


if __name__ == "__main__":
    demo_pipeline()
