import {Suspense, useEffect, useLayoutEffect, useMemo, useRef} from 'react';
import {useGLTF} from '@react-three/drei';
import {Canvas, useFrame, useThree} from '@react-three/fiber';
import {MathUtils, Mesh, PerspectiveCamera, Vector3} from 'three';
import type {Group} from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {FloorShadows, LabRoom} from './LabRoom';
import type {Position} from './LabRoom';

type EquipmentId = 'quantum' | 'optics' | 'control' | 'optimization' | 'research';
type View = 'overview' | EquipmentId;

type LabSceneProps = {
  selected: string | null;
  onSelect: (id: string) => void;
  lowGraphics: boolean;
  view: View;
  viewRequest: number;
  onReady?: () => void;
  onError?: (message: string) => void;
};

type Fixture = {id: EquipmentId; model: number; at: Position; angle?: number; width: number; depth: number};

const fixtures: Fixture[] = [
  {id: 'quantum', model: 0, at: [0, 0, -0.89], angle: 0.16, width: 1.65, depth: 1.65},
  {id: 'optics', model: 1, at: [-3.64, 0, -2.06], angle: 0.08, width: 3.12, depth: 1.28},
  {id: 'control', model: 2, at: [3.3, 0, -3.96], angle: -0.08, width: 0.82, depth: 0.81},
  {id: 'control', model: 2, at: [4.34, 0, -3.98], angle: -0.08, width: 0.82, depth: 0.81},
  {id: 'control', model: 3, at: [1.66, 0, -3.57], angle: 0.05, width: 1.48, depth: 0.87},
  {id: 'optimization', model: 3, at: [3.89, 0, -0.49], angle: -0.45, width: 1.48, depth: 0.87},
  {id: 'research', model: 3, at: [3.71, 0, 2.27], angle: -0.64, width: 1.48, depth: 0.87},
];

const modelUrls = ['dilution-refrigerator', 'optical-bench', 'electronics-rack', 'workstation']
  .map(name => `${import.meta.env.BASE_URL}lab/models/${name}.glb`);

export function clearLabModels() { useGLTF.clear(modelUrls); }

const cameras: Record<View, {position: Position; target: Position}> = {
  overview: {position: [3.5, 3.15, 8.35], target: [-0.29, 1.42, -0.7]},
  quantum: {position: [1.99, 1.98, 3.34], target: [0, 1.38, -0.92]},
  optics: {position: [-1.35, 2.17, 1.88], target: [-3.54, 0.97, -2.02]},
  control: {position: [2.55, 2.25, 0.43], target: [3.09, 1.12, -3.77]},
  optimization: {position: [1.18, 2.09, 2.96], target: [3.82, 0.87, -0.47]},
  research: {position: [0.89, 1.96, 5.51], target: [3.65, 0.87, 2.25]},
};
const canvasCamera = {position: cameras.overview.position, fov: 44, near: 0.06, far: 35};
const renderer = {antialias: true, alpha: false, powerPreference: 'low-power'} as const;
const walkDirections: Record<string, [number, number]> = {
  w: [1, 0], arrowup: [1, 0],
  s: [-1, 0], arrowdown: [-1, 0],
  a: [0, -1], arrowleft: [0, -1],
  d: [0, 1], arrowright: [0, 1],
};

function Equipment({fixture, source, onSelect}: {fixture: Fixture; source: Group; onSelect: LabSceneProps['onSelect']}) {
  const {gl} = useThree();
  const model = useMemo(() => {
    const instance = source.clone(true);
    instance.traverse(object => {
      if (object instanceof Mesh) {
        object.castShadow = true;
        object.receiveShadow = true;
      }
    });
    return instance;
  }, [source]);

  return <group name={fixture.id} position={fixture.at} rotation={[0, fixture.angle ?? 0, 0]}
    onClick={event => {
      if (event.button !== 0 || event.delta > 4) return;
      event.stopPropagation();
      onSelect(fixture.id);
    }}
    onPointerOver={event => {
      event.stopPropagation();
      gl.domElement.style.cursor = 'pointer';
    }}
    onPointerOut={() => { gl.domElement.style.cursor = ''; }}>
    <primitive object={model}/>
  </group>;
}

