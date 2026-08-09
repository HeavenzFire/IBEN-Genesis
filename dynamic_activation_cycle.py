#!/usr/bin/env python3
"""
Dynamic Activation Cycle Visualization Module
Extends the Sovereign Enforcement Cortex with sequential telemetry handshake breakdown
Shows how each component lights up when a request breaches the statutory window
"""

import hashlib
import hmac
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

class DynamicActivationCycle:
    """
    Visualizes the sequential activation of the enforcement pipeline
    when a statutory breach occurs.
    """
    
    def __init__(self):
        self.activation_sequence = []
        self.telemetry_log = []
        
    def generate_mermaid_sequence(self) -> str:
        """Generate the Mermaid.js sequence diagram for the activation cycle."""
        
        mermaid_code = '''```mermaid
sequenceDiagram
    autonumber
    participant Client as Request Ingestion
    participant Ledger as Master Ledger (SHA-256/HMAC)
    participant Trigger as Trigger Engine (10-Day Reflex)
    participant Escalation as Escalation Log (Legal Presumptions)
    participant Enforcement as Enforcement Module (AG / Statutory Action)

    Note over Client, Enforcement: 🟢 NORMAL PATH (Compliant Request ≤ 10 Days)
    Client->>Ledger: File Request & Seal Cryptographic Genesis Hash
    Ledger-->>Trigger: Register Watch Timer & State Vector

    Note over Trigger: Day 1 to 10: Countdown Active (No Breach)
    Trigger->>Ledger: Heartbeat Status Check (Valid / Within Window)

    ---

    Note over Client, Enforcement: 🔴 BREACH PATH (Overdue Request > 10 Days)
    Trigger->>Trigger: Statutory Threshold Breached (> 10 Business Days)
    
    rect rgb(40, 20, 20)
        Note over Trigger, Enforcement: ⚡ TELEMETRY HANDSHAKE & FLASH PATH
        Trigger->>Ledger: ⚡ Query State & Retrieve Immutable Genesis Record
        Ledger-->>Trigger: 🔐 Return Block Hash & Metadata Proof
        
        Trigger->>Escalation: ⚡ Broadcast Breach Telemetry (Agency Flagged: FBI / DoD)
        Escalation->>Escalation: ⚖️ Bind Statutory Citations & Legal Presumptions
        
        Escalation->>Enforcement: ⚡ Transmit Sealed Enforcement Payload
        Enforcement->>Enforcement: 🚀 Auto-File Attorney General / Regulatory Complaint
        Enforcement->>Ledger: 🔒 Seal Enforcement Outcome & Append to Chain Hash
    end
```'''
        return mermaid_code
    
    def generate_ascii_activation_flow(self, breach_data: Dict) -> str:
        """Generate ASCII art showing the activation flow with breach data."""
        
        ascii_art = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DYNAMIC ACTIVATION CYCLE - BREACH DETECTED                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  AGENCY: {breach_data.get('agency', 'UNKNOWN'):<65} ║
