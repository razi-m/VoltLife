import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface BatteryParticlesProps {
  progress: number; // 0 (scattered) to 1 (converged)
  color?: string;
}

export const BatteryParticles: React.FC<BatteryParticlesProps> = ({ progress, color = '#adc6ff' }) => {
  const pointsRef = useRef<THREE.Points>(null);
  const particleCount = 2000;

  // Generate original states: scattered (random spherical) and structured (battery pack grid)
  const [scatteredPositions, gridPositions, colors] = useMemo(() => {
    const scattered = new Float32Array(particleCount * 3);
    const grid = new Float32Array(particleCount * 3);
    const colorArray = new Float32Array(particleCount * 3);
    const baseColor = new THREE.Color(color);

    // Grid sizing parameters (e.g. 10 x 5 x 4 grid for a battery pack look)
    const cols = 16;
    const rows = 10;
    const layers = 12;
    const totalGrid = cols * rows * layers; // 1920 particles mapped to grid

    for (let i = 0; i < particleCount; i++) {
      // 1. Scattered (Random Sphere)
      const u = Math.random();
      const v = Math.random();
      const theta = u * 2.0 * Math.PI;
      const phi = Math.acos(2.0 * v - 1.0);
      const r = 3.5 + Math.random() * 2.5; // scattered outer radius

      scattered[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      scattered[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      scattered[i * 3 + 2] = r * Math.cos(phi);

      // 2. Structured Grid (Battery Pack shape)
      if (i < totalGrid) {
        const xIdx = i % cols;
        const yIdx = Math.floor((i % (cols * rows)) / cols);
        const zIdx = Math.floor(i / (cols * rows));

        // Center the grid: scale and translate
        grid[i * 3] = (xIdx - cols / 2) * 0.18;
        grid[i * 3 + 1] = (yIdx - rows / 2) * 0.14;
        grid[i * 3 + 2] = (zIdx - layers / 2) * 0.12;
      } else {
        // Remainder particles form terminal leads or chassis outline
        const isLeftLead = i % 2 === 0;
        grid[i * 3] = isLeftLead ? -1.8 : 1.8;
        grid[i * 3 + 1] = 0.9 + Math.random() * 0.2;
        grid[i * 3 + 2] = (Math.random() - 0.5) * 0.6;
      }

      // 3. Colors: slight variation based on position
      const tempColor = baseColor.clone();
      if (Math.random() > 0.8) {
        // Add safety green highlights
        tempColor.set('#4edea3');
      } else if (Math.random() > 0.95) {
        // Add safety red highlights
        tempColor.set('#ff5451');
      }
      colorArray[i * 3] = tempColor.r;
      colorArray[i * 3 + 1] = tempColor.g;
      colorArray[i * 3 + 2] = tempColor.b;
    }

    return [scattered, grid, colorArray];
  }, [color]);

  // Set initial buffer positions
  const currentPositions = useMemo(() => new Float32Array(particleCount * 3), []);

  useFrame((state) => {
    if (!pointsRef.current) return;
    const time = state.clock.getElapsedTime();
    const geo = pointsRef.current.geometry;
    const posAttr = geo.getAttribute('position') as THREE.BufferAttribute;

    // Linear interpolation between scattered and grid positions based on progress
    for (let i = 0; i < particleCount; i++) {
      const idx = i * 3;
      
      // Add subtle noise/orbit waving depending on progress state
      const noiseX = Math.sin(time * 1.5 + i) * 0.08 * (1 - progress);
      const noiseY = Math.cos(time * 1.2 + i) * 0.08 * (1 - progress);
      const noiseZ = Math.sin(time * 0.8 + i) * 0.08 * (1 - progress);

      // Lerp
      currentPositions[idx] = THREE.MathUtils.lerp(scatteredPositions[idx] + noiseX, gridPositions[idx], progress);
      currentPositions[idx + 1] = THREE.MathUtils.lerp(scatteredPositions[idx + 1] + noiseY, gridPositions[idx + 1], progress);
      currentPositions[idx + 2] = THREE.MathUtils.lerp(scatteredPositions[idx + 2] + noiseZ, gridPositions[idx + 2], progress);
    }

    posAttr.copyArray(currentPositions);
    posAttr.needsUpdate = true;

    // Rotate the overall assembly slightly for depth
    pointsRef.current.rotation.y = time * 0.1 + progress * 0.4;
    pointsRef.current.rotation.x = Math.sin(time * 0.05) * 0.05 + progress * 0.2;
  });

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[currentPositions, 3]}
        />
        <bufferAttribute
          attach="attributes-color"
          args={[colors, 3]}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.06}
        vertexColors
        transparent
        opacity={0.8}
        sizeAttenuation={true}
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </points>
  );
};

export default BatteryParticles;
