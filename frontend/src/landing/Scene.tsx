import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';

interface SceneProps {
  children: React.ReactNode;
}

export const Scene: React.FC<SceneProps> = ({ children }) => {
  return (
    <div className="landing__canvas-container" style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', zIndex: 1, pointerEvents: 'none' }}>
      <Canvas
        camera={{ position: [0, 0, 8], fov: 45 }}
        gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
        dpr={[1, 1.5]} // limit dpr on high-end screens for performance
      >
        <ambientLight intensity={0.4} />
        <directionalLight position={[5, 5, 5]} intensity={1.2} castShadow />
        <pointLight position={[-5, -5, -2]} intensity={0.5} color="#4d8eff" />
        <Suspense fallback={null}>
          {children}
        </Suspense>
      </Canvas>
    </div>
  );
};

export default Scene;
