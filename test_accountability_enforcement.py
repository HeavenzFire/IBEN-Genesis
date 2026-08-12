#!/usr/bin/env python3
"""
Unit Tests for Accountability Enforcement Module
Tests profiteering violation tracking and criminal referral generation
"""

import pytest
import json
from datetime import datetime, timedelta
from accountability_enforcement_module import (
    ProfiteeringViolation,
    CriminalReferral,
    AccountabilityEnforcementEngine
)


class TestProfiteeringViolation:
    """Test suite for ProfiteeringViolation dataclass"""
    
    def test_create_violation_basic(self):
        """Test creating a basic violation record"""
        violation = ProfiteeringViolation(
            violation_id="VIO-001",
            entity_name="Test Corp",
            entity_type="Corporation",
            scheme_description="Test scheme",
            victims_affected=100,
            monetary_extraction_usd=1_000_000.0,
            lives_lost=0,
            lives_damaged=10,
            statutory_violations=["wire_fraud"],
            evidence_hashes=["hash1"],
            whistleblower_id_hash="wh_hash",
            filing_date="2024-01-01",
            jurisdiction="NDNY",
            severity_tier="HIGH"
        )
        assert violation.violation_id == "VIO-001"
        assert violation.entity_name == "Test Corp"
        assert violation.victims_affected == 100
        assert violation.monetary_extraction_usd == 1_000_000.0
    
    def test_generate_evidence_hash(self):
        """Test that evidence hash is deterministic"""
        violation = ProfiteeringViolation(
            violation_id="VIO-002",
            entity_name="Test Corp 2",
            entity_type="LLC",
            scheme_description="Another scheme",
            victims_affected=50,
            monetary_extraction_usd=500_000.0,
            lives_lost=0,
            lives_damaged=5,
            statutory_violations=["mail_fraud"],
            evidence_hashes=["hash2"],
            whistleblower_id_hash="wh_hash2",
            filing_date="2024-02-01",
            jurisdiction="SDNY",
            severity_tier="MEDIUM"
        )
        hash1 = violation.generate_evidence_hash()
        hash2 = violation.generate_evidence_hash()
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length
    
    def test_evidence_hash_changes_with_data(self):
        """Test that hash changes when data changes"""
        violation1 = ProfiteeringViolation(
            violation_id="VIO-003",
            entity_name="Corp A",
            entity_type="Corp",
            scheme_description="Scheme A",
            victims_affected=10,
            monetary_extraction_usd=100_000.0,
            lives_lost=0,
            lives_damaged=1,
            statutory_violations=["fraud"],
            evidence_hashes=[],
            whistleblower_id_hash="wh1",
            filing_date="2024-01-01",
            jurisdiction="NY",
            severity_tier="LOW"
        )
        violation2 = ProfiteeringViolation(
            violation_id="VIO-003",
            entity_name="Corp B",  # Different name
            entity_type="Corp",
            scheme_description="Scheme A",
            victims_affected=10,
            monetary_extraction_usd=100_000.0,
            lives_lost=0,
            lives_damaged=1,
            statutory_violations=["fraud"],
            evidence_hashes=[],
            whistleblower_id_hash="wh1",
            filing_date="2024-01-01",
            jurisdiction="NY",
            severity_tier="LOW"
        )
        assert violation1.generate_evidence_hash() != violation2.generate_evidence_hash()


class TestCriminalReferral:
    """Test suite for CriminalReferral dataclass"""
    
    def test_calculate_penalty_no_lives_lost(self):
        """Test penalty calculation when no lives lost"""
        violation = ProfiteeringViolation(
            violation_id="VIO-004",
            entity_name="Bad Corp",
            entity_type="Corp",
            scheme_description="Fraud scheme",
            victims_affected=100,
            monetary_extraction_usd=2_000_000.0,
            lives_lost=0,
            lives_damaged=5,
            statutory_violations=["wire_fraud"],
            evidence_hashes=[],
            whistleblower_id_hash="wh",
            filing_date="2024-01-01",
            jurisdiction="NY",
            severity_tier="HIGH"
        )
        penalty = CriminalReferral.calculate_penalty(violation)
        assert penalty["criminal_fine_usd"] == (2_000_000.0 * 3) + (5 * 2_500_000)
        assert penalty["imprisonment_years"] == min(10 + (5 * 2), 40)
        assert penalty["restitution_usd"] == 2_000_000.0 * 2
        assert penalty["asset_forfeiture"] is True
    
    def test_calculate_penalty_with_lives_lost(self):
        """Test penalty calculation when lives are lost"""
        violation = ProfiteeringViolation(
            violation_id="VIO-005",
            entity_name="Deadly Corp",
            entity_type="Corp",
            scheme_description="Deadly scheme",
            victims_affected=50,
            monetary_extraction_usd=1_000_000.0,
            lives_lost=3,
            lives_damaged=10,
            statutory_violations=["healthcare_fraud"],
            evidence_hashes=[],
            whistleblower_id_hash="wh",
            filing_date="2024-01-01",
            jurisdiction="CA",
            severity_tier="CRITICAL"
        )
        penalty = CriminalReferral.calculate_penalty(violation)
        assert penalty["criminal_fine_usd"] == (1_000_000.0 * 3) + (3 * 10_000_000)
        assert penalty["imprisonment_years"] == min(30 + (3 * 5), 99)
        assert penalty["rico_charges_applicable"] is True
    
    def test_calculate_penalty_financial_only(self):
        """Test penalty for financial crimes with no physical harm"""
        violation = ProfiteeringViolation(
            violation_id="VIO-006",
            entity_name="Finance Corp",
            entity_type="LLC",
            scheme_description="Ponzi scheme",
            victims_affected=500,
            monetary_extraction_usd=10_000_000.0,
            lives_lost=0,
            lives_damaged=0,
            statutory_violations=["securities_fraud"],
            evidence_hashes=[],
            whistleblower_id_hash="wh",
            filing_date="2024-01-01",
            jurisdiction="NY",
            severity_tier="HIGH"
        )
        penalty = CriminalReferral.calculate_penalty(violation)
        assert penalty["imprisonment_years"] == min(5 + int(10_000_000.0 / 1_000_000), 20)
        assert penalty["rico_charges_applicable"] is True  # Over $5M


