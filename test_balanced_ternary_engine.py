#!/usr/bin/env python3
"""
Unit tests for balanced_ternary_engine.py
Tests Trit class, TernaryGates, AccountabilityState, and TernaryLedger
"""

import pytest
import sys
import os

# Add workspace to path
sys.path.insert(0, '/workspace')

from balanced_ternary_engine import (
    Trit,
    TernaryGates,
    AccountabilityState,
    TernaryLedger
)


class TestTrit:
    """Test the fundamental Trit class"""
    
    def test_valid_values(self):
        """Test that valid trit values can be created"""
        t_neg = Trit(-1)
        t_zero = Trit(0)
        t_pos = Trit(1)
        
        assert t_neg.value == -1
        assert t_zero.value == 0
        assert t_pos.value == 1
    
    def test_invalid_value_raises_error(self):
        """Test that invalid values raise ValueError"""
        with pytest.raises(ValueError):
            Trit(2)
        with pytest.raises(ValueError):
            Trit(-2)
        with pytest.raises(ValueError):
            Trit(5)
    
    def test_int_conversion(self):
        """Test conversion to int"""
        assert int(Trit(-1)) == -1
        assert int(Trit(0)) == 0
        assert int(Trit(1)) == 1
    
    def test_equality(self):
        """Test equality comparisons"""
        assert Trit(-1) == Trit(-1)
        assert Trit(0) == Trit(0)
        assert Trit(1) == Trit(1)
        assert Trit(-1) != Trit(1)
        assert Trit(0) != Trit(-1)
        
        # Compare with int
        assert Trit(-1) == -1
        assert Trit(0) == 0
        assert Trit(1) == 1
    
    def test_invert(self):
        """Test logical NOT operation"""
        assert (~Trit(-1)).value == 1
        assert (~Trit(0)).value == 0
        assert (~Trit(1)).value == -1
    
    def test_and_operation(self):
        """Test ternary AND (min)"""
        # min(-1, -1) = -1
        assert (Trit(-1) & Trit(-1)).value == -1
        # min(-1, 0) = -1
        assert (Trit(-1) & Trit(0)).value == -1
        # min(-1, 1) = -1
        assert (Trit(-1) & Trit(1)).value == -1
        # min(0, 0) = 0
        assert (Trit(0) & Trit(0)).value == 0
        # min(0, 1) = 0
        assert (Trit(0) & Trit(1)).value == 0
        # min(1, 1) = 1
        assert (Trit(1) & Trit(1)).value == 1
        
        # AND with int
        assert (Trit(-1) & -1).value == -1
        assert (Trit(1) & 0).value == 0
    
    def test_or_operation(self):
        """Test ternary OR (max)"""
        # max(-1, -1) = -1
        assert (Trit(-1) | Trit(-1)).value == -1
        # max(-1, 0) = 0
        assert (Trit(-1) | Trit(0)).value == 0
        # max(-1, 1) = 1
        assert (Trit(-1) | Trit(1)).value == 1
        # max(0, 0) = 0
        assert (Trit(0) | Trit(0)).value == 0
        # max(0, 1) = 1
        assert (Trit(0) | Trit(1)).value == 1
        # max(1, 1) = 1
        assert (Trit(1) | Trit(1)).value == 1
    
    def test_mul_operation(self):
        """Test ternary multiplication"""
        # -1 * -1 = 1
        assert (Trit(-1) * Trit(-1)).value == 1
        # -1 * 0 = 0
        assert (Trit(-1) * Trit(0)).value == 0
        # -1 * 1 = -1
        assert (Trit(-1) * Trit(1)).value == -1
        # 0 * 1 = 0
        assert (Trit(0) * Trit(1)).value == 0
        # 1 * 1 = 1
        assert (Trit(1) * Trit(1)).value == 1
    
    def test_add_operation_with_saturation(self):
        """Test ternary addition with saturation"""
        # -1 + -1 = -2 -> saturated to -1
        assert (Trit(-1) + Trit(-1)).value == -1
        # -1 + 0 = -1
        assert (Trit(-1) + Trit(0)).value == -1
        # -1 + 1 = 0
        assert (Trit(-1) + Trit(1)).value == 0
        # 0 + 0 = 0
        assert (Trit(0) + Trit(0)).value == 0
        # 1 + 1 = 2 -> saturated to 1
        assert (Trit(1) + Trit(1)).value == 1
        # 1 + -1 = 0
        assert (Trit(1) + Trit(-1)).value == 0
        
        # Addition with int
        assert (Trit(1) + 1).value == 1  # saturated
        assert (Trit(-1) + -1).value == -1  # saturated