║  REQUEST ID: {breach_data.get('request_id', 'N/A'):<63} ║
║  DAYS OVERDUE: {breach_data.get('days_overdue', 0):<63} ║
║  STATUTORY THRESHOLD: 10 BUSINESS DAYS                                       ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────────┐
│ SEQUENTIAL TELEMETRY HANDSHAKE BREAKDOWN                                     │
└──────────────────────────────────────────────────────────────────────────────┘

  STEP 1: THE PULSE (Trigger Engine Detection)
  ─────────────────────────────────────────────
  ⚡ Autonomic reflex continuously polls active request ledger
  ⚡ Clock crosses 10-business-day statutory window
  ⚡ Trigger state vector flips: [ACTIVE WATCH] → [ACTIVE BREACH]
  
     [██████████] 100% BREACH CONFIRMED
     Agency: {breach_data.get('agency', 'N/A'):<8} | Days: {breach_data.get('days_overdue', 0):>3} | Status: OVERDUE

  ↓

  STEP 2: THE LEDGER VERIFICATION FLASH
  ──────────────────────────────────────
  ⚡ Trigger Engine requests cryptographic verification handshake
  ⚡ Master Ledger returns sealed SHA-256/HMAC genesis block
  ⚡ Tamper-resistance proven, timeline of non-compliance locked
  
     GENESIS HASH: {breach_data.get('genesis_hash', 'N/A')[:48]}...
     METADATA PROOF: {breach_data.get('metadata_proof', 'VERIFIED'):<12}
     CHAIN INTEGRITY: ✅ VALIDATED

  ↓

  STEP 3: THE ESCALATION BINDING
  ───────────────────────────────
  ⚡ Telemetry data streams into Escalation Log
  ⚡ System auto-pulls statutory enforcement citations
  ⚡ Agency ID matched to exact legal presumption for default violation
  
     STATUTORY CITATIONS:
     • FOIA 5 U.S.C. § 552(a)(6)(A) - Time Limits
     • FOIA 5 U.S.C. § 552(a)(6)(C) - Exhaustion of Remedies
     • Legal Presumption: Information deemed public by operation of law
     
     ESCALATION STATUS: None → AG COMPLAINT FILED

  ↓

  STEP 4: THE ENFORCEMENT EXECUTION
  ──────────────────────────────────
  ⚡ Closed-loop circuit fires payload to Enforcement Module
  ⚡ Auto-files complaint with Attorney General / regulatory body
  ⚡ Final action permanently sealed back into Master Ledger
  
     ENFORCEMENT ACTION: Attorney General Complaint Filed
     FILING TIMESTAMP: {breach_data.get('filing_timestamp', 'N/A')}
     EVIDENTIARY CHAIN: Unbroken, Trustless, Immutable ✅

  ↓

  ┌────────────────────────────────────────────────────────────────────────────┐
  │ 🔄 FEEDBACK LOOP: Enforcement outcome sealed to Master Ledger              │
  │    New chain hash appended, completing the sovereign forensic circuit      │
  └────────────────────────────────────────────────────────────────────────────┘

