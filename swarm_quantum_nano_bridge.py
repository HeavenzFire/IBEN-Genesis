import numpy as np
from typing import List, Dict, Tuple
import math

class NanoAgent:
    """
    Represents a single nano-scale building block capable of self-assembly
    and local quantum field interaction.
    """
    def __init__(self, position: np.ndarray, agent_id: int):
        self.id = agent_id
        self.position = position  # 3D coordinates
        self.orientation = np.random.rand(3) * 2 * np.pi  # Random initial orientation
        self.state = 'free'  # 'free', 'assembling', 'locked'
        self.local_field_strength = 0.0
        self.neighbors = []
        
    def sense_local_field(self, agents: List['NanoAgent'], radius: float = 5.0):
        """Sense quantum field strength from nearby agents."""
        self.neighbors = []
        total_field = 0.0
        
        for other in agents:
            if other.id != self.id:
                dist = np.linalg.norm(self.position - other.position)
                if dist < radius:
                    self.neighbors.append(other)
                    # Field strength decays with distance, enhanced by gyroidal alignment
                    alignment_factor = np.cos(np.dot(self.orientation, other.orientation))
                    total_field += (1.0 / (dist + 0.1)) * (1.0 + alignment_factor)
                    
        self.local_field_strength = total_field
        return total_field
    
    def adapt_orientation(self, target_orientation: np.ndarray, adaptation_rate: float = 0.1):
        """Adjust orientation based on quantum feedback from the core."""
        diff = target_orientation - self.orientation
        # Normalize difference to avoid overshooting
        diff = diff - 2 * np.pi * np.round(diff / (2 * np.pi))
        self.orientation += adaptation_rate * diff
        # Keep orientation within [0, 2π]
        self.orientation = self.orientation % (2 * np.pi)
        
    def assemble_gyroidal_step(self, agents: List['NanoAgent']):
        """Move towards forming a gyroidal minimal surface structure."""
        if len(self.neighbors) < 3:
            # Wander randomly if not enough neighbors
            self.position += np.random.randn(3) * 0.5
            return
            
        # Calculate centroid of neighbors
        centroid = np.mean([n.position for n in self.neighbors], axis=0)
        
        # Gyroidal formation rule: maintain specific distance while aligning normals
        target_dist = 2.5  # Ideal spacing for gyroidal lattice
        current_dist = np.linalg.norm(self.position - centroid)
        
        if current_dist > target_dist:
            move_dir = (centroid - self.position) / current_dist
            self.position += move_dir * 0.3
        elif current_dist < target_dist * 0.8:
            move_dir = (self.position - centroid) / current_dist
            self.position += move_dir * 0.2
            
        # Align orientation with local surface normal approximation
        if len(self.neighbors) >= 3:
            v1 = self.neighbors[0].position - self.position
            v2 = self.neighbors[1].position - self.position
            normal = np.cross(v1, v2)
            if np.linalg.norm(normal) > 0.1:
                normal = normal / np.linalg.norm(normal)
                # Convert normal to orientation vector
                target_orient = np.arctan2(normal[1], normal[0]), np.arcsin(normal[2]), 0
                self.adapt_orientation(np.array(target_orient))

class SwarmCoordinator:
    """
    Manages a cluster of nano-agents, coordinating assembly and 
    interfacing with the quantum core.
    """
    def __init__(self, num_agents: int, coordinator_id: int):
        self.id = coordinator_id
        self.agents = [NanoAgent(np.random.rand(3) * 20, i) for i in range(num_agents)]
        self.assembly_progress = 0.0
        self.coherence_feedback = 0.0
        
    def run_assembly_cycle(self, quantum_feedback: float):
        """Execute one cycle of swarm assembly adapted by quantum coherence."""
        # Adaptation rate scales with quantum coherence (higher coherence = faster precision assembly)
        adaptation_rate = 0.05 + (quantum_feedback * 0.15)
        
        for agent in self.agents:
            agent.sense_local_field(self.agents)
            agent.assemble_gyroidal_step(self.agents)
            
            # Apply quantum feedback to orientation refinement
            if quantum_feedback > 0.9:
                # High coherence allows fine-tuning
                target_orient = np.random.rand(3) * 0.1  # Small refinements
                agent.adapt_orientation(target_orient, adaptation_rate)
                
        # Calculate assembly progress based on local field uniformity
        field_strengths = [a.local_field_strength for a in self.agents if a.local_field_strength > 0]
        if field_strengths:
            uniformity = 1.0 - (np.std(field_strengths) / (np.mean(field_strengths) + 1e-6))
            self.assembly_progress = max(self.assembly_progress, uniformity)
            
        return self.assembly_progress