class TestTernaryGates:
    """Test ternary logic gates"""
    
    def test_inverter(self):
        """Test NOT gate"""
        assert TernaryGates.INVERTER(Trit(-1)).value == 1
        assert TernaryGates.INVERTER(Trit(0)).value == 0
        assert TernaryGates.INVERTER(Trit(1)).value == -1
    
    def test_and_gate(self):
        """Test AND gate"""
        assert TernaryGates.AND(Trit(-1), Trit(-1)).value == -1
        assert TernaryGates.AND(Trit(-1), Trit(1)).value == -1
        assert TernaryGates.AND(Trit(0), Trit(1)).value == 0
        assert TernaryGates.AND(Trit(1), Trit(1)).value == 1
    
    def test_or_gate(self):
        """Test OR gate"""
        assert TernaryGates.OR(Trit(-1), Trit(-1)).value == -1
        assert TernaryGates.OR(Trit(-1), Trit(1)).value == 1
        assert TernaryGates.OR(Trit(0), Trit(1)).value == 1
        assert TernaryGates.OR(Trit(0), Trit(0)).value == 0
    
    def test_majority_gate(self):
        """Test majority gate"""
        # All same
        assert TernaryGates.MAJORITY(Trit(-1), Trit(-1), Trit(-1)).value == -1
        assert TernaryGates.MAJORITY(Trit(0), Trit(0), Trit(0)).value == 0
        assert TernaryGates.MAJORITY(Trit(1), Trit(1), Trit(1)).value == 1
        
        # Two out of three - sum based logic
        # -1 + -1 + 1 = -1 -> negative -> -1
        assert TernaryGates.MAJORITY(Trit(-1), Trit(-1), Trit(1)).value == -1
        # -1 + 1 + 1 = 1 -> positive -> 1
        assert TernaryGates.MAJORITY(Trit(-1), Trit(1), Trit(1)).value == 1
        # -1 + 0 + 0 = -1 -> negative -> -1 (implementation uses sum)
        assert TernaryGates.MAJORITY(Trit(-1), Trit(0), Trit(0)).value == -1
        # 1 + 0 + 0 = 1 -> positive -> 1
        assert TernaryGates.MAJORITY(Trit(1), Trit(0), Trit(0)).value == 1
    
    def test_consensus_gate(self):
        """Test consensus gate with multiple inputs"""
        # Empty input
        assert TernaryGates.CONSENSUS([]).value == 0
        
        # All same
        assert TernaryGates.CONSENSUS([Trit(-1), Trit(-1), Trit(-1)]).value == -1
        assert TernaryGates.CONSENSUS([Trit(1), Trit(1), Trit(1)]).value == 1
        
        # Mixed - positive sum
        assert TernaryGates.CONSENSUS([Trit(1), Trit(1), Trit(-1)]).value == 1
        
        # Mixed - negative sum
        assert TernaryGates.CONSENSUS([Trit(-1), Trit(-1), Trit(1)]).value == -1
        
        # Balanced - zero sum
        assert TernaryGates.CONSENSUS([Trit(-1), Trit(1)]).value == 0


