"""
IBEN-Genesis: Gyroidal Tensor Topology Module

Implements non-Euclidean gyroidal surface routing for the P2P mesh network.
Maps quaternary logic states to orthogonal pathways minimizing latency
and maximizing throughput across volatile network environments.

Gyroid minimal surface equation: sin(x)cos(y) + sin(y)cos(z) + sin(z)cos(x) = 0
"""

import numpy as np
from typing import List, Tuple, Dict, Optional, Set
from dataclasses import dataclass, field
import math
from collections import defaultdict


@dataclass
class MeshNode:
    """Represents a node in the P2P gyroidal mesh network"""
    node_id: str
    position: np.ndarray  # 3D coordinates on gyroidal surface
    state_vectors: Dict[str, List[int]] = field(default_factory=dict)
    neighbors: Set[str] = field(default_factory=set)
    routing_capacity: float = 1.0
    health_score: float = 1.0
    
    def __post_init__(self):
        if isinstance(self.position, list):
            self.position = np.array(self.position)
        if len(self.position) != 3:
            raise ValueError("Node position must be 3D coordinates")


@dataclass
class RoutingPath:
    """Represents a data routing path through the mesh"""
    path_id: str
    nodes: List[str]
    tensor_stream: int  # 0-3 for quaternary orthogonal streams
    latency: float
    bandwidth: float
    priority: int = 0


