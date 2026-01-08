import React, { useRef, useMemo, Suspense } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface ParticleFieldProps {
  count?: number;
}

const ParticleField: React.FC<ParticleFieldProps> = ({ count = 100 }) => {
  const mesh = useRef<THREE.Points>(null);

  const particles = useMemo(() => {
    const positions = new Float32Array(count * 3);

    for (let i = 0; i < count; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 20;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 20;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 10;
    }

    return { positions };
  }, [count]);

  useFrame((state) => {
    if (!mesh.current) return;
    mesh.current.rotation.y = state.clock.getElapsedTime() * 0.02;
    mesh.current.rotation.x = Math.sin(state.clock.getElapsedTime() * 0.01) * 0.1;
  });

  return (
    <points ref={mesh}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={particles.positions.length / 3}
          array={particles.positions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.05}
        color="#4F68D8"
        transparent
        opacity={0.6}
        sizeAttenuation
      />
    </points>
  );
};

interface FloatingSpheresProps {
  trustScore: number;
}

const FloatingSpheres: React.FC<FloatingSpheresProps> = ({ trustScore }) => {
  const sphereRef = useRef<THREE.Mesh>(null);

  const speed = trustScore < 0.4 ? 0 : 1;
  const isDistorted = trustScore >= 0.4 && trustScore < 0.6;
  const distortion = isDistorted ? Math.sin(Date.now() / 100) * 0.2 : 0;

  useFrame((state) => {
    if (!sphereRef.current) return;
    const time = state.clock.getElapsedTime();
    sphereRef.current.position.y = Math.sin(time * 0.5 * speed) * 0.5 + distortion;
    sphereRef.current.rotation.x = time * 0.1 * speed;
    sphereRef.current.rotation.y = time * 0.15 * speed;

    // Color shift based on trust (Blue -> Red-ish/Purple)
    // Simple implementation: opacity drop or color change
    if (sphereRef.current.material instanceof THREE.MeshStandardMaterial) {
      // sphereRef.current.material.color.setHSL(...) // optional
    }
  });

  return (
    <>
      <mesh ref={sphereRef} position={[3, 0, -2]} scale={0.8}>
        <icosahedronGeometry args={[1, 1]} />
        <meshStandardMaterial
          color={trustScore < 0.6 ? "#E86B6B" : "#4F68D8"}
          transparent
          opacity={0.15 * (trustScore + 0.2)}
          roughness={0.8}
          metalness={0.2}
          wireframe
        />
      </mesh>
      <mesh position={[-3, -1, -3]} scale={0.5}>
        <octahedronGeometry args={[1, 0]} />
        <meshStandardMaterial
          color={trustScore < 0.6 ? "#E86B6B" : "#6B7FE8"}
          transparent
          opacity={0.1 * trustScore}
          roughness={0.9}
          wireframe
        />
      </mesh>
      <mesh position={[0, 2, -4]} scale={0.6}>
        <torusGeometry args={[1, 0.3, 16, 32]} />
        <meshStandardMaterial
          color={trustScore < 0.6 ? "#E86B6B" : "#4F68D8"}
          transparent
          opacity={0.08 * trustScore}
          roughness={0.8}
          wireframe
        />
      </mesh>
    </>
  );
};

interface SceneProps {
  trustScore: number;
}

const Scene: React.FC<SceneProps> = ({ trustScore }) => {
  return (
    <>
      <ambientLight intensity={0.8} />
      <directionalLight position={[5, 5, 5]} intensity={0.5} />
      <pointLight position={[-5, -5, 5]} intensity={0.3} color="#4F68D8" />
      <ParticleField count={150} />
      <FloatingSpheres trustScore={trustScore} />
    </>
  );
};

interface ThreeHeroBackgroundProps {
  trustScore?: number; // 0 to 1
}

export const ThreeHeroBackground: React.FC<ThreeHeroBackgroundProps> = ({ trustScore = 1.0 }) => {
  return (
    <div className="absolute inset-0 -z-10 opacity-70">
      <Suspense fallback={<div className="absolute inset-0 bg-gradient-to-br from-background to-secondary/20" />}>
        <Canvas
          camera={{ position: [0, 0, 8], fov: 60 }}
          dpr={[1, 1.5]}
          gl={{ antialias: true, alpha: true }}
          style={{ background: 'transparent' }}
        >

          <Scene trustScore={trustScore} />
        </Canvas>
      </Suspense>
    </div>
  );
};

export default ThreeHeroBackground;
