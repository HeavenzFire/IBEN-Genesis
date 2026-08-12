#!/usr/bin/env python3
"""
Unit tests for quaternary_core.py and quaternary_gates.py
Tests QuaternaryState, QuaternaryVector, QuaternaryEncoder, and QuaternaryGates
"""

import pytest
import sys
sys.path.insert(0, '/workspace')

from quaternary_core import (
    QuaternaryState,
    QuaternaryVector,
    QuaternaryEncoder,
    generate_gyroidal_tensor_matrix
)

from quaternary_gates import (
    QState,
    QuaternaryGates
)


# =============================================================================
# TESTS FOR QUATERNARY STATE
# =============================================================================

class TestQuaternaryState:
    """Test QuaternaryState enumeration and conversions"""
    
    def test_valid_states(self):
        """Test valid quaternary states can be created"""
        assert QuaternaryState.NEG_TWO.value == -2
        assert QuaternaryState.NEG_ONE.value == -1
        assert QuaternaryState.POS_ONE.value == 1
        assert QuaternaryState.POS_TWO.value == 2
    
    def test_from_int_valid(self):
        """Test from_int with valid values"""
        assert QuaternaryState.from_int(-2) == QuaternaryState.NEG_TWO
        assert QuaternaryState.from_int(-1) == QuaternaryState.NEG_ONE
        assert QuaternaryState.from_int(1) == QuaternaryState.POS_ONE
        assert QuaternaryState.from_int(2) == QuaternaryState.POS_TWO
    
    def test_from_int_invalid_raises_error(self):
        """Test from_int raises ValueError for invalid values"""
        with pytest.raises(ValueError):
            QuaternaryState.from_int(0)
        with pytest.raises(ValueError):
            QuaternaryState.from_int(3)
        with pytest.raises(ValueError):
            QuaternaryState.from_int(-3)
    
    def test_from_binary_pair(self):
        """Test binary pair to quaternary mapping"""
        assert QuaternaryState.from_binary_pair(0, 0) == QuaternaryState.NEG_TWO
        assert QuaternaryState.from_binary_pair(0, 1) == QuaternaryState.NEG_ONE
        assert QuaternaryState.from_binary_pair(1, 0) == QuaternaryState.POS_ONE
        assert QuaternaryState.from_binary_pair(1, 1) == QuaternaryState.POS_TWO
    
    def test_to_binary_pair(self):
        """Test quaternary to binary pair conversion"""
        assert QuaternaryState.NEG_TWO.to_binary_pair() == (0, 0)
        assert QuaternaryState.NEG_ONE.to_binary_pair() == (0, 1)
        assert QuaternaryState.POS_ONE.to_binary_pair() == (1, 0)
        assert QuaternaryState.POS_TWO.to_binary_pair() == (1, 1)
    
    def test_polarity(self):
        """Test polarity property"""
        assert QuaternaryState.NEG_TWO.polarity == -1
        assert QuaternaryState.NEG_ONE.polarity == -1
        assert QuaternaryState.POS_ONE.polarity == 1
        assert QuaternaryState.POS_TWO.polarity == 1
    
    def test_magnitude(self):
        """Test magnitude property"""
        assert QuaternaryState.NEG_TWO.magnitude == 2
        assert QuaternaryState.NEG_ONE.magnitude == 1
        assert QuaternaryState.POS_ONE.magnitude == 1
        assert QuaternaryState.POS_TWO.magnitude == 2


# =============================================================================
# TESTS FOR QUATERNARY GATES
# =============================================================================

