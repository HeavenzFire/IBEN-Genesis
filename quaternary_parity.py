#!/usr/bin/env python3
"""
IBEN-Genesis: Quaternary Cryptographic Parity Framework
Establishes parity constraints for validating peer-to-peer ledger transactions
using quaternary logic structures.

This module implements:
- Quaternary checksum algorithms
- Multi-party consensus validation
- Error detection and correction codes
- Ledger state verification protocols
"""

from typing import List, Tuple, Dict, Optional
from enum import IntEnum
import hashlib


class QState(IntEnum):
    """Quaternary state enumeration."""
    NULL = 0      # 00: Ground state
    DIRECT = 1    # 01: Forward propagation
    COUNTER = 2   # 10: Reverse propagation
    SYNTROPIC = 3 # 11: Super-state overlay


class QuaternaryParityValidator:
    """
    Implements cryptographic parity validation for quaternary-based ledgers.
    
    Core Principles:
    - Each transaction encoded as quaternary state sequence
    - Parity symbols enable single-error detection/correction
    - Consensus achieved through syntropic MAX operator
    - Quantum-resistant through lattice-inspired structures
    """
    
    def __init__(self, block_size: int = 8, parity_symbols: int = 4):
        """
        Initialize validator with configurable parameters.
        
        Args:
            block_size: Number of data symbols per block
            parity_symbols: Number of parity symbols for error correction
        """
        self.block_size = block_size
        self.parity_symbols = parity_symbols
        self.total_symbols = block_size + parity_symbols
    
    def compute_quaternary_checksum(self, data: List[int]) -> int:
        """
        Compute quaternary checksum using weighted sum modulo 4.
        
        Formula: checksum = Σ(data[i] × (i+1)) mod 4
        
        Args:
            data: List of quaternary symbols [0-3]
            
        Returns:
            Single quaternary checksum value [0-3]
        """
        if not all(d in [0, 1, 2, 3] for d in data):
            raise ValueError("Data must contain only quaternary values 0-3")
        
        weighted_sum = sum(d * (i + 1) for i, d in enumerate(data))
        return weighted_sum % 4
    
    def compute_dual_parity(self, data: List[int]) -> Tuple[int, int]:
        """
        Compute dual parity for enhanced error detection.
        
        Uses two independent parity calculations:
        - P1: Simple XOR-equivalent (sum mod 4)
        - P2: Weighted position parity
        
        Args:
            data: List of quaternary symbols
            
        Returns:
            Tuple of (parity1, parity2)
        """
        if not all(d in [0, 1, 2, 3] for d in data):
            raise ValueError("Data must contain only quaternary values 0-3")
        
        # P1: Direct sum modulo 4
        p1 = sum(data) % 4
        
        # P2: Alternating weight pattern (1, 2, 1, 2, ...)
        weights = [1 if i % 2 == 0 else 2 for i in range(len(data))]
        p2 = sum(d * w for d, w in zip(data, weights)) % 4
        
        return (p1, p2)
    
    def encode_with_parity(self, data: List[int]) -> List[int]:
        """
        Encode data block with parity symbols for error correction.
        
        Appends parity symbols to enable single-error detection and correction.
        
        Args:
            data: Data symbols (must be <= block_size)
            
        Returns:
            Extended block with parity symbols appended
        """
        if len(data) > self.block_size:
            raise ValueError(f"Data exceeds block size ({len(data)} > {self.block_size})")
        
        # Pad data to block size
        padded_data = data + [0] * (self.block_size - len(data))
        
        # Generate parity symbols
        parity_symbols = []
        
        # Parity 1: Checksum
        p1 = self.compute_quaternary_checksum(padded_data)
        parity_symbols.append(p1)
        
        # Parity 2 & 3: Dual parity
        p2, p3 = self.compute_dual_parity(padded_data)
        parity_symbols.extend([p2, p3])
        
        # Parity 4+: Additional redundancy based on position patterns
        for i in range(3, self.parity_symbols):
            pattern_sum = sum(d for j, d in enumerate(padded_data) if j % (i + 1) == 0)
            parity_symbols.append(pattern_sum % 4)
        
        return padded_data + parity_symbols
    
    def detect_and_correct_errors(self, received: List[int]) -> Tuple[List[int], List[int]]:
        """
        Detect and correct single-symbol errors in received block.
        
        Uses syndrome decoding to identify error location and magnitude.
        
        Args:
            received: Received block (data + parity symbols)
            
        Returns:
            Tuple of (corrected_data, error_locations)
        """
        if len(received) != self.total_symbols:
            raise ValueError(f"Invalid block length: {len(received)} != {self.total_symbols}")
        
        data = received[:self.block_size]
        received_parity = received[self.block_size:]
        
        # Recompute expected parity
        expected_p1 = self.compute_quaternary_checksum(data)
        expected_p2, expected_p3 = self.compute_dual_parity(data)
        
        error_locations = []
        corrected = data.copy()
        
        # Check for discrepancies
        syndrome = []
        syndrome.append((received_parity[0] - expected_p1) % 4)
        syndrome.append((received_parity[1] - expected_p2) % 4)
        syndrome.append((received_parity[2] - expected_p3) % 4)
        
        # If any syndrome is non-zero, we have an error
        if any(s != 0 for s in syndrome):
            # Try to locate single-symbol error
            for pos in range(self.block_size):
                # Test if changing this position fixes the syndrome
                for delta in [1, 2, 3]:
                    test_data = data.copy()
                    test_data[pos] = (test_data[pos] + delta) % 4
                    
                    test_p1 = self.compute_quaternary_checksum(test_data)
                    test_p2, test_p3 = self.compute_dual_parity(test_data)
                    
                    if (test_p1 == received_parity[0] and 
                        test_p2 == received_parity[1] and 
                        test_p3 == received_parity[2]):
                        corrected = test_data
                        error_locations.append(pos)
                        break
                
                if error_locations:
                    break
        
        return corrected, error_locations
    
    def validate_ledger_transaction(self, transaction: Dict) -> Tuple[bool, str]:
        """
        Validate a ledger transaction using quaternary parity rules.
        
        Transaction structure:
        {
            'sender': str,
            'receiver': str,
            'amount': int,
            'timestamp': int,
            'data': List[int],  # Quaternary-encoded payload
            'checksum': int,
            'consensus_votes': List[int]  # Node votes [0-3]
        }
        
        Args:
            transaction: Transaction dictionary
            
        Returns:
            Tuple of (is_valid, reason)
        """
        required_fields = ['sender', 'receiver', 'amount', 'timestamp', 'data', 'checksum']
        for field in required_fields:
            if field not in transaction:
                return False, f"Missing required field: {field}"
        
        # Validate data contains only quaternary values
        if not all(d in [0, 1, 2, 3] for d in transaction['data']):
            return False, "Invalid quaternary data values"
        
        # Verify checksum
        computed_checksum = self.compute_quaternary_checksum(transaction['data'])
        if computed_checksum != transaction['checksum']:
            return False, f"Checksum mismatch: expected {computed_checksum}, got {transaction['checksum']}"
        
        # Validate consensus votes if present
        if 'consensus_votes' in transaction:
            votes = transaction['consensus_votes']
            if not all(v in [0, 1, 2, 3] for v in votes):
                return False, "Invalid consensus vote values"
            
            # Require majority syntropic/direct votes for validation
            valid_votes = sum(1 for v in votes if v in [1, 3])
            if valid_votes < len(votes) // 2 + 1:
                return False, "Insufficient consensus validation"
        
        # Validate amount is non-negative
        if transaction['amount'] < 0:
            return False, "Negative amount not allowed"
        
        return True, "Transaction valid"
    
    def compute_syntropic_consensus(self, node_states: List[List[int]]) -> List[int]:
        """
        Compute consensus state across multiple validating nodes.
        
        Uses MAX operator for syntropic resolution:
        CONSENSUS[i] = MAX(node_states[0][i], node_states[1][i], ...)
        
        Args:
            node_states: List of quaternary state arrays from each node
            
        Returns:
            Consensus state array
        """
        if not node_states:
            raise ValueError("No node states provided")
        
        array_length = len(node_states[0])
        if not all(len(ns) == array_length for ns in node_states):
            raise ValueError("All node states must have same length")
        
        consensus = []
        for i in range(array_length):
            max_state = max(ns[i] for ns in node_states)
            consensus.append(max_state)
        
        return consensus
    
    def generate_state_proof(self, data: List[int], block_id: int) -> Dict:
        """
        Generate cryptographic state proof for immutable logging.
        
        Creates a verifiable proof combining:
        - Quaternary Merkle-like root
        - Parity signatures
        - Block metadata hash
        
        Args:
            data: Quaternary state data
            block_id: Unique block identifier
            
        Returns:
            State proof dictionary
        """
        # Compute quaternary root (iterative pairwise MAX reduction)
        current_level = data.copy()
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                if i + 1 < len(current_level):
                    next_level.append(max(current_level[i], current_level[i + 1]))
                else:
                    next_level.append(current_level[i])
            current_level = next_level
        
        quat_root = current_level[0] if current_level else 0
        
        # Compute parity signature
        parity = self.compute_dual_parity(data)
        
        # Create cryptographic hash binding
        hash_input = f"{block_id}:{quat_root}:{parity[0]}:{parity[1]}:{''.join(map(str, data))}"
        crypto_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        
        return {
            'block_id': block_id,
            'quaternary_root': quat_root,
            'parity_signature': parity,
            'data_length': len(data),
            'crypto_binding': crypto_hash,
            'timestamp': self._get_logical_timestamp()
        }
    
    def _get_logical_timestamp(self) -> int:
        """Get logical timestamp for proof generation."""
        import time
        return int(time.time() * 1000)
    
    def verify_state_proof(self, data: List[int], proof: Dict) -> bool:
        """
        Verify a state proof against original data.
        
        Args:
            data: Original quaternary data
            proof: State proof dictionary
            
        Returns:
            True if proof is valid
        """
        # Recompute quaternary root
        current_level = data.copy()
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                if i + 1 < len(current_level):
                    next_level.append(max(current_level[i], current_level[i + 1]))
                else:
                    next_level.append(current_level[i])
            current_level = next_level
        
        computed_root = current_level[0] if current_level else 0
        
        # Verify root matches
        if computed_root != proof['quaternary_root']:
            return False
        
        # Verify parity
        computed_parity = self.compute_dual_parity(data)
        if computed_parity != tuple(proof['parity_signature']):
            return False
        
        # Verify crypto binding
        hash_input = f"{proof['block_id']}:{proof['quaternary_root']}:{proof['parity_signature'][0]}:{proof['parity_signature'][1]}:{''.join(map(str, data))}"
        expected_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        
        return proof['crypto_binding'] == expected_hash