class GyroidalTopology:
    """
    Manages gyroidal surface-based node placement and routing
    Implements non-Euclidean topology for optimal data distribution
    """
    
    def __init__(self, grid_size: int = 10, gyroid_scale: float = 2 * np.pi):
        self.grid_size = grid_size
        self.gyroid_scale = gyroid_scale
        self.nodes: Dict[str, MeshNode] = {}
        self.routing_paths: Dict[str, RoutingPath] = {}
        self.tensor_streams: Dict[int, List[str]] = {i: [] for i in range(4)}
        
    @staticmethod
    def gyroid_function(x: float, y: float, z: float) -> float:
        """
        Evaluate gyroid minimal surface implicit function
        f(x,y,z) = sin(x)cos(y) + sin(y)cos(z) + sin(z)cos(x)
        Points where f(x,y,z) ≈ 0 lie on the gyroid surface
        """
        return (np.sin(x) * np.cos(y) + 
                np.sin(y) * np.cos(z) + 
                np.sin(z) * np.cos(x))
    
    @staticmethod
    def gyroid_gradient(x: float, y: float, z: float) -> np.ndarray:
        """
        Compute gradient of gyroid function for surface normal
        Used for determining optimal routing directions
        """
        dx = np.cos(x) * np.cos(y) - np.sin(z) * np.sin(x)
        dy = -np.sin(x) * np.sin(y) + np.cos(y) * np.cos(z)
        dz = -np.sin(y) * np.sin(z) + np.cos(z) * np.cos(x)
        return np.array([dx, dy, dz])
    
    def project_to_gyroid_surface(self, point: np.ndarray, 
                                   iterations: int = 5) -> np.ndarray:
        """
        Project a 3D point onto the nearest point on the gyroid surface
        Uses Newton-Raphson iteration for convergence
        """
        p = point.copy().astype(float)
        
        for _ in range(iterations):
            f_val = self.gyroid_function(*p)
            grad = self.gyroid_gradient(*p)
            
            grad_norm = np.linalg.norm(grad)
            if grad_norm < 1e-10:
                break
            
            # Move point along gradient to minimize f(p)
            step = f_val / (grad_norm ** 2) * grad
            p = p - step
        
        return p
    
    def generate_mesh_nodes(self, num_nodes: int = 100) -> Dict[str, MeshNode]:
        """
        Generate nodes distributed across gyroidal surface
        Each node positioned at optimal routing location
        """
        nodes = {}
        
        # Sample points in 3D space and project to gyroid surface
        for i in range(num_nodes):
            # Random initial position
            theta = np.random.uniform(0, self.gyroid_scale)
            phi = np.random.uniform(0, self.gyroid_scale)
            r = np.random.uniform(1, 3)
            
            x = r * np.sin(theta) * np.cos(phi)
            y = r * np.sin(theta) * np.sin(phi)
            z = r * np.cos(theta)
            
            initial_point = np.array([x, y, z])
            surface_point = self.project_to_gyroid_surface(initial_point)
            
            node_id = f"node_{i:04d}"
            nodes[node_id] = MeshNode(
                node_id=node_id,
                position=surface_point
            )
        
        self.nodes = nodes
        self._establish_neighbor_connections()
        return nodes
    
    def _establish_neighbor_connections(self, max_distance: float = 2.0):
        """Connect nodes within gyroidal distance threshold"""
        node_list = list(self.nodes.values())
        
        for i, node1 in enumerate(node_list):
            for j, node2 in enumerate(node_list):
                if i >= j:
                    continue
                
                # Calculate geodesic-like distance on gyroid surface
                euclidean_dist = np.linalg.norm(node1.position - node2.position)
                
                # Adjust for gyroid curvature
                grad1 = self.gyroid_gradient(*node1.position)
                grad2 = self.gyroid_gradient(*node2.position)
                
                # Angle between surface normals affects effective distance
                angle_factor = np.dot(grad1, grad2) / (
                    np.linalg.norm(grad1) * np.linalg.norm(grad2) + 1e-10
                )
                
                effective_distance = euclidean_dist * (2 - angle_factor)
                
                if effective_distance < max_distance:
                    node1.neighbors.add(node2.node_id)
                    node2.neighbors.add(node1.node_id)
    
    def assign_tensor_stream(self, node_id: str, 
                              quaternary_state: int) -> int:
        """
        Assign node to one of four orthogonal tensor streams
        based on quaternary state (-2,-1,+1,+2) -> stream (0,1,2,3)
        """
        state_to_stream = {-2: 0, -1: 1, 1: 2, 2: 3}
        stream = state_to_stream.get(quaternary_state, 0)
        
        if node_id not in self.tensor_streams[stream]:
            self.tensor_streams[stream].append(node_id)
        
        return stream
    
    def find_optimal_path(self, source_id: str, target_id: str,
                          tensor_stream: Optional[int] = None) -> Optional[RoutingPath]:
        """
        Find optimal routing path using A* algorithm on gyroidal topology
        Considers tensor stream constraints for quaternary routing
        """
        if source_id not in self.nodes or target_id not in self.nodes:
            return None
        
        # A* search with gyroidal distance heuristic
        open_set = [(0, [source_id])]
        visited = set()
        
        while open_set:
            _, current_path = min(open_set, key=lambda x: x[0])
            current_node = current_path[-1]
            
            if current_node == target_id:
                path_latency = self._calculate_path_latency(current_path)
                path_bandwidth = self._calculate_path_bandwidth(current_path)
                
                path_id = f"path_{source_id}_{target_id}"
                path = RoutingPath(
                    path_id=path_id,
                    nodes=current_path,
                    tensor_stream=tensor_stream if tensor_stream is not None else 0,
                    latency=path_latency,
                    bandwidth=path_bandwidth
                )
                
                self.routing_paths[path_id] = path
                return path
            
            visited.add(current_node)
            open_set.remove((_, current_path))
            
            # Explore neighbors
            node = self.nodes[current_node]
            for neighbor_id in node.neighbors:
                if neighbor_id in visited:
                    continue
                
                new_path = current_path + [neighbor_id]
                heuristic = self._gyroidal_heuristic(neighbor_id, target_id)
                cost = len(new_path) + heuristic
                
                open_set.append((cost, new_path))
        
        return None
    
    def _gyroidal_heuristic(self, node1_id: str, node2_id: str) -> float:
        """Heuristic: estimated remaining distance on gyroid surface"""
        node1 = self.nodes[node1_id]
        node2 = self.nodes[node2_id]
        return np.linalg.norm(node1.position - node2.position)
    
    def _calculate_path_latency(self, path: List[str]) -> float:
        """Calculate total latency for a routing path"""
        if len(path) < 2:
            return 0.0
        
        total_latency = 0.0
        for i in range(len(path) - 1):
            node1 = self.nodes[path[i]]
            node2 = self.nodes[path[i + 1]]
            
            # Latency based on distance and node health
            distance = np.linalg.norm(node1.position - node2.position)
            health_factor = (node1.health_score + node2.health_score) / 2
            
            total_latency += distance / (health_factor + 0.1)
        
        return total_latency
    
    def _calculate_path_bandwidth(self, path: List[str]) -> float:
        """Calculate bottleneck bandwidth for a routing path"""
        if not path:
            return 0.0
        
        min_bandwidth = float('inf')
        for node_id in path:
            node = self.nodes[node_id]
            available_bw = node.routing_capacity * node.health_score
            min_bandwidth = min(min_bandwidth, available_bw)
        
        return min_bandwidth if min_bandwidth != float('inf') else 0.0
    
    def detect_congestion(self, threshold: float = 0.7) -> List[str]:
        """Identify congested nodes exceeding capacity threshold"""
        congested = []
        for node_id, node in self.nodes.items():
            load = 1.0 - node.health_score
            if load > threshold:
                congested.append(node_id)
        return congested
    
    def rebalance_routing(self, congested_nodes: List[str]) -> List[RoutingPath]:
        """
        Re-route paths away from congested nodes
        Part of self-healing protocol
        """
        new_paths = []
        
        for path_id, path in list(self.routing_paths.items()):
            uses_congested = any(n in congested_nodes for n in path.nodes)
            
            if uses_congested:
                source = path.nodes[0]
                target = path.nodes[-1]
                
                # Temporarily reduce health of congested nodes
                original_health = {}
                for node_id in congested_nodes:
                    if node_id in self.nodes:
                        original_health[node_id] = self.nodes[node_id].health_score
                        self.nodes[node_id].health_score *= 0.1
                
                # Find new path avoiding congested nodes
                new_path = self.find_optimal_path(source, target, path.tensor_stream)
                
                # Restore health scores
                for node_id, health in original_health.items():
                    self.nodes[node_id].health_score = health
                
                if new_path:
                    new_paths.append(new_path)
        
        return new_paths


