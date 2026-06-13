import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface IntroSceneProps {
  active: boolean;
}

export const IntroScene: React.FC<IntroSceneProps> = ({ active }) => {
  const groupRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (!active || !groupRef.current) return;
    const time = state.clock.getElapsedTime();
    groupRef.current.rotation.y = time * 0.15;
    groupRef.current.rotation.x = Math.sin(time * 0.1) * 0.1;
  });

  if (!active) return null;

  return (
    <group ref={groupRef}>
      {/* Scattered red glowing warning components */}
      {Array.from({ length: 15 }).map((_, i) => {
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(Math.random() * 2 - 1);
        const r = 2.0 + Math.random() * 1.5;
        const x = r * Math.sin(phi) * Math.cos(theta);
        const y = r * Math.sin(phi) * Math.sin(theta);
        const z = r * Math.cos(phi);
        const size = 0.15 + Math.random() * 0.25;

        return (
          <mesh key={i} position={[x, y, z]}>
            <boxGeometry args={[size, size, size]} />
            <meshStandardMaterial
              color="#ff5451"
              wireframe
              emissive="#ff5451"
              emissiveIntensity={0.6}
            />
          </mesh>
        );
      })}
      
      {/* Heavy warning core */}
      <mesh>
        <sphereGeometry args={[1.2, 16, 16]} />
        <meshBasicMaterial
          color="#ff5451"
          wireframe
          transparent
          opacity={0.15}
        />
      </mesh>
    </group>
  );
};

export default IntroScene;