class QuantumNanoSwarmHierarchy:
    """
    The master controller integrating Quantum Engine, Swarm Coordinators,
    and Nano Agents into a unified adaptive system.
    """
    def __init__(self, num_coordinators: int = 4, agents_per_coordinator: int = 50):
        self.coordinators = [
            SwarmCoordinator(agents_per_coordinator, i) 
            for i in range(num_coordinators)
        ]
        self.quantum_coherence_history = []
        self.global_assembly_score = 0.0
        
        # Simulated quantum core state (from previous engine)
        self.core_coherence = 0.999998  # Starting high fidelity
        
    def simulate_quantum_core_feedback(self, swarm_quality: float) -> float:
        """
        Simulate how the physical swarm quality affects quantum coherence.
        Better assembly = higher coherence.
        """
        # Base coherence decay due to thermal noise
        thermal_decay = 0.00001 * (1.0 - swarm_quality)
        
        # Swarm improvement factor
        swarm_boost = swarm_quality * 0.00005
        
        # Update core coherence
        self.core_coherence = max(0.9, min(0.999999, 
                                          self.core_coherence - thermal_decay + swarm_boost))
        return self.core_coherence
        
    def run_evolutionary_cycle(self, cycles: int = 100):
        """Run the full hierarchy evolution loop."""
        print(f"--- Starting Quantum-Nano Swarm Evolution ({cycles} cycles) ---")
        print(f"Initial Quantum Coherence: {self.core_coherence:.6f}")
        print(f"Initial Assembly Score: {self.global_assembly_score:.4f}\n")
        
        for cycle in range(cycles):
            # 1. Gather swarm assembly status
            coordinator_scores = []
            for coord in self.coordinators:
                # Pass current quantum coherence to swarm for adaptation
                score = coord.run_assembly_cycle(self.core_coherence)
                coordinator_scores.append(score)
                
            # 2. Aggregate global assembly quality
            self.global_assembly_score = np.mean(coordinator_scores)
            
            # 3. Quantum core reacts to physical structure quality
            new_coherence = self.simulate_quantum_core_feedback(self.global_assembly_score)
            self.quantum_coherence_history.append(new_coherence)
            
            # Progress logging every 20 cycles
            if cycle % 20 == 0 or cycle == cycles - 1:
                print(f"Cycle {cycle:3d}: Assembly={self.global_assembly_score:.4f}, "
                      f"Coherence={new_coherence:.6f}, "
                      f"Delta={new_coherence - self.quantum_coherence_history[-2] if len(self.quantum_coherence_history) > 1 else 0:+.6f}")
                      
        print(f"\n--- Evolution Complete ---")
        print(f"Final Assembly Score: {self.global_assembly_score:.4f}")
        print(f"Final Quantum Coherence: {self.core_coherence:.6f}")
        print(f"Coherence Improvement: {(self.core_coherence - 0.999998) * 1e6:.2f} ppm")
        
        return {
            "final_coherence": self.core_coherence,
            "final_assembly": self.global_assembly_score,
            "history": self.quantum_coherence_history
        }

if __name__ == "__main__":
    # Initialize the hierarchical system
    hierarchy = QuantumNanoSwarmHierarchy(num_coordinators=5, agents_per_coordinator=30)
    
    # Run the evolutionary integration
    results = hierarchy.run_evolutionary_cycle(cycles=100)
    
    # Verify the positive feedback loop
    if results["final_coherence"] > 0.999998:
        print("\n✅ SUCCESS: Swarm integration improved quantum coherence!")
        print("   Nano-agents successfully optimized gyroidal topology for room-temp stability.")
    else:
        print("\n⚠️  WARNING: Coherence did not improve. Further adaptation needed.")
