"use client";

import React, { useRef, useMemo, useEffect, useState } from "react";
import * as THREE from "three";
import { useFrame } from "@react-three/fiber";
import { useGLTF, useTexture } from "@react-three/drei";

interface GoldCoinProps {
  isHovered: boolean;
  pointer: { x: number; y: number };
  onIntroComplete?: () => void;
  reducedMotion?: boolean;
}

export function GoldCoin({
  isHovered,
  pointer,
  onIntroComplete,
  reducedMotion = false,
}: GoldCoinProps) {
  const groupRef = useRef<THREE.Group>(null);
  const meshRef = useRef<THREE.Mesh>(null);

  // Animation state tracking
  const [introFinished, setIntroFinished] = useState(reducedMotion);
  const introStartTime = useRef<number | null>(null);

  // Load optimized GLTF model
  const { scene } = useGLTF("/models/gold/Gold.glb");

  // Load PBR texture maps
  const [baseColorMap, metallicMap, roughnessMap, normalMap] = useTexture([
    "/models/gold/Gold_BaseColor.png",
    "/models/gold/Gold_Metallic.png",
    "/models/gold/Gold_Roughness.png",
    "/models/gold/Gold_Normal.png",
  ]);

  // Configure color space & texture parameters
  useEffect(() => {
    if (baseColorMap) {
      baseColorMap.colorSpace = THREE.SRGBColorSpace;
      baseColorMap.needsUpdate = true;
    }
    if (metallicMap) {
      metallicMap.colorSpace = THREE.NoColorSpace;
      metallicMap.needsUpdate = true;
    }
    if (roughnessMap) {
      roughnessMap.colorSpace = THREE.NoColorSpace;
      roughnessMap.needsUpdate = true;
    }
    if (normalMap) {
      normalMap.colorSpace = THREE.NoColorSpace;
      normalMap.needsUpdate = true;
    }
  }, [baseColorMap, metallicMap, roughnessMap, normalMap]);

  // Extract geometry from loaded model
  const coinGeometry = useMemo(() => {
    let geom: THREE.BufferGeometry | null = null;
    scene.traverse((child) => {
      if ((child as THREE.Mesh).isMesh && !geom) {
        geom = (child as THREE.Mesh).geometry.clone();
      }
    });
    return geom;
  }, [scene]);

  // Create authoritative physical PBR Gold material
  const coinMaterial = useMemo(() => {
    return new THREE.MeshStandardMaterial({
      map: baseColorMap,
      metalnessMap: metallicMap,
      roughnessMap: roughnessMap,
      normalMap: normalMap,
      normalScale: new THREE.Vector2(0.85, 0.85),
      metalness: 1.0,
      roughness: 0.32,
      color: new THREE.Color("#FFF8E7"),
      envMapIntensity: 1.2,
      side: THREE.DoubleSide,
    });
  }, [baseColorMap, metallicMap, roughnessMap, normalMap]);

  // Continuous rotation and interaction tracking
  const currentRotationY = useRef<number>(reducedMotion ? 0.45 : 0);
  const currentRotationX = useRef<number>(reducedMotion ? 0.12 : 0);
  const currentRotationZ = useRef<number>(0);
  const currentScale = useRef<number>(reducedMotion ? 1.0 : 0.01);
  const currentSpeed = useRef<number>(0.5);

  useFrame((state, delta) => {
    if (!groupRef.current) return;

    const clampedDelta = Math.min(delta, 0.05);
    const time = state.clock.getElapsedTime();

    // Reduced motion handling
    if (reducedMotion) {
      groupRef.current.rotation.y = 0.45;
      groupRef.current.rotation.x = 0.12;
      groupRef.current.rotation.z = 0;
      groupRef.current.scale.set(1.0, 1.0, 1.0);
      return;
    }

    // Stage A & B: Cinematic Intro Sequence (duration ~2.0 seconds)
    if (!introFinished) {
      if (introStartTime.current === null) {
        introStartTime.current = time;
      }
      const elapsedIntro = time - introStartTime.current;
      const introDuration = 2.0;

      if (elapsedIntro < introDuration) {
        const progress = elapsedIntro / introDuration;
        // Smooth cubic ease out
        const easeOut = 1 - Math.pow(1 - progress, 3);

        // Smooth scale entrance (0.1 -> 1.0)
        currentScale.current = THREE.MathUtils.lerp(0.1, 1.0, easeOut);

        // Cinematic spin: 1 full rotation (2 * PI) with deceleration
        const spinSpeed = (1 - progress * 0.75) * 6.0;
        currentRotationY.current += spinSpeed * clampedDelta;

        // Subtle initial tilt that rights itself
        currentRotationX.current = THREE.MathUtils.lerp(0.35, 0.08, easeOut);
        currentRotationZ.current = Math.sin(progress * Math.PI) * 0.15;
      } else {
        setIntroFinished(true);
        if (onIntroComplete) {
          onIntroComplete();
        }
      }
    } else {
      // Stage C & Idle / Hover phase: Seamless continuation without resetting rotation!
      const targetSpeed = isHovered ? 2.4 : 0.65;
      currentSpeed.current = THREE.MathUtils.lerp(
        currentSpeed.current,
        targetSpeed,
        clampedDelta * 3.5
      );

      // Continuous vertical axis rotation
      currentRotationY.current += currentSpeed.current * clampedDelta;

      // Pointer tilt interpolation (clamped to restrained angles)
      const targetTiltX = isHovered
        ? THREE.MathUtils.clamp(-pointer.y * 0.35, -0.3, 0.3)
        : Math.sin(time * 0.8) * 0.05;

      const targetTiltZ = isHovered
        ? THREE.MathUtils.clamp(pointer.x * 0.35, -0.3, 0.3)
        : Math.cos(time * 0.7) * 0.03;

      currentRotationX.current = THREE.MathUtils.lerp(
        currentRotationX.current,
        targetTiltX,
        clampedDelta * 4.0
      );
      currentRotationZ.current = THREE.MathUtils.lerp(
        currentRotationZ.current,
        targetTiltZ,
        clampedDelta * 4.0
      );

      // Restrained scale response on hover (1.0 -> 1.05)
      const targetScale = isHovered ? 1.05 : 1.0;
      currentScale.current = THREE.MathUtils.lerp(
        currentScale.current,
        targetScale,
        clampedDelta * 5.0
      );
    }

    // Apply values to group
    groupRef.current.rotation.y = currentRotationY.current;
    groupRef.current.rotation.x = currentRotationX.current;
    groupRef.current.rotation.z = currentRotationZ.current;
    groupRef.current.scale.set(
      currentScale.current,
      currentScale.current,
      currentScale.current
    );
  });

  if (!coinGeometry) return null;

  return (
    <group ref={groupRef} dispose={null}>
      <mesh
        ref={meshRef}
        geometry={coinGeometry}
        material={coinMaterial}
        castShadow
        receiveShadow
      />
    </group>
  );
}

// Preload the GLTF model for instantaneous rendering
useGLTF.preload("/models/gold/Gold.glb");
