#!/usr/bin/env python3
"""
IBEN-Genesis: Quaternary Logic Gate Framework
Implements truth tables and hardware gate equivalents for base-4 algebraic operations.

State Mapping:
  0 (00): Null/Ground - Absolute rest, network isolation
  1 (01): True/Direct - Forward propagation, nominal validation
  2 (10): Inverted/Counter - Reverse propagation, negative parity
  3 (11): Syntropic/Overlay - Quantum-resistant super-state, multidimensional routing
"""

from typing import List, Tuple, Dict
from enum import IntEnum
import numpy as np


class QState(IntEnum):
    """Quaternary state enumeration with semantic labels."""
    NULL = 0      # 00: Ground state
    DIRECT = 1    # 01: Forward propagation
    COUNTER = 2   # 10: Reverse propagation
    SYNTROPIC = 3 # 11: Super-state overlay


class QuaternaryGates:
    """Implementation of quaternary logic gates and truth tables."""
    
    @staticmethod
    def NOT(x: int) -> int:
        """
        Quaternary Inversion (NOT Operator)
        Maps high energy states symmetrically to low energy states.
        Formula: NOT(x) = 3 - x
        
        Truth Table:
          x | NOT(x)
          0 |   3
          1 |   2
          2 |   1
          3 |   0
        """
        if x not in [0, 1, 2, 3]:
            raise ValueError(f"Invalid quaternary state: {x}")
        return 3 - x
    
    @staticmethod
    def AND(x: int, y: int) -> int:
        """
        Quaternary AND (Minimum Operator)
        Returns the minimum state value - conservative conjunction.
        Formula: AND(x, y) = min(x, y)
        
        Truth Table (4x4):
            AND | 0  1  2  3
            ----+-----------
             0  | 0  0  0  0
             1  | 0  1  1  1
             2  | 0  1  2  2
             3  | 0  1  2  3
        """
        if x not in [0, 1, 2, 3] or y not in [0, 1, 2, 3]:
            raise ValueError(f"Invalid quaternary states: {x}, {y}")
        return min(x, y)
    
    @staticmethod
    def OR(x: int, y: int) -> int:
        """
        Quaternary OR (Maximum Operator)
        Returns the maximum state value - liberal disjunction.
        Formula: OR(x, y) = max(x, y)
        
        Truth Table (4x4):
            OR | 0  1  2  3
           ----+-----------
            0  | 0  1  2  3
            1  | 1  1  2  3
            2  | 2  2  2  3
            3  | 3  3  3  3
        """
        if x not in [0, 1, 2, 3] or y not in [0, 1, 2, 3]:
            raise ValueError(f"Invalid quaternary states: {x}, {y}")
        return max(x, y)
    
    @staticmethod
    def XOR(x: int, y: int) -> int:
        """
        Quaternary XOR (Absolute Difference Operator)
        Returns the absolute difference between states.
        Formula: XOR(x, y) = |x - y|
        
        Truth Table (4x4):
            XOR | 0  1  2  3
            ----+-----------
             0  | 0  1  2  3
             1  | 1  0  1  2
             2  | 2  1  0  1
             3  | 3  2  1  0
        """
        if x not in [0, 1, 2, 3] or y not in [0, 1, 2, 3]:
            raise ValueError(f"Invalid quaternary states: {x}, {y}")
        return abs(x - y)
    
    @staticmethod
    def NAND(x: int, y: int) -> int:
        """
        Quaternary NAND (NOT-AND Operator)
        Formula: NAND(x, y) = NOT(AND(x, y)) = 3 - min(x, y)
        """
        return QuaternaryGates.NOT(QuaternaryGates.AND(x, y))
    
    @staticmethod
    def NOR(x: int, y: int) -> int:
        """
        Quaternary NOR (NOT-OR Operator)
        Formula: NOR(x, y) = NOT(OR(x, y)) = 3 - max(x, y)
        """
        return QuaternaryGates.NOT(QuaternaryGates.OR(x, y))
    
    @staticmethod
    def XNOR(x: int, y: int) -> int:
        """
        Quaternary XNOR (Equivalence Operator)
        Returns 3 - |x - y|, highest when states match.
        """
        return 3 - abs(x - y)
    
    @staticmethod
    def CONSENSUS(states: List[int]) -> int:
        """
        Syntropic Consensus (MAX Operator)
        Multi-party validation using maximum-state resolution.
        Formula: CONSENSUS(x₁, x₂, ..., xₙ) = max(x₁, x₂, ..., xₙ)
        
        Used for ledger finality across conflicting data paths.
        """
        if not all(s in [0, 1, 2, 3] for s in states):
            raise ValueError(f"Invalid quaternary states in consensus: {states}")
        if len(states) == 0:
            raise ValueError("Consensus requires at least one state")
        return max(states)
    
    @staticmethod
    def BALANCE(states: List[int]) -> int:
        """
        Balanced State Resolution
        Computes the algebraic sum with symmetric bipolar mapping:
        0→0, 1→+1, 2→-1, 3→0 (neutral overlay)
        Returns the sign of the sum as a quaternary state.
        """
        bipolar_map = {0: 0, 1: 1, 2: -1, 3: 0}
        total = sum(bipolar_map[s] for s in states)
        
        if total > 0:
            return QState.DIRECT
        elif total < 0:
            return QState.COUNTER
        else:
            return QState.NULL
    
    @classmethod
    def generate_truth_table(cls, operation: str) -> str:
        """Generate formatted truth table for any quaternary operation."""
        ops = {
            'NOT': lambda x: cls.NOT(x),
            'AND': lambda x, y: cls.AND(x, y),
            'OR': lambda x, y: cls.OR(x, y),
            'XOR': lambda x, y: cls.XOR(x, y),
            'NAND': lambda x, y: cls.NAND(x, y),
            'NOR': lambda x, y: cls.NOR(x, y),
            'XNOR': lambda x, y: cls.XNOR(x, y),
        }
        
        if operation not in ops:
            raise ValueError(f"Unknown operation: {operation}")
        
        op_func = ops[operation]
        
        if operation == 'NOT':
            table = "NOT Truth Table:\n"
            table += "  x | NOT(x)\n"
            table += "  --+--------\n"
            for x in range(4):
                result = op_func(x)
                table += f"  {x} |   {result}\n"
        else:
            table = f"{operation} Truth Table:\n"
            table += f"  {operation} | 0  1  2  3\n"
            table += "  ----------+-----------\n"
            for x in range(4):
                row = f"     {x}    |"
                for y in range(4):
                    result = op_func(x, y)
                    row += f" {result}  "
                table += row + "\n"
        
        return table
    
    @classmethod
    def verify_gate_properties(cls) -> Dict[str, bool]:
        """Verify fundamental logic gate properties for quaternary system."""
        results = {}
        
        # Test involution: NOT(NOT(x)) = x
        results['NOT_involution'] = all(cls.NOT(cls.NOT(x)) == x for x in range(4))
        
        # Test commutativity: AND(x,y) = AND(y,x), etc.
        results['AND_commutative'] = all(
            cls.AND(x, y) == cls.AND(y, x) for x in range(4) for y in range(4)
        )
        results['OR_commutative'] = all(
            cls.OR(x, y) == cls.OR(y, x) for x in range(4) for y in range(4)
        )
        results['XOR_commutative'] = all(
            cls.XOR(x, y) == cls.XOR(y, x) for x in range(4) for y in range(4)
        )
        
        # Test associativity
        results['AND_associative'] = all(
            cls.AND(cls.AND(x, y), z) == cls.AND(x, cls.AND(y, z))
            for x in range(4) for y in range(4) for z in range(4)
        )
        results['OR_associative'] = all(
            cls.OR(cls.OR(x, y), z) == cls.OR(x, cls.OR(y, z))
            for x in range(4) for y in range(4) for z in range(4)
        )
        
        # Test De Morgan's Laws: NOT(AND(x,y)) = OR(NOT(x), NOT(y))
        results['de_morgan_1'] = all(
            cls.NAND(x, y) == cls.NOR(cls.NOT(x), cls.NOT(y))
            for x in range(4) for y in range(4)
        )
        
        # Test identity elements
        results['AND_identity_3'] = all(cls.AND(x, 3) == x for x in range(4))  # 3 is identity for AND
        results['OR_identity_0'] = all(cls.OR(x, 0) == x for x in range(4))    # 0 is identity for OR
        
        return results


