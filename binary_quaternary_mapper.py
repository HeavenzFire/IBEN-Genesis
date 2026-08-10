#!/usr/bin/env python3
"""
IBEN-Genesis: Binary-to-Quaternary Mapping Algorithm
Translates standard binary data streams into quaternary state arrays.

This module implements the algorithmic mapping for converting binary sequences
into base-4 quaternary representations, enabling 2x data density compression
for the IBEN-Genesis peer-to-peer mesh framework.
"""

from typing import List, Tuple, Dict, Union
from enum import IntEnum
import struct


class QState(IntEnum):
    """Quaternary state enumeration."""
    NULL = 0      # 00: Ground state
    DIRECT = 1    # 01: Forward propagation
    COUNTER = 2   # 10: Reverse propagation
    SYNTROPIC = 3 # 11: Super-state overlay


class BinaryQuaternaryMapper:
    """
    Converts between binary and quaternary representations.
    
    Key Properties:
    - Each quaternary digit encodes exactly 2 bits
    - Achieves 50% reduction in symbol count vs binary
    - Supports variable-length padding for non-even bit counts
    """
    
    @staticmethod
    def bits_to_quaternary(bits: List[int]) -> List[int]:
        """
        Convert a list of bits (0s and 1s) to quaternary states.
        
        Args:
            bits: List of binary digits [0, 1, 0, 1, ...]
            
        Returns:
            List of quaternary states [0-3]
            
        Example:
            bits [0,0,0,1,1,0,1,1] → quaternary [0,1,2,3]
        """
        if not all(b in [0, 1] for b in bits):
            raise ValueError("Input must contain only 0s and 1s")
        
        # Pad with leading zero if odd length
        if len(bits) % 2 != 0:
            bits = [0] + bits
        
        quaternary = []
        for i in range(0, len(bits), 2):
            # Combine two bits into one quaternary digit
            q_value = bits[i] * 2 + bits[i + 1]
            quaternary.append(q_value)
        
        return quaternary
    
    @staticmethod
    def quaternary_to_bits(quaternary: List[int]) -> List[int]:
        """
        Convert quaternary states back to binary bits.
        
        Args:
            quaternary: List of quaternary states [0-3]
            
        Returns:
            List of binary digits [0, 1, ...]
        """
        if not all(q in [0, 1, 2, 3] for q in quaternary):
            raise ValueError("Input must contain only values 0-3")
        
        bits = []
        for q in quaternary:
            # Expand each quaternary digit to two bits
            bits.append((q >> 1) & 1)  # High bit
            bits.append(q & 1)          # Low bit
        
        return bits
    
    @staticmethod
    def bytes_to_quaternary(data: bytes) -> List[int]:
        """
        Convert byte array to quaternary state array.
        
        Each byte (8 bits) becomes 4 quaternary digits.
        
        Args:
            data: Raw bytes
            
        Returns:
            List of quaternary states [0-3]
        """
        bits = []
        for byte in data:
            for i in range(7, -1, -1):
                bits.append((byte >> i) & 1)
        
        return BinaryQuaternaryMapper.bits_to_quaternary(bits)
    
    @staticmethod
    def quaternary_to_bytes(quaternary: List[int]) -> bytes:
        """
        Convert quaternary state array back to bytes.
        
        Args:
            quaternary: List of quaternary states [0-3]
            
        Returns:
            Raw bytes
        """
        bits = BinaryQuaternaryMapper.quaternary_to_bits(quaternary)
        
        # Pad to multiple of 8 if needed
        while len(bits) % 8 != 0:
            bits = [0] + bits
        
        result = bytearray()
        for i in range(0, len(bits), 8):
            byte_val = 0
            for j in range(8):
                byte_val = (byte_val << 1) | bits[i + j]
            result.append(byte_val)
        
        return bytes(result)
    
    @staticmethod
    def string_to_quaternary(text: str, encoding: str = 'utf-8') -> List[int]:
        """
        Convert text string to quaternary state array.
        
        Args:
            text: Input string
            encoding: Character encoding (default: utf-8)
            
        Returns:
            List of quaternary states
        """
        data = text.encode(encoding)
        return BinaryQuaternaryMapper.bytes_to_quaternary(data)
    
    @staticmethod
    def quaternary_to_string(quaternary: List[int], encoding: str = 'utf-8') -> str:
        """
        Convert quaternary state array back to text string.
        
        Args:
            quaternary: List of quaternary states
            encoding: Character encoding (default: utf-8)
            
        Returns:
            Decoded string
        """
        data = BinaryQuaternaryMapper.quaternary_to_bytes(quaternary)
        return data.decode(encoding)
    
    @staticmethod
    def encode_integer(value: int, min_digits: int = 1) -> List[int]:
        """
        Encode an integer as quaternary digits (base-4 representation).
        
        Args:
            value: Non-negative integer
            min_digits: Minimum number of quaternary digits (padding with zeros)
            
        Returns:
            List of quaternary digits (most significant first)
        """
        if value < 0:
            raise ValueError("Only non-negative integers supported")
        
        if value == 0:
            return [0] * max(min_digits, 1)
        
        digits = []
        while value > 0:
            digits.append(value % 4)
            value //= 4
        
        # Reverse to get most significant first
        digits.reverse()
        
        # Pad to minimum length
        while len(digits) < min_digits:
            digits.insert(0, 0)
        
        return digits
    
    @staticmethod
    def decode_integer(quaternary: List[int]) -> int:
        """
        Decode quaternary digits back to integer.
        
        Args:
            quaternary: List of quaternary digits (most significant first)
            
        Returns:
            Integer value
        """
        if not all(q in [0, 1, 2, 3] for q in quaternary):
            raise ValueError("Input must contain only values 0-3")
        
        value = 0
        for digit in quaternary:
            value = value * 4 + digit
        
        return value
    
    @staticmethod
    def calculate_compression_ratio(original_bits: int) -> float:
        """
        Calculate the compression ratio achieved by quaternary encoding.
        
        Quaternary achieves exactly 2:1 compression (50% reduction).
        
        Args:
            original_bits: Number of bits in original binary representation
            
        Returns:
            Compression ratio (original_size / compressed_size)
        """
        quaternary_digits = (original_bits + 1) // 2
        if quaternary_digits == 0:
            return 1.0
        return original_bits / quaternary_digits
    
    @staticmethod
    def analyze_efficiency(data: bytes) -> Dict[str, Union[int, float]]:
        """
        Analyze the efficiency of quaternary encoding for given data.
        
        Args:
            data: Original binary data
            
        Returns:
            Dictionary with efficiency metrics
        """
        original_bits = len(data) * 8
        quaternary = BinaryQuaternaryMapper.bytes_to_quaternary(data)
        
        # Count state distribution
        state_counts = {0: 0, 1: 0, 2: 0, 3: 0}
        for q in quaternary:
            state_counts[q] += 1
        
        total = len(quaternary)
        
        return {
            'original_bits': original_bits,
            'quaternary_digits': len(quaternary),
            'compression_ratio': original_bits / len(quaternary) if quaternary else 0,
            'space_savings_percent': (1 - len(quaternary) / original_bits) * 100 if original_bits > 0 else 0,
            'state_distribution': state_counts,
            'state_frequencies': {k: v / total if total > 0 else 0 for k, v in state_counts.items()},
            'most_common_state': max(state_counts, key=state_counts.get),
        }