class TestAccountabilityState:
    """Test accountability state machine"""
    
    def test_initialization(self):
        """Test state machine initialization"""
        state = AccountabilityState("entity123", "price_gouging")
        
        assert state.entity_id == "entity123"
        assert state.violation_type == "price_gouging"
        assert state.evidence_strength.value == 0
        assert state.statutory_breach.value == 0
        assert state.harm_confirmed.value == 0
        assert state.enforcement_required.value == 0
    
    def test_ingest_evidence(self):
        """Test evidence ingestion"""
        state = AccountabilityState("test", "test_violation")
        
        # Strong violation evidence
        state.ingest_evidence(-0.95)
        assert state.evidence_strength.value == -1
        
        # Strong compliant evidence
        state.ingest_evidence(0.85)
        assert state.evidence_strength.value == 1
        
        # Uncertain/null evidence
        state.ingest_evidence(0.1)
        assert state.evidence_strength.value == 0
        
        state.ingest_evidence(-0.2)
        assert state.evidence_strength.value == 0
    
    def test_check_threshold(self):
        """Test statutory threshold checking"""
        state = AccountabilityState("test", "test_violation")
        
        # Over threshold (breach)
        state.check_threshold(days_elapsed=45, threshold=10)
        assert state.statutory_breach.value == -1
        
        # Under threshold (compliant)
        state.check_threshold(days_elapsed=5, threshold=10)
        assert state.statutory_breach.value == 1
        
        # At threshold (null/boundary)
        state.check_threshold(days_elapsed=10, threshold=10)
        assert state.statutory_breach.value == 0
    
    def test_assess_harm(self):
        """Test harm assessment"""
        state = AccountabilityState("test", "test_violation")
        
        # Severe harm (violation)
        state.assess_harm(lives_lost=100, financial_damage=50e9)
        assert state.harm_confirmed.value == -1
        
        # No harm (compliant)
        state.assess_harm(lives_lost=0, financial_damage=0)
        assert state.harm_confirmed.value == 1
        
        # Moderate harm (null)
        state.assess_harm(lives_lost=5, financial_damage=1e6)
        assert state.harm_confirmed.value == 0
    
    def test_compute_enforcement_decision(self):
        """Test enforcement decision logic"""
        state = AccountabilityState("test", "test_violation")
        
        # All violations -> enforcement required (-1)
        state.evidence_strength = Trit(-1)
        state.statutory_breach = Trit(-1)
        state.harm_confirmed = Trit(-1)
        decision = state.compute_enforcement_decision()
        assert decision.value == -1  # min(-1, -1, -1) = -1
        
        # AND logic: -1 & -1 & 1 = min(-1, -1, 1) = -1
        # When any condition is COMPLIANT (+1), the AND still returns the minimum
        state.evidence_strength = Trit(-1)
        state.statutory_breach = Trit(-1)
        state.harm_confirmed = Trit(1)
        decision = state.compute_enforcement_decision()
        assert decision.value == -1  # min(-1, -1, 1) = -1
        
        # Mixed with NULL: -1 & 0 & 1 = min(-1, 0, 1) = -1
        state.evidence_strength = Trit(-1)
        state.statutory_breach = Trit(0)
        state.harm_confirmed = Trit(1)
        decision = state.compute_enforcement_decision()
        assert decision.value == -1  # min(-1, 0, 1) = -1
        
        # All NULL -> review (0)
        state.evidence_strength = Trit(0)
        state.statutory_breach = Trit(0)
        state.harm_confirmed = Trit(0)
        decision = state.compute_enforcement_decision()
        assert decision.value == 0  # min(0, 0, 0) = 0
        
        # Any NULL with positive values -> 0
        state.evidence_strength = Trit(0)
        state.statutory_breach = Trit(1)
        state.harm_confirmed = Trit(1)
        decision = state.compute_enforcement_decision()
        assert decision.value == 0  # min(0, 1, 1) = 0
    
    def test_get_state_vector(self):
        """Test state vector output"""
        state = AccountabilityState("entity456", "pollution")
        state.ingest_evidence(-0.8)
        state.check_threshold(30, 10)
        state.assess_harm(50, 1e9)
        state.compute_enforcement_decision()
        
        vector = state.get_state_vector()
        
        assert vector["entity_id"] == "entity456"
        assert vector["violation_type"] == "pollution"
        assert "timestamp" in vector
        assert vector["evidence_strength"] == -1
        assert vector["statutory_breach"] == -1
        assert vector["harm_confirmed"] == -1
        assert vector["enforcement_required"] == -1


class TestTernaryLedger:
    """Test ternary ledger functionality"""
    
    def test_ledger_initialization(self):
        """Test ledger creation with genesis block"""
        ledger = TernaryLedger()
        
        assert ledger.genesis_hash is not None
        assert len(ledger.genesis_hash) == 64  # SHA256 hex length
        assert len(ledger.chain) == 0
    
    def test_seal_state(self):
        """Test sealing states to ledger"""
        ledger = TernaryLedger()
        
        state = AccountabilityState("test_entity", "test_violation")
        state.ingest_evidence(-0.9)
        state.check_threshold(20, 10)
        state.assess_harm(10, 1e6)
        state.compute_enforcement_decision()
        
        block_hash = ledger.seal_state(state)
        
        assert block_hash is not None
        assert len(block_hash) == 64
        assert len(ledger.chain) == 1
        assert ledger.chain[0] == block_hash
    
    def test_multiple_blocks_chain(self):
        """Test chaining multiple blocks"""
        ledger = TernaryLedger()
        
        # Seal first state
        state1 = AccountabilityState("entity1", "violation1")
        hash1 = ledger.seal_state(state1)
        
        # Seal second state
        state2 = AccountabilityState("entity2", "violation2")
        hash2 = ledger.seal_state(state2)
        
        # Seal third state
        state3 = AccountabilityState("entity3", "violation3")
        hash3 = ledger.seal_state(state3)
        
        assert len(ledger.chain) == 3
        assert ledger.chain[0] == hash1
        assert ledger.chain[1] == hash2
        assert ledger.chain[2] == hash3
        
        # Verify hashes are unique
        assert hash1 != hash2
        assert hash2 != hash3
        assert hash1 != hash3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