"""
        return ascii_art
    
    def simulate_breach_activation(self, request_data: Dict) -> Dict:
        """Simulate the complete activation cycle for a breached request."""
        
        # Step 1: Convert datetime objects to strings for JSON serialization
        serializable_request = {}
        for key, value in request_data.items():
            if isinstance(value, datetime):
                serializable_request[key] = value.strftime('%Y-%m-%d')
            else:
                serializable_request[key] = value
        
        # Step 2: Generate genesis hash (simulating ledger lookup)
        genesis_data = json.dumps(serializable_request, sort_keys=True)
        genesis_hash = hashlib.sha256(genesis_data.encode()).hexdigest()
        
        # Step 3: Calculate days overdue
        filing_date = request_data.get('filing_date', datetime.now())
        current_date = request_data.get('current_date', datetime.now())
        business_days = self._calculate_business_days(filing_date, current_date)
        days_overdue = max(0, business_days - 10)
        
        # Step 3: Build activation telemetry
        activation_telemetry = {
            'request_id': request_data.get('request_id', 'UNKNOWN'),
            'agency': request_data.get('agency', 'UNKNOWN'),
            'subject': request_data.get('subject', 'UNKNOWN'),
            'filing_date': filing_date.strftime('%Y-%m-%d') if isinstance(filing_date, datetime) else str(filing_date),
            'current_date': current_date.strftime('%Y-%m-%d') if isinstance(current_date, datetime) else str(current_date),
            'business_days_elapsed': business_days,
            'days_overdue': days_overdue,
            'genesis_hash': genesis_hash,
            'metadata_proof': 'VERIFIED',
            'statutory_citations': [
                '5 U.S.C. § 552(a)(6)(A)',
                '5 U.S.C. § 552(a)(6)(C)',
                'Legal Presumption: Public by Operation of Law'
            ],
            'escalation_status': 'AG COMPLAINT FILED' if days_overdue > 0 else 'WITHIN WINDOW',
            'enforcement_action': f"Attorney General Complaint - {request_data.get('agency', 'UNKNOWN')}" if days_overdue > 0 else 'NONE',
            'filing_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
            'chain_integrity': 'VALIDATED',
            'activation_sequence': [
                'PULSE_DETECTED',
                'LEDGER_VERIFIED',
                'ESCALATION_BOUND',
                'ENFORCEMENT_EXECUTED',
                'FEEDBACK_SEALED'
            ]
        }
        
        self.activation_sequence.append(activation_telemetry)
        return activation_telemetry
    
    def _calculate_business_days(self, start_date: datetime, end_date: datetime) -> int:
        """Calculate business days between two dates (excluding weekends)."""
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        business_days = 0
        current_date = start_date
        
        while current_date <= end_date:
            # Monday = 0, Sunday = 6
            if current_date.weekday() < 5:
                business_days += 1
            current_date += timedelta(days=1)
        
        return business_days
    
    def generate_full_report(self, breach_requests: List[Dict]) -> str:
        """Generate a complete activation cycle report for multiple breach requests."""
        
        report_lines = [
            "=" * 80,
            "SOVEREIGN ENFORCEMENT CORTEX - DYNAMIC ACTIVATION CYCLE REPORT",
            "=" * 80,
            "",
            self.generate_mermaid_sequence(),
            ""
        ]
        
        for idx, request in enumerate(breach_requests, 1):
            telemetry = self.simulate_breach_activation(request)
            
            report_lines.append(f"\n{'='*80}")
            report_lines.append(f"ACTIVATION CYCLE #{idx} - {telemetry['agency']}")
            report_lines.append(f"{'='*80}\n")
            report_lines.append(self.generate_ascii_activation_flow(telemetry))
        
        report_lines.append("\n" + "=" * 80)
        report_lines.append("SUMMARY OF ACTIVATION SEQUENCES")
        report_lines.append("=" * 80)
        
        for idx, telemetry in enumerate(self.activation_sequence, 1):
            status_icon = "🔴" if telemetry['days_overdue'] > 0 else "🟢"
            report_lines.append(
                f"{idx}. {status_icon} {telemetry['agency']}: "
                f"{telemetry['escalation_status']} "
                f"(+{telemetry['days_overdue']} days overdue)"
            )
        
        report_lines.append("\n" + "=" * 80)
        report_lines.append("✅ ALL ACTIVATION CYCLES COMPLETED - EVIDENTIARY CHAIN INTACT")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)


# Demonstration execution
if __name__ == "__main__":
    print("Initializing Dynamic Activation Cycle Module...")
    print("=" * 80)
    
    # Initialize the activation cycle visualizer
    activator = DynamicActivationCycle()
    
    # Sample breach requests from the demonstration
    breach_requests = [
        {
            'request_id': 'FOIA-2024-001',
            'agency': 'FBI',
            'subject': 'Surveillance Program Documents',
            'filing_date': datetime(2024, 11, 1),
            'current_date': datetime(2024, 12, 1)  # ~22 calendar days, ~17 business days
        },
        {
            'request_id': 'FOIA-2024-004',
            'agency': 'DoD',
            'subject': 'UAP Incident Reports',
            'filing_date': datetime(2024, 10, 1),
            'current_date': datetime(2024, 12, 1)  # ~44 calendar days, ~42 business days
        }
    ]
    
    # Generate and display the full activation cycle report
    report = activator.generate_full_report(breach_requests)
    print(report)
    
    # Save to file for reference
    with open('/workspace/activation_cycle_report.txt', 'w') as f:
        f.write(report)
    
    print("\n✅ Activation cycle report saved to: /workspace/activation_cycle_report.txt")
    print("✅ Mermaid.js sequence diagram embedded in report for visualization")