def demonstrate_mapping():
    """Demonstrate binary-to-quaternary mapping with examples."""
    print("=" * 60)
    print("IBEN-Genesis: Binary-to-Quaternary Mapping Algorithm")
    print("=" * 60)
    print()
    
    mapper = BinaryQuaternaryMapper()
    
    # Example 1: Simple bit mapping
    print("1. Basic Bit-to-Quaternary Mapping:")
    print("-" * 40)
    test_bits = [0, 0, 0, 1, 1, 0, 1, 1]
    quaternary = mapper.bits_to_quaternary(test_bits)
    recovered_bits = mapper.quaternary_to_bits(quaternary)
    
    print(f"  Original bits:  {test_bits}")
    print(f"  Quaternary:     {quaternary}")
    print(f"  Recovered bits: {recovered_bits}")
    print(f"  Lossless:       {test_bits == recovered_bits}")
    print()
    
    # Example 2: Byte conversion
    print("2. Byte Array Conversion:")
    print("-" * 40)
    test_bytes = b"IBEN"
    quaternary = mapper.bytes_to_quaternary(test_bytes)
    recovered_bytes = mapper.quaternary_to_bytes(quaternary)
    
    print(f"  Original bytes:  {test_bytes}")
    print(f"  Original bits:   {len(test_bytes) * 8}")
    print(f"  Quaternary:      {quaternary}")
    print(f"  Quat. digits:    {len(quaternary)}")
    print(f"  Recovered bytes: {recovered_bytes}")
    print(f"  Lossless:        {test_bytes == recovered_bytes}")
    print()
    
    # Example 3: String encoding
    print("3. Text String Encoding:")
    print("-" * 40)
    test_string = "Genesis Mesh Network"
    quaternary = mapper.string_to_quaternary(test_string)
    recovered_string = mapper.quaternary_to_string(quaternary)
    
    print(f"  Original:     '{test_string}'")
    print(f"  Original bits: {len(test_string.encode('utf-8')) * 8}")
    print(f"  Quaternary:    {quaternary[:20]}... ({len(quaternary)} digits)")
    print(f"  Recovered:    '{recovered_string}'")
    print(f"  Lossless:      {test_string == recovered_string}")
    print()
    
    # Example 4: Integer encoding
    print("4. Integer Base-4 Encoding:")
    print("-" * 40)
    test_integers = [0, 1, 15, 255, 1024, 65535]
    for val in test_integers:
        encoded = mapper.encode_integer(val)
        decoded = mapper.decode_integer(encoded)
        print(f"  {val:6d} → {encoded} → {decoded} ✓" if val == decoded else f"  ERROR!")
    print()
    
    # Example 5: Efficiency analysis
    print("5. Compression Efficiency Analysis:")
    print("-" * 40)
    sample_data = b"The quick brown fox jumps over the lazy dog."
    analysis = mapper.analyze_efficiency(sample_data)
    
    print(f"  Sample data: '{sample_data.decode()}'")
    print(f"  Original size:    {analysis['original_bits']} bits")
    print(f"  Quaternary size:  {analysis['quaternary_digits']} digits")
    print(f"  Compression ratio: {analysis['compression_ratio']:.2f}x")
    print(f"  Space savings:    {analysis['space_savings_percent']:.1f}%")
    print(f"  State distribution:")
    for state, count in analysis['state_distribution'].items():
        name = ['NULL', 'DIRECT', 'COUNTER', 'SYNTROPIC'][state]
        freq = analysis['state_frequencies'][state]
        print(f"    {name}: {count} ({freq*100:.1f}%)")
    print(f"  Most common state: {['NULL', 'DIRECT', 'COUNTER', 'SYNTROPIC'][analysis['most_common_state']]}")
    print()
    
    # Example 6: Theoretical radix economy
    print("6. Radix Economy Comparison:")
    print("-" * 40)
    print("  Base-2 (Binary):   radix_cost = 2 × ln(2) ≈ 1.386")
    print("  Base-4 (Quaternary): radix_cost = 4 × ln(4) ≈ 5.545")
    print("  Optimal (e ≈ 2.718): radix_cost = e × ln(e) ≈ 2.718")
    print()
    print("  Note: While base-e is theoretically optimal,")
    print("        base-4 provides practical hardware benefits")
    print("        with exact 2-bit grouping and symmetric states.")
    print()
    
    # Verify round-trip integrity
    print("7. Round-Trip Integrity Verification:")
    print("-" * 40)
    test_cases = [
        b"",
        b"\x00",
        b"\xFF",
        b"Hello, World!",
        b"\x00\x01\x02\x03\xFF\xFE\xFD",
        "Unicode: 你好世界 🌐".encode('utf-8'),
    ]
    
    all_passed = True
    for i, data in enumerate(test_cases):
        quaternary = mapper.bytes_to_quaternary(data)
        recovered = mapper.quaternary_to_bytes(quaternary)
        passed = data == recovered
        all_passed = all_passed and passed
        status = "✓" if passed else "✗"
        print(f"  Test {i+1}: {status} ({len(data)} bytes → {len(quaternary)} quat.)")
    
    print()
    if all_passed:
        print("✓ All round-trip tests passed!")
    else:
        print("✗ Some tests failed!")


if __name__ == "__main__":
    demonstrate_mapping()