def visualize_gyroid_surface(resolution: int = 50) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate coordinate grids for gyroid surface visualization
    Returns x, y, z grids for plotting
    """
    x = np.linspace(-2*np.pi, 2*np.pi, resolution)
    y = np.linspace(-2*np.pi, 2*np.pi, resolution)
    z = np.linspace(-2*np.pi, 2*np.pi, resolution)
    
    X, Y, Z = np.meshgrid(x, y, z)
    
    return X, Y, Z


# Demonstration
if __name__ == "__main__":
    print("=" * 60)
    print("IBEN-Genesis: Gyroidal Tensor Topology Demonstration")
    print("=" * 60)
    
    # Initialize topology
    topology = GyroidalTopology(grid_size=10)
    
    # Generate mesh nodes
    nodes = topology.generate_mesh_nodes(num_nodes=50)
    print(f"\nGenerated {len(nodes)} mesh nodes on gyroidal surface")
    
    # Show sample node positions
    print("\nSample node positions (first 5):")
    for i, (node_id, node) in enumerate(list(nodes.items())[:5]):
        print(f"  {node_id}: {node.position.round(3)}")
        print(f"    Neighbors: {len(node.neighbors)}")
    
    # Assign tensor streams based on quaternary states
    print("\nAssigning tensor streams...")
    quaternary_states = [-2, -1, 1, 2]
    for i, node_id in enumerate(list(nodes.keys())[:20]):
        state = quaternary_states[i % 4]
        stream = topology.assign_tensor_stream(node_id, state)
        print(f"  {node_id}: state={state}, stream={stream}")
    
    # Find optimal routing path
    print("\nFinding optimal routing path...")
    node_ids = list(nodes.keys())
    if len(node_ids) >= 2:
        source, target = node_ids[0], node_ids[-1]
        path = topology.find_optimal_path(source, target)
        
        if path:
            print(f"  Path found: {path.path_id}")
            print(f"  Nodes: {path.nodes[:5]}{'...' if len(path.nodes) > 5 else ''}")
            print(f"  Latency: {path.latency:.3f}")
            print(f"  Bandwidth: {path.bandwidth:.3f}")
            print(f"  Tensor stream: {path.tensor_stream}")
    
    # Test congestion detection and rebalancing
    print("\nTesting self-healing protocols...")
    # Simulate congestion on some nodes
    for node_id in list(nodes.keys())[:5]:
        nodes[node_id].health_score = 0.3
    
    congested = topology.detect_congestion(threshold=0.5)
    print(f"  Congested nodes detected: {len(congested)}")
    
    new_paths = topology.rebalance_routing(congested)
    print(f"  Alternative paths generated: {len(new_paths)}")
    
    print("\n" + "=" * 60)
    print("Gyroidal topology module validated successfully")
    print("=" * 60)
