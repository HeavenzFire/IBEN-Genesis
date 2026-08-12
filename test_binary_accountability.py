#!/usr/bin/env python3
"""
Unit Tests for Binary Accountability Engine
Tests binary state machine and compliance tracking
"""

import pytest
from datetime import datetime, timedelta
from binary_accountability_engine import (
    STATE_COMPLIANT,
    STATE_BREACHED,
    STATE_ENFORCED,
    THRESHOLD_DAYS,
    AccountabilityNode,
    AccountabilityEngine
)


class TestConstants:
    """Test binary state constants"""
    
    def test_state_compliant_is_zero(self):
        """Test STATE_COMPLIANT equals 0"""
        assert STATE_COMPLIANT == 0
    
    def test_state_breached_is_one(self):
        """Test STATE_BREACHED equals 1"""
        assert STATE_BREACHED == 1
    
    def test_state_enforced_is_two(self):
        """Test STATE_ENFORCED equals 2"""
        assert STATE_ENFORCED == 2
    
    def test_threshold_days_default(self):
        """Test default threshold is 10 days"""
        assert THRESHOLD_DAYS == 10


class TestAccountabilityNode:
    """Test suite for AccountabilityNode class"""
    
    def test_node_initialization(self):
        """Test node initializes with default values"""
        node = AccountabilityNode("REQ-001", "Test Entity", datetime.now())
        assert node.request_id == "REQ-001"
        assert node.entity == "Test Entity"
        assert node.state == STATE_COMPLIANT
        assert node.response_received is False
        assert node.enforcement_action is None
        assert len(node.hash_chain) == 64
    
    def test_node_with_lives_affected(self):
        """Test node with lives affected parameter"""
        node = AccountabilityNode("REQ-002", "Entity 2", datetime.now(), lives_affected=100)
        assert node.lives_affected == 100
    
    def test_calculate_business_days(self):
        """Test business days calculation"""
        filing_date = datetime.now() - timedelta(days=14)
        node = AccountabilityNode("REQ-003", "Entity 3", filing_date)
        business_days = node.calculate_business_days(datetime.now())
        assert business_days >= 0
        assert business_days <= 14
    
    def test_update_state_compliant(self):
        """Test state remains compliant within threshold"""
        filing_date = datetime.now() - timedelta(days=5)
        node = AccountabilityNode("REQ-004", "Entity 4", filing_date)
        changed = node.update_state(datetime.now())
        assert changed is False
        assert node.state == STATE_COMPLIANT
    
    def test_update_state_breached(self):
        """Test state transitions to breached after threshold"""
        filing_date = datetime.now() - timedelta(days=15)
        node = AccountabilityNode("REQ-005", "Entity 5", filing_date)
        changed = node.update_state(datetime.now())
        assert changed is True
        assert node.state == STATE_BREACHED
    
    def test_trigger_enforcement(self):
        """Test triggering enforcement action"""
        filing_date = datetime.now() - timedelta(days=15)
        node = AccountabilityNode("REQ-006", "Entity 6", filing_date, lives_affected=10)
        node.update_state(datetime.now())
        action = node.trigger_enforcement()
        assert node.state == STATE_ENFORCED
        assert action is not None
        assert "fine_calculated" in action
    
    def test_seal_record(self):
        """Test sealing record to chain"""
        node = AccountabilityNode("REQ-007", "Entity 7", datetime.now())
        old_hash = node.hash_chain
        new_head = node.seal_record("previous_hash_123")
        assert new_head != old_hash
        assert len(new_head) == 64


class TestAccountabilityEngine:
    """Test suite for AccountabilityEngine class"""
    
    def test_engine_initialization(self):
        """Test engine initializes correctly"""
        engine = AccountabilityEngine()
        assert engine.ledger == []
        assert engine.chain_head == "0" * 64
    
    def test_ingest_request(self):
        """Test ingesting a new request"""
        engine = AccountabilityEngine()
        engine.ingest_request("REQ-008", "Entity 8", days_ago=5)
        assert len(engine.ledger) == 1
        assert engine.ledger[0].entity == "Entity 8"
    
    def test_ingest_request_with_lives(self):
        """Test ingesting request with lives affected"""
        engine = AccountabilityEngine()
        engine.ingest_request("REQ-009", "Entity 9", days_ago=10, lives=50)
        assert len(engine.ledger) == 1
        assert engine.ledger[0].lives_affected == 50
    
    def test_run_cycle_no_breaches(self):
        """Test cycle with no breaches"""
        engine = AccountabilityEngine()
        # All requests within threshold
        engine.ingest_request("REQ-010", "Entity 10", days_ago=5)
        engine.ingest_request("REQ-011", "Entity 11", days_ago=3)
        report = engine.run_cycle()
        assert report["breaches_found"] == 0
        assert report["total_requests"] == 2
    
    def test_run_cycle_with_breaches(self):
        """Test cycle with breaches"""
        engine = AccountabilityEngine()
        # Compliant request
        engine.ingest_request("REQ-012", "Entity 12", days_ago=5)
        # Breached request (over threshold)
        engine.ingest_request("REQ-013", "Entity 13", days_ago=15, lives=10)
        report = engine.run_cycle()
        assert report["breaches_found"] == 1
        assert report["total_requests"] == 2
    
    def test_run_cycle_multiple_breaches(self):
        """Test cycle with multiple breaches"""
        engine = AccountabilityEngine()
        engine.ingest_request("REQ-014", "Entity 14", days_ago=20, lives=5)
        engine.ingest_request("REQ-015", "Entity 15", days_ago=30, lives=15)
        engine.ingest_request("REQ-016", "Entity 16", days_ago=50, lives=25)
        report = engine.run_cycle()
        assert report["breaches_found"] == 3
        assert report["total_fines_recommended"] > 0
    
    def test_generate_report(self):
        """Test report generation"""
        engine = AccountabilityEngine()
        engine.ingest_request("REQ-017", "Entity 17", days_ago=15, lives=10)
        engine.run_cycle()
        report = engine.generate_report()
        assert "total_requests" in report
        assert "breaches_found" in report
        assert "total_fines_recommended" in report
        assert "chain_integrity" in report
        assert report["chain_integrity"] == "VALID"
    
    def test_chain_head_updates(self):
        """Test that chain head updates after cycle"""
        engine = AccountabilityEngine()
        initial_head = engine.chain_head
        engine.ingest_request("REQ-018", "Entity 18", days_ago=15)
        engine.run_cycle()
        assert engine.chain_head != initial_head


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