function EquipmentLayout({selected, onSelect, onReady}: Pick<LabSceneProps, 'selected' | 'onSelect' | 'onReady'>) {
  const models = useGLTF(modelUrls, false, false);
  const {gl, invalidate} = useThree();
  const ready = useRef(onReady);
  useLayoutEffect(() => { ready.current = onReady; }, [onReady]);
  useEffect(() => {
    invalidate();
    const frame = window.requestAnimationFrame(() => {
      if (!gl.getContext().isContextLost()) ready.current?.();
    });
    return () => window.cancelAnimationFrame(frame);
  }, [gl, invalidate]);

  return <>
    <FloorShadows footprints={fixtures.map(fixture => ({...fixture, selected: fixture.id === selected}))}/>
    {fixtures.map(fixture =>
      <Equipment key={`${fixture.id}:${fixture.at[0]}`} fixture={fixture}
        source={models[fixture.model].scene} onSelect={onSelect}/>
    )}
  </>;
}

type Flight = {
  elapsed: number;
  fromPosition: Vector3;
  fromTarget: Vector3;
  toPosition: Vector3;
  toTarget: Vector3;
};

function LabCamera({view, viewRequest, lowGraphics, onError}: Pick<LabSceneProps, 'view' | 'viewRequest' | 'lowGraphics' | 'onError'>) {
  const {camera, gl, invalidate, size} = useThree();
  const orbit = useMemo(() => {
    const controls = new OrbitControls(camera);
    controls.target.set(...cameras.overview.target);
    controls.minDistance = 1.9;
    controls.maxDistance = 12.5;
    controls.minPolarAngle = 0.81;
    controls.maxPolarAngle = Math.PI / 2 - 0.035;
    controls.minAzimuthAngle = -0.87;
    controls.maxAzimuthAngle = 0.9;
    controls.panSpeed = 0.64;
    controls.rotateSpeed = 0.65;
    controls.zoomSpeed = 0.8;
    controls.screenSpacePanning = false;
    controls.dampingFactor = 0.16;
    controls.update();
    return controls;
  }, [camera]);
  const flight = useRef<Flight | null>(null);
  const mounted = useRef(false);
  const aspect = size.width / Math.max(size.height, 1);
  const narrow = aspect < 1.32;

  useLayoutEffect(() => {
    if (camera instanceof PerspectiveCamera) {
      camera.fov = MathUtils.clamp(44 + (1.48 - aspect) * 19, 44, 60);
      camera.updateProjectionMatrix();
      invalidate();
    }
  }, [aspect, camera, invalidate]);

  useLayoutEffect(() => {
    orbit.enableDamping = !lowGraphics;
  }, [lowGraphics, orbit]);

  useLayoutEffect(() => {
    const canvas = gl.domElement;
    const boundedTarget = new Vector3();
    const cameraStep = new Vector3();
    const forward = new Vector3();
    const right = new Vector3();
    const vertical = new Vector3(0, 1, 0);
    const interrupt = () => { flight.current = null; };
    const change = () => {
      boundedTarget.set(
        MathUtils.clamp(orbit.target.x, -4.56, 4.63),
        MathUtils.clamp(orbit.target.y, 0.52, 2.32),
        MathUtils.clamp(orbit.target.z, -4.47, 3.82),
      );
      camera.position.add(cameraStep.subVectors(boundedTarget, orbit.target));
      orbit.target.copy(boundedTarget);
      canvas.dataset.cameraPosition = camera.position.toArray().map(value => value.toFixed(3)).join(',');
      invalidate();
    };
    const walk = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        canvas.blur();
        return;
      }
      if (event.altKey || event.ctrlKey || event.metaKey) return;
      const direction = walkDirections[event.key.toLowerCase()];
      if (!direction) return;
      event.preventDefault();
      interrupt();
      camera.getWorldDirection(forward);
      forward.y = 0;
      forward.normalize();
      right.crossVectors(forward, vertical);
      cameraStep.copy(forward).multiplyScalar(direction[0] * 0.24).addScaledVector(right, direction[1] * 0.24);
      // The initial overview is just outside the front opening. A walk can
      // approach the room from there while keeping movement inside its bounds.
      const {x, z} = camera.position;
      cameraStep.x = MathUtils.clamp(cameraStep.x, Math.min(-5.3 - x, 0), Math.max(5.3 - x, 0));
      cameraStep.z = MathUtils.clamp(cameraStep.z, Math.min(-4.64 - z, 0), Math.max(5.08 - z, 0));
      camera.position.add(cameraStep);
      orbit.target.add(cameraStep);
      orbit.update();
      invalidate();
    };
    const focus = () => canvas.focus({preventScroll: true});
    orbit.connect(canvas);
    orbit.addEventListener('change', change);
    orbit.addEventListener('start', interrupt);
    canvas.tabIndex = 0;
    canvas.setAttribute('aria-label', 'Interactive 3D laboratory. Use arrow keys or W A S D to move, and Escape to release focus.');
    canvas.addEventListener('pointerdown', focus);
    canvas.addEventListener('keydown', walk);
    change();
    return () => {
      orbit.removeEventListener('change', change);
      orbit.removeEventListener('start', interrupt);
      orbit.dispose();
      canvas.removeEventListener('pointerdown', focus);
      canvas.removeEventListener('keydown', walk);
    };
  }, [camera, gl, invalidate, orbit]);

  useEffect(() => {
    const canvas = gl.domElement;
    const lost = (event: Event) => {
      event.preventDefault();
      onError?.('The WebGL connection was lost. The equipment list and modules are still available.');
    };
    canvas.addEventListener('webglcontextlost', lost);
    return () => canvas.removeEventListener('webglcontextlost', lost);
  }, [gl, onError]);

  useLayoutEffect(() => {
    const preset = cameras[view];
    const position = view === 'overview' && narrow ? [2.78, 3.13, 9.05] as Position : preset.position;
    const target = new Vector3(...preset.target);
    const destination = new Vector3(...position);
    if (!mounted.current || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      camera.position.copy(destination);
      orbit.target.copy(target);
      orbit.update();
      mounted.current = true;
    } else {
      flight.current = {
        elapsed: 0,
        fromPosition: camera.position.clone(),
        fromTarget: orbit.target.clone(),
        toPosition: destination,
        toTarget: target,
      };
    }
    invalidate();
  }, [camera, invalidate, narrow, orbit, view, viewRequest]);

  useFrame((_, delta) => {
    const next = flight.current;
    if (next) {
      next.elapsed = Math.min(next.elapsed + Math.min(delta, 0.05), 0.56);
      const t = next.elapsed / 0.56;
      const eased = t * t * (3 - 2 * t);
      camera.position.lerpVectors(next.fromPosition, next.toPosition, eased);
      orbit.target.lerpVectors(next.fromTarget, next.toTarget, eased);
      if (t < 1) invalidate();
      else flight.current = null;
    }
    orbit.update(delta);
  }, -1);

  return null;
}

export default function LabScene({selected, onSelect, lowGraphics, view, viewRequest, onReady, onError}: LabSceneProps) {
  return <Canvas frameloop="demand" camera={canvasCamera}
    gl={renderer} dpr={lowGraphics ? 1 : [1, 1.5]} shadows={lowGraphics ? false : 'percentage'}>
    <LabCamera view={view} viewRequest={viewRequest} lowGraphics={lowGraphics} onError={onError}/>
    <LabRoom lowGraphics={lowGraphics}/>
    <Suspense fallback={null}>
      <EquipmentLayout selected={selected} onSelect={onSelect} onReady={onReady}/>
    </Suspense>
  </Canvas>;
}