def demonstrate_gate_operations():
    """Demonstrate all quaternary gate operations with examples."""
    print("=" * 60)
    print("IBEN-Genesis: Quaternary Logic Gate Framework")
    print("=" * 60)
    print()
    
    gates = QuaternaryGates()
    
    # Display all truth tables
    for op in ['NOT', 'AND', 'OR', 'XOR', 'NAND', 'NOR', 'XNOR']:
        print(gates.generate_truth_table(op))
        print()
    
    # Verify gate properties
    print("Gate Property Verification:")
    print("-" * 40)
    properties = gates.verify_gate_properties()
    for prop, result in properties.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {prop}: {status}")
    print()
    
    # Demonstrate consensus mechanism
    print("Syntropic Consensus Examples:")
    print("-" * 40)
    test_cases = [
        [1, 1, 2, 1],  # Majority direct
        [2, 2, 1, 2],  # Majority counter
        [0, 1, 2, 3],  # Mixed states
        [3, 3, 3, 3],  # All syntropic
    ]
    for case in test_cases:
        result = gates.CONSENSUS(case)
        state_name = ['NULL', 'DIRECT', 'COUNTER', 'SYNTROPIC'][result]
        print(f"  CONSENSUS{case} = {result} ({state_name})")
    print()
    
    # Demonstrate balance resolution
    print("Balanced State Resolution Examples:")
    print("-" * 40)
    balance_cases = [
        [1, 1, 1],      # Positive sum
        [2, 2, 2],      # Negative sum
        [1, 2],         # Cancel out
        [1, 1, 2, 2],   # Perfect balance
        [3, 3, 1],      # Syntropic neutral + direct
    ]
    for case in balance_cases:
        result = gates.BALANCE(case)
        state_name = ['NULL', 'DIRECT', 'COUNTER', 'SYNTROPIC'][result]
        print(f"  BALANCE{case} = {result} ({state_name})")
    print()
    
    # Show bit representation mapping
    print("Quaternary State Bit Mapping:")
    print("-" * 40)
    for i in range(4):
        bits = format(i, '02b')
        name = ['NULL/Ground', 'Direct/Forward', 'Counter/Reverse', 'Syntropic/Overlay'][i]
        print(f"  {i} ({bits}): {name}")
    print()


if __name__ == "__main__":
    demonstrate_gate_operations()
    
    # Run property verification
    gates = QuaternaryGates()
    props = gates.verify_gate_properties()
    if all(props.values()):
        print("\n✓ All quaternary gate properties verified successfully!")
    else:
        failed = [k for k, v in props.items() if not v]
        print(f"\n✗ Failed properties: {failed}")
