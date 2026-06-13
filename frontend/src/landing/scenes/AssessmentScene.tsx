import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface AssessmentSceneProps {
  active: boolean;
}

export const AssessmentScene: React.FC<AssessmentSceneProps> = ({ active }) => {
  const laserRef = useRef<THREE.Mesh>(null);
  const glowRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (!active) return;
    const time = state.clock.getElapsedTime();
    
    // Sweep laser plane up and down between -1.5 and 1.5
    const yPos = Math.sin(time * 2.2) * 1.3;
    
    if (laserRef.current) {
      laserRef.current.position.y = yPos;
    }
    if (glowRef.current) {
      glowRef.current.position.y = yPos;
      glowRef.current.scale.x = 1.0 + Math.sin(time * 10) * 0.05; // heartbeat pulse
    }
  });

  if (!active) return null;

  return (
    <group>
      {/* Laser horizontal bar */}
      <mesh ref={laserRef} position={[0, 0, 0]}>
        <boxGeometry args={[3.2, 0.02, 1.8]} />
        <meshBasicMaterial
          color="#06b6d4"
          transparent
          opacity={0.8}
          blending={THREE.AdditiveBlending}
        />
      </mesh>

      {/* Laser glow halo */}
      <mesh ref={glowRef} position={[0, 0, 0]}>
        <boxGeometry args={[3.4, 0.12, 1.9]} />
        <meshBasicMaterial
          color="#06b6d4"
          transparent
          opacity={0.25}
          blending={THREE.AdditiveBlending}
        />
      </mesh>

      {/* Secondary diagnostic scan rings */}
      <mesh rotation={[Math.PI / 2, 0, 0]} position={[0, -0.8, 0]}>
        <torusGeometry args={[1.5, 0.01, 4, 32]} />
        <meshBasicMaterial color="#06b6d4" transparent opacity={0.3} />
      </mesh>
      <mesh rotation={[Math.PI / 2, 0, 0]} position={[0, 0.8, 0]}>
        <torusGeometry args={[1.5, 0.01, 4, 32]} />
        <meshBasicMaterial color="#06b6d4" transparent opacity={0.3} />
      </mesh>
    </group>
  );
};

export default AssessmentScene;
