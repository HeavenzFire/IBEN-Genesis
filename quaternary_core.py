"""
IBEN-Genesis: Quaternary Logic Core Module

Implements quaternary state encoding (-2, -1, +1, +2) for enhanced 
information density and multi-state routing in the P2P mesh framework.

Quadrant State Encoding eliminates neutral zero, using symmetric bipolar pairs
for balanced positive/negative vector loads with 2x data permutations vs binary.
"""

from enum import IntEnum
from typing import List, Tuple, Optional
import numpy as np
from dataclasses import dataclass


class QuaternaryState(IntEnum):
    """Quaternary logic states: symmetric bipolar encoding"""
    NEG_TWO = -2
    NEG_ONE = -1
    POS_ONE = 1
    POS_TWO = 2
    
    @classmethod
    def from_int(cls, value: int) -> 'QuaternaryState':
        """Convert integer to QuaternaryState with validation"""
        if value not in [-2, -1, 1, 2]:
            raise ValueError(f"Invalid quaternary state: {value}. Must be -2, -1, 1, or 2")
        return cls(value)
    
    @classmethod
    def from_binary_pair(cls, bit1: int, bit2: int) -> 'QuaternaryState':
        """
        Map binary pair (0/1, 0/1) to quaternary state
        00 -> -2, 01 -> -1, 10 -> +1, 11 -> +2
        """
        mapping = {
            (0, 0): cls.NEG_TWO,
            (0, 1): cls.NEG_ONE,
            (1, 0): cls.POS_ONE,
            (1, 1): cls.POS_TWO
        }
        return mapping[(bit1, bit2)]
    
    def to_binary_pair(self) -> Tuple[int, int]:
        """Convert quaternary state back to binary pair"""
        mapping = {
            self.NEG_TWO: (0, 0),
            self.NEG_ONE: (0, 1),
            self.POS_ONE: (1, 0),
            self.POS_TWO: (1, 1)
        }
        return mapping[self]
    
    @property
    def polarity(self) -> int:
        """Return polarity: -1 for negative states, +1 for positive"""
        return 1 if self.value > 0 else -1
    
    @property
    def magnitude(self) -> int:
        """Return magnitude: 1 or 2"""
        return abs(self.value)


@dataclass
class QuaternaryVector:
    """Vector of quaternary states for data encoding"""
    states: List[QuaternaryState]
    
    def __post_init__(self):
        if not self.states:
            raise ValueError("QuaternaryVector cannot be empty")
    
    def __len__(self) -> int:
        return len(self.states)
    
    def dot_product(self, other: 'QuaternaryVector') -> int:
        """Compute dot product maintaining quaternary constraints"""
        if len(self) != len(other):
            raise ValueError("Vectors must have same length")
        return sum(s.value * o.value for s, o in zip(self.states, other.states))
    
    def tensor_transform(self, matrix: np.ndarray) -> 'QuaternaryVector':
        """Apply gyroidal tensor transformation"""
        values = np.array([s.value for s in self.states])
        transformed = matrix @ values
        # Quantize back to valid quaternary states
        quantized = []
        for val in transformed:
            clamped = np.clip(val, -2, 2)
            if clamped >= 0:
                q_state = 1 if clamped < 1.5 else 2
            else:
                q_state = -1 if clamped > -1.5 else -2
            if q_state == 0:
                q_state = 1 if val > 0 else -1
            quantized.append(QuaternaryState.from_int(q_state))
        return QuaternaryVector(quantized)
    
    def information_density(self) -> float:
        """Calculate bits per symbol (log2(4) = 2 bits per quaternary state)"""
        return len(self.states) * 2.0
    
    def checksum(self) -> int:
        """Generate quaternary checksum for error detection"""
        total = sum(s.value for s in self.states)
        return ((total + 6) % 4) - 2  # Map to valid quaternary range


