import React, { useEffect, useRef, useState } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import BatteryParticles from './BatteryParticles';
import IntroScene from './scenes/IntroScene';
import AadhaarScene from './scenes/AadhaarScene';
import AssessmentScene from './scenes/AssessmentScene';
import ImpactScene from './scenes/ImpactScene';

export const ScrollStory: React.FC = () => {
  const { camera } = useThree();
  
  // Track scroll position using a ref to avoid React re-renders in scroll handler
  const scrollProgressRef = useRef(0);
  const [activeScene, setActiveScene] = useState<number>(0);
  const [particleProgress, setParticleProgress] = useState<number>(0);

  useEffect(() => {
    let active = true;
    let frameId: number;

    const handleScroll = () => {
      if (!active) return;
      const update = () => {
        const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
        if (scrollHeight <= 0) return;
        const progress = Math.min(Math.max(window.scrollY / scrollHeight, 0), 1);
        scrollProgressRef.current = progress;
      };
      
      cancelAnimationFrame(frameId);
      frameId = requestAnimationFrame(update);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();

    return () => {
      active = false;
      cancelAnimationFrame(frameId);
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  // Targets for camera lerp
  const targetCamPos = useRef(new THREE.Vector3(0, 0, 8));
  const targetLookAt = useRef(new THREE.Vector3(0, 0, 0));
  const currentLookAt = useRef(new THREE.Vector3(0, 0, 0));

  useFrame(() => {
    const progress = scrollProgressRef.current;

    // 1. Determine active scene and target camera paths based on progress phases
    let phase = 0;
    let localPartProgress = 0;

    if (progress < 0.20) {
      // Phase 0: Intro / Battery Crisis
      phase = 0;
      localPartProgress = 0.0;
      targetCamPos.current.set(0, 0, 8);
      targetLookAt.current.set(0, 0, 0);
    } else if (progress >= 0.20 && progress < 0.45) {
      // Phase 1: Aadhaar Identity
      phase = 1;
      // Map 0.20 - 0.45 scroll progress to 0.0 - 0.5 particle convergence
      const t = (progress - 0.20) / 0.25;
      localPartProgress = t * 0.5;
      targetCamPos.current.set(0.5, -0.2, 7.5);
      targetLookAt.current.set(0, 0, 0);
    } else if (progress >= 0.45 && progress < 0.70) {
      // Phase 2: AI Intake Assessment
      phase = 2;
      // Map 0.45 - 0.70 scroll progress to 0.5 - 0.9 particle convergence
      const t = (progress - 0.45) / 0.25;
      localPartProgress = 0.5 + t * 0.4;
      targetCamPos.current.set(-1.4, 0.4, 6.0); // angle view for scanning laser
      targetLookAt.current.set(-0.2, 0, 0);
    } else {
      // Phase 3: Second-life Deployment & Impact
      phase = 3;
      // Map 0.70 - 1.00 scroll progress to 0.9 - 1.0 particle convergence
      const t = (progress - 0.70) / 0.30;
      localPartProgress = 0.9 + t * 0.1;
      targetCamPos.current.set(0, 0.5, 9.0); // pull back to show outgoing energy lines
      targetLookAt.current.set(0, 0, 0);
    }

    // Sync state for components
    if (activeScene !== phase) {
      setActiveScene(phase);
    }
    // Subtle damping/easing for particle convergence progress
    setParticleProgress((prev) => THREE.MathUtils.lerp(prev, localPartProgress, 0.08));

    // 2. Smoothly lerp camera position and orientation (dampening)
    camera.position.lerp(targetCamPos.current, 0.05);
    
    currentLookAt.current.lerp(targetLookAt.current, 0.05);
    camera.lookAt(currentLookAt.current);
  });

  return (
    <group>
      {/* Background/ambient glow lighting effects matching active scene */}
      <pointLight
        position={[0, 0, 2]}
        intensity={activeScene === 0 ? 1.5 : activeScene === 2 ? 2.5 : 0.5}
        color={
          activeScene === 0
            ? '#ff5451' // warning red
            : activeScene === 2
            ? '#06b6d4' // intake cyan
            : '#4d8eff' // blueprint blue
        }
      />

      {/* Main converging particle assembly */}
      <BatteryParticles progress={particleProgress} />

      {/* Overlaid scene specific visual cues */}
      <IntroScene active={activeScene === 0} />
      <AadhaarScene active={activeScene === 1} />
      <AssessmentScene active={activeScene === 2} />
      <ImpactScene active={activeScene === 3} />
    </group>
  );
};

export default ScrollStory;