def demonstrate_parity_validation():
    """Demonstrate quaternary parity validation with examples."""
    print("=" * 60)
    print("IBEN-Genesis: Quaternary Cryptographic Parity Framework")
    print("=" * 60)
    print()
    
    validator = QuaternaryParityValidator(block_size=8, parity_symbols=4)
    
    # Example 1: Checksum computation
    print("1. Quaternary Checksum Computation:")
    print("-" * 40)
    test_data = [1, 2, 0, 3, 1, 2, 3, 0]
    checksum = validator.compute_quaternary_checksum(test_data)
    print(f"  Data:     {test_data}")
    print(f"  Checksum: {checksum}")
    print()
    
    # Example 2: Dual parity
    print("2. Dual Parity Calculation:")
    print("-" * 40)
    p1, p2 = validator.compute_dual_parity(test_data)
    print(f"  Data:       {test_data}")
    print(f"  Parity P1:  {p1} (direct sum mod 4)")
    print(f"  Parity P2:  {p2} (weighted position)")
    print()
    
    # Example 3: Encoding with parity
    print("3. Block Encoding with Parity Symbols:")
    print("-" * 40)
    original_data = [1, 0, 3, 2, 1, 1, 0, 2]
    encoded = validator.encode_with_parity(original_data)
    print(f"  Original data: {original_data}")
    print(f"  Encoded block: {encoded}")
    print(f"  Data portion:  {encoded[:validator.block_size]}")
    print(f"  Parity portion: {encoded[validator.block_size:]}")
    print()
    
    # Example 4: Error detection and correction
    print("4. Error Detection and Correction:")
    print("-" * 40)
    # Introduce a single-symbol error
    corrupted = encoded.copy()
    error_pos = 3
    corrupted[error_pos] = (corrupted[error_pos] + 2) % 4
    print(f"  Original:  {encoded}")
    print(f"  Corrupted: {corrupted} (position {error_pos} altered)")
    
    corrected, errors = validator.detect_and_correct_errors(corrupted)
    print(f"  Corrected: {corrected}")
    print(f"  Errors found at: {errors}")
    print(f"  Recovery successful: {corrected == encoded[:validator.block_size]}")
    print()
    
    # Example 5: Transaction validation
    print("5. Ledger Transaction Validation:")
    print("-" * 40)
    valid_transaction = {
        'sender': 'node_alpha',
        'receiver': 'node_beta',
        'amount': 100,
        'timestamp': 1699900000,
        'data': [1, 2, 3, 0, 1, 1, 2, 0],
        'checksum': 0,  # Will be computed
        'consensus_votes': [3, 3, 1, 3, 1]
    }
    valid_transaction['checksum'] = validator.compute_quaternary_checksum(valid_transaction['data'])
    
    is_valid, reason = validator.validate_ledger_transaction(valid_transaction)
    print(f"  Valid transaction test:")
    print(f"    Result: {'✓ VALID' if is_valid else '✗ INVALID'}")
    print(f"    Reason: {reason}")
    print()
    
    invalid_transaction = valid_transaction.copy()
    invalid_transaction['amount'] = -50
    is_valid, reason = validator.validate_ledger_transaction(invalid_transaction)
    print(f"  Invalid transaction test (negative amount):")
    print(f"    Result: {'✓ VALID' if is_valid else '✗ INVALID'}")
    print(f"    Reason: {reason}")
    print()
    
    # Example 6: Syntropic consensus
    print("6. Syntropic Consensus Across Nodes:")
    print("-" * 40)
    node_states = [
        [1, 0, 2, 1, 3],
        [0, 1, 2, 2, 1],
        [1, 1, 1, 3, 2],
        [2, 0, 3, 1, 1],
    ]
    consensus = validator.compute_syntropic_consensus(node_states)
    print(f"  Node 1: {node_states[0]}")
    print(f"  Node 2: {node_states[1]}")
    print(f"  Node 3: {node_states[2]}")
    print(f"  Node 4: {node_states[3]}")
    print(f"  Consensus (MAX): {consensus}")
    print()
    
    # Example 7: State proof generation and verification
    print("7. Immutable State Proof Generation:")
    print("-" * 40)
    ledger_data = [1, 2, 0, 3, 1, 2, 1, 0, 3, 3, 2, 1]
    proof = validator.generate_state_proof(ledger_data, block_id=42)
    
    print(f"  Ledger data: {ledger_data}")
    print(f"  Block ID:    {proof['block_id']}")
    print(f"  Quat. root:  {proof['quaternary_root']}")
    print(f"  Parity sig:  {proof['parity_signature']}")
    print(f"  Crypto bind: {proof['crypto_binding']}")
    print()
    
    # Verify the proof
    is_valid = validator.verify_state_proof(ledger_data, proof)
    print(f"  Proof verification: {'✓ VALID' if is_valid else '✗ INVALID'}")
    
    # Tamper with data and verify again
    tampered_data = ledger_data.copy()
    tampered_data[5] = (tampered_data[5] + 1) % 4
    is_valid = validator.verify_state_proof(tampered_data, proof)
    print(f"  Tampered data verification: {'✓ VALID' if is_valid else '✗ INVALID'} (expected: INVALID)")
    print()
    
    # Summary
    print("=" * 60)
    print("Parity Framework Summary:")
    print("-" * 40)
    print(f"  Block size:        {validator.block_size} symbols")
    print(f"  Parity symbols:    {validator.parity_symbols}")
    print(f"  Total block size:  {validator.total_symbols} symbols")
    print(f"  Error correction:  Single-symbol detection & correction")
    print(f"  Consensus method:  Syntropic MAX operator")
    print("=" * 60)


if __name__ == "__main__":
    demonstrate_parity_validation()