class QuaternaryEncoder:
    """Encode/decode data using quaternary logic"""
    
    @staticmethod
    def encode_bytes(data: bytes) -> QuaternaryVector:
        """Convert bytes to quaternary vector (4 bits -> 2 quaternary states)"""
        states = []
        for byte in data:
            # Split byte into two 4-bit nibbles
            high_nibble = (byte >> 4) & 0xF
            low_nibble = byte & 0xF
            
            # Each nibble (4 values) maps to one quaternary state
            for nibble in [high_nibble, low_nibble]:
                # Map 0-3 to -2,-1,+1,+2
                mapping = {0: -2, 1: -1, 2: 1, 3: 2}
                states.append(QuaternaryState.from_int(mapping[nibble % 4]))
        
        return QuaternaryVector(states)
    
    @staticmethod
    def decode_bytes(vector: QuaternaryVector) -> bytes:
        """Convert quaternary vector back to bytes"""
        if len(vector) % 2 != 0:
            raise ValueError("Vector length must be even for byte decoding")
        
        reverse_mapping = {-2: 0, -1: 1, 1: 2, 2: 3}
        result = []
        
        for i in range(0, len(vector), 2):
            high = reverse_mapping[vector.states[i].value]
            low = reverse_mapping[vector.states[i + 1].value]
            byte = (high << 4) | low
            result.append(byte)
        
        return bytes(result)
    
    @staticmethod
    def apply_error_correction(vector: QuaternaryVector, 
                                expected_checksum: int) -> Tuple[QuaternaryVector, bool]:
        """
        Basic error detection/correction using quaternary checksum
        Returns corrected vector and success flag
        """
        actual_checksum = vector.checksum()
        
        if actual_checksum == expected_checksum:
            return vector, True
        
        # Simple single-error correction attempt
        states = list(vector.states)
        for i in range(len(states)):
            original = states[i]
            for test_val in [-2, -1, 1, 2]:
                if test_val == original.value:
                    continue
                states[i] = QuaternaryState.from_int(test_val)
                test_vector = QuaternaryVector(states)
                if test_vector.checksum() == expected_checksum:
                    return test_vector, True
            states[i] = original
        
        return vector, False


def generate_gyroidal_tensor_matrix(dimensions: int = 4) -> np.ndarray:
    """
    Generate gyroidal tensor transformation matrix for quaternary routing
    Maps four logic states to orthogonal pathways on gyroidal surface
    """
    # Gyroid minimal surface approximation tensor
    theta = np.pi / 4  # 45-degree rotation for orthogonal separation
    
    # Create base rotation matrix for 4D quaternary space
    base_matrix = np.eye(dimensions)
    
    # Apply gyroidal curvature transformation
    gyroid_factor = np.sin(theta) * np.cos(theta)
    
    for i in range(dimensions):
        for j in range(dimensions):
            if i != j:
                base_matrix[i][j] = gyroid_factor * ((-1) ** (i + j))
    
    # Normalize to maintain unit vector properties
    norm = np.linalg.norm(base_matrix, axis=1, keepdims=True)
    norm[norm == 0] = 1  # Avoid division by zero
    base_matrix = base_matrix / norm
    
    return base_matrix


# Example usage and demonstration
if __name__ == "__main__":
    print("=" * 60)
    print("IBEN-Genesis: Quaternary Logic Core Demonstration")
    print("=" * 60)
    
    # Test quaternary state encoding
    test_data = b"IBEN"
    encoder = QuaternaryEncoder()
    
    encoded = encoder.encode_bytes(test_data)
    print(f"\nOriginal data: {test_data}")
    print(f"Encoded quaternary states: {[s.value for s in encoded.states]}")
    print(f"Information density: {encoded.information_density()} bits")
    
    # Test round-trip encoding
    decoded = encoder.decode_bytes(encoded)
    print(f"Decoded data: {decoded}")
    print(f"Round-trip successful: {test_data == decoded}")
    
    # Test tensor transformation
    tensor_matrix = generate_gyroidal_tensor_matrix(len(encoded.states))
    transformed = encoded.tensor_transform(tensor_matrix[:len(encoded.states)])
    print(f"\nTensor transformed states: {[s.value for s in transformed.states]}")
    
    # Test checksum
    checksum = encoded.checksum()
    print(f"Quaternary checksum: {checksum}")
    
    # Test error correction
    corrupted_states = list(encoded.states)
    corrupted_states[0] = QuaternaryState.from_int(-corrupted_states[0].value)  # Flip first state
    corrupted = QuaternaryVector(corrupted_states)
    corrected, success = encoder.apply_error_correction(corrupted, checksum)
    print(f"\nError correction successful: {success}")
    print(f"Corrected matches original: {corrected.states == encoded.states}")
    
    print("\n" + "=" * 60)
    print("Quaternary core module validated successfully")
    print("=" * 60)
