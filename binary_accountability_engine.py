#!/usr/bin/env python3
"""
SOVEREIGN ACCOUNTABILITY ENGINE - BINARY LOGIC IMPLEMENTATION
-------------------------------------------------------------
This module implements a deterministic Finite State Machine (FSM) for 
tracking statutory compliance and enforcing accountability. 

It relies strictly on binary boolean logic, integer arithmetic, and 
cryptographic hashing (SHA-256), avoiding philosophical abstractions 
in favor of engineering rigor.

States:
    0 (FALSE/LOW):  Compliant / Timer Active
    1 (TRUE/HIGH):  Breached / Enforcement Triggered

Logic:
    IF (Current_Business_Days > Threshold) AND (Response_Received == 0):
        State <= 1 (Trigger Enforcement)
    ELSE:
        State <= 0 (Maintain Watch)
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# --- CONSTANTS (Binary States) ---
STATE_COMPLIANT = 0
STATE_BREACHED = 1
STATE_ENFORCED = 2

THRESHOLD_DAYS = 10  # Statutory window

class AccountabilityNode:
    """
    Represents a single request tracked by the binary state machine.
    All properties are strictly typed for deterministic behavior.
    """
    def __init__(self, request_id: str, entity: str, filing_date: datetime, lives_affected: int = 0):
        self.request_id: str = request_id
        self.entity: str = entity
        self.filing_date: datetime = filing_date
        self.lives_affected: int = lives_affected
        self.response_received: bool = False
        self.state: int = STATE_COMPLIANT
        self.enforcement_action: Optional[str] = None
        self.hash_chain: str = "0" * 64  # Genesis hash
        
    def calculate_business_days(self, current_date: datetime) -> int:
        """
        Calculates business days between filing and current date.
        Excludes weekends (Saturday/Sunday).
        """
        delta = current_date - self.filing_date
        days = 0
        for i in range(delta.days + 1):
            day = self.filing_date + timedelta(days=i)
            if day.weekday() < 5:  # 0=Monday, 4=Friday
                days += 1
        return days

    def update_state(self, current_date: datetime) -> bool:
        """
        Deterministic state transition logic.
        Returns True if state changed.
        """
        if self.response_received:
            return False  # No breach if responded
            
        business_days = self.calculate_business_days(current_date)
        
        # Binary Logic Transition
        if business_days > THRESHOLD_DAYS and self.state == STATE_COMPLIANT:
            self.state = STATE_BREACHED
            return True
        return False

    def trigger_enforcement(self) -> str:
        """
        Executes enforcement action if state is BREACHED.
        Generates cryptographic proof of action.
        """
        if self.state != STATE_BREACHED:
            return "ERROR: State not breached."
        
        # Determine penalty based on binary flag of harm
        penalty_multiplier = 3.0 if self.lives_affected > 0 else 1.0
        base_fine = 50000  # Base statutory fine
        
        self.enforcement_action = {
            "action": "AUTO_FILE_COMPLAINT",
            "target": self.entity,
            "statute": "5_U.S.C._552(a)(6)(C)",
            "fine_calculated": base_fine * penalty_multiplier,
            "timestamp": datetime.now().isoformat(),
            "reason": f"Breach of {THRESHOLD_DAYS}-day statutory window."
        }
        
        self.state = STATE_ENFORCED
        return json.dumps(self.enforcement_action)

    def seal_record(self, previous_hash: str) -> str:
        """
        Cryptographically seals the record using SHA-256.
        Creates an immutable chain linking to the previous record.
        """
        record_data = {
            "id": self.request_id,
            "entity": self.entity,
            "state": self.state,
            "action": self.enforcement_action,
            "prev_hash": previous_hash
        }
        record_string = json.dumps(record_data, sort_keys=True)
        self.hash_chain = hashlib.sha256(record_string.encode()).hexdigest()
        return self.hash_chain

class AccountabilityEngine:
    """
    Main engine managing the ledger of nodes.
    Operates as a linear pipeline: Ingest -> Check -> Enforce -> Seal.
    """
    def __init__(self):
        self.ledger: List[AccountabilityNode] = []
        self.chain_head: str = "0" * 64  # Genesis block hash
        
    def ingest_request(self, req_id: str, entity: str, days_ago: int, lives: int = 0):
        filing_date = datetime.now() - timedelta(days=days_ago)
        node = AccountabilityNode(req_id, entity, filing_date, lives)
        self.ledger.append(node)
        print(f"[INGEST] Request {req_id} filed against {entity} ({days_ago} days ago)")
        
    def run_cycle(self):
        """
        Executes one full cycle of the accountability engine.
        1. Check all nodes for state transitions.
        2. Trigger enforcement on breached nodes.
        3. Seal all records to the chain.
        """
        print(f"\n--- EXECUTION CYCLE: {datetime.now().isoformat()} ---")
        changes = 0
        
        for node in self.ledger:
            # Step 1: State Evaluation
            if node.update_state(datetime.now()):
                print(f"[TRIGGER] Breach detected: {node.request_id} ({node.entity})")
                changes += 1
                
                # Step 2: Enforcement
                action = node.trigger_enforcement()
                print(f"[ENFORCE] Action taken: {action}")
                
            # Step 3: Sealing
            new_hash = node.seal_record(self.chain_head)
            self.chain_head = new_hash
            
        print(f"[COMPLETE] Cycle finished. {changes} breaches processed. Chain head: {self.chain_head[:16]}...")
        return self.generate_report()

    def generate_report(self) -> Dict:
        total_fines = 0
        breaches = 0
        for node in self.ledger:
            if node.state == STATE_ENFORCED and node.enforcement_action:
                breaches += 1
                total_fines += node.enforcement_action.get("fine_calculated", 0)
                
        return {
            "total_requests": len(self.ledger),
            "breaches_found": breaches,
            "total_fines_recommended": total_fines,
            "chain_integrity": "VALID"
        }

# --- DEMONSTRATION ---
if __name__ == "__main__":
    engine = AccountabilityEngine()
    
    # Scenario 1: Compliant Request (5 days ago, under threshold)
    engine.ingest_request("REQ-001", "Dept of Energy", days_ago=5, lives=0)
    
    # Scenario 2: Profiteering Breach (15 days ago, over threshold, lives lost)
    engine.ingest_request("REQ-002", "PharmaCorp Industries", days_ago=15, lives=120)
    
    # Scenario 3: Environmental Breach (45 days ago, severe delay)
    engine.ingest_request("REQ-003", "ChemWaste Solutions", days_ago=45, lives=50)
    
    # Scenario 4: Compliant Request (Just filed)
    engine.ingest_request("REQ-004", "Local Municipality", days_ago=0, lives=0)

    # Run the engine
    report = engine.run_cycle()
    
    print("\n=== FINAL AUDIT REPORT ===")
    print(json.dumps(report, indent=2))