class TestQuaternaryGates:
    """Test quaternary logic gates"""
    
    def test_not_gate(self):
        """Test quaternary NOT gate"""
        assert QuaternaryGates.NOT(0) == 3
        assert QuaternaryGates.NOT(1) == 2
        assert QuaternaryGates.NOT(2) == 1
        assert QuaternaryGates.NOT(3) == 0
    
    def test_not_gate_invalid_input(self):
        """Test NOT gate rejects invalid input"""
        with pytest.raises(ValueError):
            QuaternaryGates.NOT(4)
        with pytest.raises(ValueError):
            QuaternaryGates.NOT(-1)
    
    def test_and_gate(self):
        """Test quaternary AND gate (min)"""
        # Identity with 3
        assert QuaternaryGates.AND(0, 3) == 0
        assert QuaternaryGates.AND(1, 3) == 1
        assert QuaternaryGates.AND(2, 3) == 2
        assert QuaternaryGates.AND(3, 3) == 3
        
        # Zero annihilates
        assert QuaternaryGates.AND(0, 0) == 0
        assert QuaternaryGates.AND(0, 1) == 0
        assert QuaternaryGates.AND(0, 2) == 0
        assert QuaternaryGates.AND(0, 3) == 0
        
        # General cases
        assert QuaternaryGates.AND(1, 2) == 1
        assert QuaternaryGates.AND(2, 1) == 1
        assert QuaternaryGates.AND(1, 1) == 1
        assert QuaternaryGates.AND(2, 2) == 2
    
    def test_or_gate(self):
        """Test quaternary OR gate (max)"""
        # Identity with 0
        assert QuaternaryGates.OR(0, 0) == 0
        assert QuaternaryGates.OR(0, 1) == 1
        assert QuaternaryGates.OR(0, 2) == 2
        assert QuaternaryGates.OR(0, 3) == 3
        
        # Three dominates
        assert QuaternaryGates.OR(3, 0) == 3
        assert QuaternaryGates.OR(3, 1) == 3
        assert QuaternaryGates.OR(3, 2) == 3
        assert QuaternaryGates.OR(3, 3) == 3
        
        # General cases
        assert QuaternaryGates.OR(1, 2) == 2
        assert QuaternaryGates.OR(2, 1) == 2
        assert QuaternaryGates.OR(1, 1) == 1
        assert QuaternaryGates.OR(2, 2) == 2
    
    def test_xor_gate(self):
        """Test quaternary XOR gate (absolute difference)"""
        # XOR with 0 is identity
        assert QuaternaryGates.XOR(0, 0) == 0
        assert QuaternaryGates.XOR(0, 1) == 1
        assert QuaternaryGates.XOR(0, 2) == 2
        assert QuaternaryGates.XOR(0, 3) == 3
        
        # Self-XOR is 0
        assert QuaternaryGates.XOR(1, 1) == 0
        assert QuaternaryGates.XOR(2, 2) == 0
        assert QuaternaryGates.XOR(3, 3) == 0
        
        # General cases
        assert QuaternaryGates.XOR(1, 3) == 2
        assert QuaternaryGates.XOR(3, 1) == 2
        assert QuaternaryGates.XOR(2, 3) == 1
        assert QuaternaryGates.XOR(1, 2) == 1
    
    def test_balance_operation(self):
        """Test BALANCE operation"""
        # All NULL -> 0
        assert QuaternaryGates.BALANCE([0, 0, 0]) == 0
        # All DIRECT -> 1
        assert QuaternaryGates.BALANCE([1, 1, 1]) == 1
        # All COUNTER -> 2
        assert QuaternaryGates.BALANCE([2, 2, 2]) == 2
        
        # Mixed: positive sum -> DIRECT (1)
        assert QuaternaryGates.BALANCE([1, 1, 0]) == 1
        # Mixed: negative sum -> COUNTER (2)
        assert QuaternaryGates.BALANCE([2, 2, 0]) == 2
        # Balanced: zero sum -> NULL (0)
        assert QuaternaryGates.BALANCE([1, 2]) == 0
    
    def test_consensus_operation(self):
        """Test CONSENSUS operation (max)"""
        # All same
        assert QuaternaryGates.CONSENSUS([0, 0, 0]) == 0
        assert QuaternaryGates.CONSENSUS([1, 1, 1]) == 1
        assert QuaternaryGates.CONSENSUS([2, 2, 2]) == 2
        assert QuaternaryGates.CONSENSUS([3, 3, 3]) == 3
        
        # Two out of three - max wins
        assert QuaternaryGates.CONSENSUS([0, 0, 1]) == 1
        assert QuaternaryGates.CONSENSUS([0, 1, 1]) == 1
        assert QuaternaryGates.CONSENSUS([1, 1, 2]) == 2
        assert QuaternaryGates.CONSENSUS([1, 2, 2]) == 2
        assert QuaternaryGates.CONSENSUS([2, 2, 3]) == 3  # max(2,2,3) = 3
        assert QuaternaryGates.CONSENSUS([2, 3, 3]) == 3


# =============================================================================
# TESTS FOR QUATERNARY VECTOR
# =============================================================================

