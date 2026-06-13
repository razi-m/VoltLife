import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface ImpactSceneProps {
  active: boolean;
}

interface Node {
  name: string;
  position: [number, number, number];
  color: string;
}

export const ImpactScene: React.FC<ImpactSceneProps> = ({ active }) => {
  const groupRef = useRef<THREE.Group>(null);
  
  // Destination nodes across simulated second-life grid
  const nodes: Node[] = useMemo(() => [
    { name: 'Bhadla Solar, RJ', position: [-2.2, 1.2, -0.5], color: '#f59e0b' },
    { name: 'Leh Microgrid, JK', position: [2.0, 1.5, 0.5], color: '#4d8eff' },
    { name: 'Tamil Nadu Wind, TN', position: [1.8, -1.2, -0.5], color: '#4edea3' },
    { name: 'Rural Microgrid, UP', position: [-2.0, -1.0, 0.8], color: '#38bdf8' }
  ], []);

  // Generate particles that flow along curved trajectories from center (0,0,0) to each destination
  const particleCount = 24;
  const particles = useMemo(() => {
    const data = [];
    for (let i = 0; i < particleCount; i++) {
      const nodeIndex = i % nodes.length;
      const speed = 0.5 + Math.random() * 0.5;
      const delay = Math.random() * 2;
      const offset = new THREE.Vector3(
        (Math.random() - 0.5) * 0.4,
        (Math.random() - 0.5) * 0.4,
        (Math.random() - 0.5) * 0.4
      );
      data.push({ nodeIndex, speed, delay, offset });
    }
    return data;
  }, [nodes]);

  // Mesh references for animating flowing particles
  const particleRefs = useRef<THREE.Mesh[]>([]);

  useFrame((state) => {
    if (!active) return;
    const time = state.clock.getElapsedTime();
    
    // Rotate overall scene slightly
    if (groupRef.current) {
      groupRef.current.rotation.y = time * 0.05;
    }

    // Animate flow of each particle
    particles.forEach((p, idx) => {
      const mesh = particleRefs.current[idx];
      if (!mesh) return;

      const targetNode = nodes[p.nodeIndex];
      const targetPos = new THREE.Vector3(...targetNode.position);
      
      // Calculate progress of the flow cycle (0 to 1)
      const progress = ((time * p.speed + p.delay) % 2) / 2; // scale cycle to 2 seconds
      
      // Arc / curved path height
      const arcHeight = Math.sin(progress * Math.PI) * 0.6;
      
      // Interpolated position + arc height + particle-specific offset
      const currentPos = new THREE.Vector3().lerpVectors(
        new THREE.Vector3(0, 0, 0),
        targetPos,
        progress
      );
      currentPos.y += arcHeight; // Add upward arc bending
      currentPos.add(p.offset); // Add noise
      
      mesh.position.copy(currentPos);
      
      // Fade out at ends of the flow cycle
      const mat = mesh.material as THREE.MeshBasicMaterial;
      if (mat) {
        mat.opacity = Math.sin(progress * Math.PI) * 0.8;
      }
    });
  });

  if (!active) return null;

  return (
    <group ref={groupRef}>
      {/* Central power distribution node */}
      <mesh position={[0, 0, 0]}>
        <sphereGeometry args={[0.3, 16, 16]} />
        <meshBasicMaterial color="#4edea3" transparent opacity={0.3} wireframe />
      </mesh>

      {/* Target second-life sites */}
      {nodes.map((node, i) => (
        <group key={node.name} position={node.position}>
          {/* Glowing wireframe target sphere */}
          <mesh>
            <sphereGeometry args={[0.35, 12, 12]} />
            <meshBasicMaterial
              color={node.color}
              wireframe
              transparent
              opacity={0.5}
            />
          </mesh>
          
          {/* External radar orbit ring */}
          <mesh rotation={[Math.PI / 2, 0, 0]}>
            <torusGeometry args={[0.5, 0.01, 4, 24]} />
            <meshBasicMaterial
              color={node.color}
              transparent
              opacity={0.3}
            />
          </mesh>
        </group>
      ))}

      {/* Dynamic energy flow particles */}
      {particles.map((p, idx) => (
        <mesh
          key={idx}
          ref={(el) => {
            if (el) particleRefs.current[idx] = el;
          }}
        >
          <boxGeometry args={[0.08, 0.08, 0.08]} />
          <meshBasicMaterial
            color={nodes[p.nodeIndex].color}
            transparent
            opacity={0}
            blending={THREE.AdditiveBlending}
          />
        </mesh>
      ))}
    </group>
  );
};

export default ImpactScene;
