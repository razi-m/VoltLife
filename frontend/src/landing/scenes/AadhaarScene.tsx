import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface AadhaarSceneProps {
  active: boolean;
}

export const AadhaarScene: React.FC<AadhaarSceneProps> = ({ active }) => {
  const groupRef = useRef<THREE.Group>(null);
  const ring1Ref = useRef<THREE.Mesh>(null);
  const ring2Ref = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (!active) return;
    const time = state.clock.getElapsedTime();
    if (groupRef.current) {
      groupRef.current.rotation.y = time * 0.08;
    }
    if (ring1Ref.current) {
      ring1Ref.current.rotation.x = time * 0.3;
      ring1Ref.current.rotation.y = time * 0.15;
    }
    if (ring2Ref.current) {
      ring2Ref.current.rotation.y = -time * 0.25;
      ring2Ref.current.rotation.z = time * 0.1;
    }
  });

  if (!active) return null;

  return (
    <group ref={groupRef}>
      {/* Concentric holographic ring 1 */}
      <mesh ref={ring1Ref}>
        <torusGeometry args={[2.2, 0.02, 8, 48]} />
        <meshBasicMaterial color="#4d8eff" transparent opacity={0.6} />
      </mesh>

      {/* Concentric holographic ring 2 */}
      <mesh ref={ring2Ref}>
        <torusGeometry args={[2.5, 0.015, 8, 48]} />
        <meshBasicMaterial color="#4edea3" transparent opacity={0.4} />
      </mesh>

      {/* Hexagonal blueprint grid overlay */}
      <mesh position={[0, 0, 0]}>
        <sphereGeometry args={[2.0, 12, 12]} />
        <meshBasicMaterial
          color="#4d8eff"
          wireframe
          transparent
          opacity={0.12}
        />
      </mesh>
    </group>
  );
};

export default AadhaarScene;