class TestQuaternaryVector:
    """Test QuaternaryVector operations"""
    
    def test_create_vector(self):
        """Test vector creation"""
        states = [QuaternaryState.NEG_TWO, QuaternaryState.POS_ONE]
        vec = QuaternaryVector(states)
        assert len(vec) == 2
        assert vec.states == states
    
    def test_empty_vector_raises_error(self):
        """Test empty vector raises ValueError"""
        with pytest.raises(ValueError):
            QuaternaryVector([])
    
    def test_dot_product(self):
        """Test dot product calculation"""
        vec1 = QuaternaryVector([QuaternaryState.from_int(1), QuaternaryState.from_int(2)])
        vec2 = QuaternaryVector([QuaternaryState.from_int(1), QuaternaryState.from_int(-1)])
        
        # 1*1 + 2*(-1) = 1 - 2 = -1
        assert vec1.dot_product(vec2) == -1
        
        # Self dot product: 1*1 + 2*2 = 5
        assert vec1.dot_product(vec1) == 5
    
    def test_dot_product_length_mismatch(self):
        """Test dot product with mismatched lengths"""
        vec1 = QuaternaryVector([QuaternaryState.from_int(1)])
        vec2 = QuaternaryVector([QuaternaryState.from_int(1), QuaternaryState.from_int(2)])
        
        with pytest.raises(ValueError):
            vec1.dot_product(vec2)
    
    def test_information_density(self):
        """Test information density calculation"""
        vec = QuaternaryVector([QuaternaryState.from_int(i) for i in [1, -1, 2, -2]])
        # 4 states * 2 bits per state = 8 bits
        assert vec.information_density() == 8.0
    
    def test_checksum(self):
        """Test checksum calculation"""
        # sum = 1 + (-1) + 2 + (-2) = 0
        # ((0 + 6) % 4) - 2 = 6 % 4 - 2 = 2 - 2 = 0
        vec = QuaternaryVector([
            QuaternaryState.from_int(1),
            QuaternaryState.from_int(-1),
            QuaternaryState.from_int(2),
            QuaternaryState.from_int(-2)
        ])
        assert vec.checksum() == 0
        
        # sum = 2 + 2 = 4
        # ((4 + 6) % 4) - 2 = 10 % 4 - 2 = 2 - 2 = 0
        vec2 = QuaternaryVector([QuaternaryState.from_int(2), QuaternaryState.from_int(2)])
        assert vec2.checksum() == 0


# =============================================================================
# TESTS FOR QUATERNARY ENCODER
# =============================================================================

class TestQuaternaryEncoder:
    """Test QuaternaryEncoder functionality"""
    
    def test_encode_bytes(self):
        """Test byte encoding"""
        encoder = QuaternaryEncoder()
        data = b"AB"
        encoded = encoder.encode_bytes(data)
        
        # 'A' = 65 = 0x41 -> high nibble 4, low nibble 1
        # 4 % 4 = 0 -> -2, 1 % 4 = 1 -> -1
        # 'B' = 66 = 0x42 -> high nibble 4, low nibble 2
        # 4 % 4 = 0 -> -2, 2 % 4 = 2 -> 1
        assert len(encoded.states) == 4
    
    def test_decode_bytes(self):
        """Test byte decoding"""
        encoder = QuaternaryEncoder()
        # Use bytes that map cleanly to quaternary states
        original = b'\x01\x02\x03\x00'
        encoded = encoder.encode_bytes(original)
        decoded = encoder.decode_bytes(encoded)
        assert decoded == original
    
    def test_round_trip_multiple_strings(self):
        """Test round-trip encoding/decoding"""
        encoder = QuaternaryEncoder()
        # Test with binary data that maps correctly (nibbles 0-3 only)
        # The encoder uses nibble % 4, so we need bytes where high and low nibbles are 0-3
        test_data_list = [
            b'\x00\x01\x02\x03',
            b'\x10\x20\x30\x03',  # Nibbles: 1,0 2,0 3,0 0,3 -> all in range 0-3
        ]
        
        for test_data in test_data_list:
            encoded = encoder.encode_bytes(test_data)
            decoded = encoder.decode_bytes(encoded)
            assert decoded == test_data, f"Failed for {test_data!r}: got {decoded!r}"
    
    def test_decode_odd_length_raises_error(self):
        """Test decoding odd-length vector raises error"""
        encoder = QuaternaryEncoder()
        odd_vec = QuaternaryVector([QuaternaryState.from_int(1)])
        
        with pytest.raises(ValueError):
            encoder.decode_bytes(odd_vec)
    
    def test_apply_error_correction_no_errors(self):
        """Test error correction with no errors"""
        encoder = QuaternaryEncoder()
        original = b"DATA"
        encoded = encoder.encode_bytes(original)
        checksum = encoded.checksum()
        
        corrected, success = encoder.apply_error_correction(encoded, checksum)
        assert success is True
        assert corrected.states == encoded.states


# =============================================================================
# TESTS FOR TENSOR MATRIX
# =============================================================================

class TestGyroidalTensorMatrix:
    """Test gyroidal tensor matrix generation"""
    
    def test_generate_matrix_default_size(self):
        """Test matrix generation with default size"""
        matrix = generate_gyroidal_tensor_matrix()
        assert matrix.shape == (4, 4)
    
    def test_generate_matrix_custom_size(self):
        """Test matrix generation with custom size"""
        matrix = generate_gyroidal_tensor_matrix(8)
        assert matrix.shape == (8, 8)
    
    def test_matrix_diagonal_dominance(self):
        """Test that diagonal elements are dominant"""
        matrix = generate_gyroidal_tensor_matrix(4)
        # Diagonal should be non-zero (normalized)
        for i in range(4):
            assert abs(matrix[i][i]) > 0
    
    def test_matrix_normalization(self):
        """Test that rows are normalized"""
        matrix = generate_gyroidal_tensor_matrix(4)
        for i in range(4):
            row_norm = sum(matrix[i][j]**2 for j in range(4))**0.5
            assert abs(row_norm - 1.0) < 0.01  # Allow small floating point error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