class TestAccountabilityEnforcementEngine:
    """Test suite for AccountabilityEnforcementEngine"""
    
    def test_engine_initialization(self):
        """Test engine initializes correctly"""
        engine = AccountabilityEnforcementEngine()
        assert engine.violation_registry == []
        assert engine.criminal_referrals == []
        assert engine.enforcement_actions == []
        assert engine.master_ledger_ref == "IBEN-Genesis"
        assert engine.secret_key is not None
        assert len(engine.secret_key) == 32  # SHA-256 key length
    
    def test_file_violation(self):
        """Test filing a violation with the engine"""
        engine = AccountabilityEnforcementEngine()
        violation_data = {
            "entity_name": "File Corp",
            "entity_type": "Corporation",
            "scheme_description": "Test filing scheme",
            "victims_affected": 25,
            "monetary_extraction_usd": 250_000.0,
            "lives_lost": 0,
            "lives_damaged": 2,
            "statutory_violations": ["conspiracy"],
            "jurisdiction": "TX"
        }
        violation = engine.file_violation(violation_data)
        assert violation.entity_name == "File Corp"
        assert violation.victims_affected == 25
        assert len(engine.violation_registry) == 1
        assert len(violation.evidence_hashes) >= 1  # Auto-generated hash added
    
    def test_auto_generate_criminal_referral(self):
        """Test that auto-generating a criminal referral works"""
        engine = AccountabilityEnforcementEngine()
        violation_data = {
            "entity_name": "Referral Corp",
            "entity_type": "Healthcare Corporation",
            "scheme_description": "Healthcare fraud test",
            "victims_affected": 75,
            "monetary_extraction_usd": 750_000.0,
            "lives_lost": 1,
            "lives_damaged": 5,
            "statutory_violations": ["false_claims", "healthcare_fraud"],
            "jurisdiction": "FL"
        }
        violation = engine.file_violation(violation_data)
        referral = engine.auto_generate_criminal_referral(violation)
        assert referral.violation_id == violation.violation_id
        assert len(referral.recipient_agencies) >= 2
        assert referral.asset_forfeiture_recommended is True
        assert referral.restitution_required is True
        assert len(engine.criminal_referrals) == 1
    
    def test_execute_enforcement_action(self):
        """Test executing an enforcement action"""
        engine = AccountabilityEnforcementEngine()
        violation_data = {
            "entity_name": "Enforcement Corp",
            "entity_type": "Corporation",
            "scheme_description": "Enforcement test",
            "victims_affected": 50,
            "monetary_extraction_usd": 500_000.0,
            "lives_lost": 0,
            "lives_damaged": 3,
            "statutory_violations": ["wire_fraud"],
            "jurisdiction": "CA"
        }
        violation = engine.file_violation(violation_data)
        referral = engine.auto_generate_criminal_referral(violation)
        action = engine.execute_enforcement_action(referral)
        assert action["status"] == "SUBMITTED"
        assert action["referral_id"] == referral.referral_id
        assert len(action["tracking_numbers"]) == len(referral.recipient_agencies)
        assert len(engine.enforcement_actions) == 1
    
    def test_run_full_enforcement_cycle(self):
        """Test running a full enforcement cycle"""
        engine = AccountabilityEnforcementEngine()
        violation_data = {
            "entity_name": "Cycle Corp",
            "entity_type": "Pharmaceutical Company",
            "scheme_description": "Full cycle test - price gouging",
            "victims_affected": 100,
            "monetary_extraction_usd": 1_000_000.0,
            "lives_lost": 2,
            "lives_damaged": 10,
            "statutory_violations": ["pharmaceutical_fraud", "antitrust"],
            "jurisdiction": "NY"
        }
        result = engine.run_full_enforcement_cycle(violation_data)
        assert result["enforcement_cycle_complete"] is True
        assert result["entity_held_accountable"] == "Cycle Corp"
        assert result["evidence_chain_secured"] is True
        assert result["cryptographic_integrity"] == "VERIFIED"
        assert len(result["agencies_notified"]) >= 2


class TestStatutoryCitations:
    """Test statutory citation mappings"""
    
    def test_statutory_citations_exist(self):
        """Test that statutory citations are defined"""
        engine = AccountabilityEnforcementEngine()
        assert "false_claims" in engine.STATUTORY_CITATIONS
        assert "healthcare_fraud" in engine.STATUTORY_CITATIONS
        assert "wire_fraud" in engine.STATUTORY_CITATIONS
        assert "mail_fraud" in engine.STATUTORY_CITATIONS
        assert "conspiracy" in engine.STATUTORY_CITATIONS
    
    def test_recipient_agencies_exist(self):
        """Test that recipient agencies table exists"""
        engine = AccountabilityEnforcementEngine()
        assert "DOJ_Criminal" in engine.RECIPIENT_AGENCIES
        assert "FBI_PublicCorruption" in engine.RECIPIENT_AGENCIES
        assert "HHS_OIG" in engine.RECIPIENT_AGENCIES


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
