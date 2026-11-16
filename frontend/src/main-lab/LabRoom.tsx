import {useEffect, useMemo} from 'react';
import {useThree} from '@react-three/fiber';
import {CanvasTexture, PMREMGenerator, RepeatWrapping, SRGBColorSpace} from 'three';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';

export type Position = [number, number, number];

const paint = '#e9e6e0';
const frame = '#8d929c';
const graphite = '#303946';
const floorHeight = -0.017;

function makeTexture(width: number, height: number, draw: (context: CanvasRenderingContext2D) => void) {
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext('2d');
  if (context) draw(context);
  const texture = new CanvasTexture(canvas);
  texture.colorSpace = SRGBColorSpace;
  return texture;
}

function Panel({at, size, color, metal = 0, glow = false}: {
  at: Position; size: Position; color: string; metal?: number; glow?: boolean;
}) {
  return <mesh position={at} receiveShadow>
    <boxGeometry args={size}/>
    <meshStandardMaterial color={color} metalness={metal} roughness={metal ? 0.43 : 0.73}
      emissive={glow ? color : '#000000'} emissiveIntensity={glow ? 1.05 : 0}/>
  </mesh>;
}

function Floor() {
  const surface = useMemo(() => {
    const texture = makeTexture(256, 256, context => {
      context.fillStyle = '#b6bbc3';
      context.fillRect(0, 0, 256, 256);
      const pixels = context.getImageData(0, 0, 256, 256);
      for (let index = 0; index < pixels.data.length; index += 4) {
        const variation = ((index * 13) ^ (index >>> 7) ^ (index >>> 3)) % 11 - 5;
        pixels.data[index] += variation;
        pixels.data[index + 1] += variation;
        pixels.data[index + 2] += variation;
      }
      context.putImageData(pixels, 0, 0);
      context.fillStyle = 'rgba(65, 75, 92, 0.16)';
      context.fillRect(0, 0, 256, 1);
      context.fillRect(0, 0, 1, 256);
      context.fillStyle = 'rgba(251, 247, 243, 0.22)';
      context.fillRect(0, 1, 256, 1);
      context.fillRect(1, 0, 1, 256);
    });
    texture.wrapS = texture.wrapT = RepeatWrapping;
    texture.repeat.set(10, 9);
    texture.anisotropy = 4;
    return texture;
  }, []);
  useEffect(() => () => surface.dispose(), [surface]);

  return <>
    <Panel at={[0, -0.15, 0]} size={[11.9, 0.26, 10.7]} color="#8a909c"/>
    <mesh position={[0, floorHeight, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
      <planeGeometry args={[11.9, 10.7]}/>
      <meshStandardMaterial map={surface} color="#dfe0e2" metalness={0.22} roughness={0.48}/>
    </mesh>
    <Panel at={[-5.66, -0.012, 0]} size={[0.033, 0.007, 10.32]} color="#6d7d99" metal={0.25}/>
    <Panel at={[5.66, -0.012, 0]} size={[0.033, 0.007, 10.32]} color="#6d7d99" metal={0.25}/>
    <Panel at={[0, -0.012, -4.98]} size={[11.32, 0.007, 0.033]} color="#6d7d99" metal={0.25}/>
    <Panel at={[0, -0.012, 4.95]} size={[11.32, 0.007, 0.033]} color="#6d7d99" metal={0.25}/>
  </>;
}

export type Footprint = {at: Position; width: number; depth: number; angle?: number; selected?: boolean};

export function FloorShadows({footprints}: {footprints: Footprint[]}) {
  const softShadow = useMemo(() => makeTexture(96, 96, context => {
    const gradient = context.createRadialGradient(48, 48, 8, 48, 48, 48);
    gradient.addColorStop(0, 'rgba(22, 28, 38, 0.55)');
    gradient.addColorStop(0.55, 'rgba(30, 38, 52, 0.36)');
    gradient.addColorStop(1, 'rgba(36, 47, 62, 0)');
    context.fillStyle = gradient;
    context.fillRect(0, 0, 96, 96);
  }), []);
  useEffect(() => () => softShadow.dispose(), [softShadow]);

  return <>{footprints.map(({at, width, depth, angle = 0, selected}) =>
    <group key={`${at[0]}:${at[2]}`} position={[at[0], -0.01, at[2]]} rotation={[0, angle, 0]}>
      <mesh rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[width * 1.32, depth * 1.55]}/>
        <meshBasicMaterial map={softShadow} transparent opacity={0.76} depthWrite={false} toneMapped={false}/>
      </mesh>
      {selected && <group position={[0, 0.004, 0]}>
        {[-1, 1].map(side =>
          <group key={side} position={[side * width * 0.53, 0, depth * 0.54]}>
            <Panel at={[side * -0.115, 0, 0]} size={[0.23, 0.006, 0.027]} color="#746bf2" glow/>
            <Panel at={[0, 0, -0.103]} size={[0.027, 0.006, 0.18]} color="#746bf2" glow/>
          </group>
        )}
      </group>}
    </group>
  )}</>;
}

function WallSign({at, title, subtitle, width, mark = false}: {
  at: Position; title: string; subtitle: string; width: number; mark?: boolean;
}) {
  const sign = useMemo(() => makeTexture(1024, 256, context => {
    context.clearRect(0, 0, 1024, 256);
    context.fillStyle = '#596987';
    const offset = mark ? 135 : 28;
    if (mark) {
      context.lineWidth = 9;
      context.strokeStyle = '#6267a4';
      context.beginPath();
      context.moveTo(33, 100);
      context.lineTo(76, 76);
      context.lineTo(109, 98);
      context.lineTo(108, 141);
      context.lineTo(67, 165);
      context.lineTo(33, 145);
      context.closePath();
      context.stroke();
      context.beginPath();
      context.moveTo(33, 100);
      context.lineTo(67, 121);
      context.lineTo(109, 98);
      context.moveTo(67, 121);
      context.lineTo(67, 165);
      context.stroke();
    }
    context.font = '600 27px system-ui, sans-serif';
    context.fillText(subtitle, offset, 103, 1024 - offset - 12);
    context.fillStyle = '#2e394a';
    context.font = '600 60px system-ui, sans-serif';
    context.fillText(title, offset, 168, 1024 - offset - 12);
  }), [mark, subtitle, title]);
  useEffect(() => () => sign.dispose(), [sign]);

  return <mesh position={at}>
    <planeGeometry args={[width, width / 4]}/>
    <meshBasicMaterial map={sign} transparent depthWrite={false} toneMapped={false}/>
  </mesh>;
}

function Windows() {
  return <>
    <Panel at={[-6.62, 1.95, -1.28]} size={[0.13, 3.91, 7.79]} color="#b9c5cf"/>
    <Panel at={[-6.27, 1.46, -5.1]} size={[0.78, 2.95, 0.13]} color="#d7dbe0"/>
    <Panel at={[-6.22, 3.39, -1.3]} size={[0.12, 0.07, 7.48]} color="#edf5ff" glow/>
    <Panel at={[-5.89, 0.34, -0.87]} size={[0.13, 0.68, 8.95]} color={paint}/>
    <Panel at={[-5.87, 0.68, -0.87]} size={[0.19, 0.056, 8.95]} color={frame} metal={0.34}/>
    <Panel at={[-5.88, 3.38, -0.87]} size={[0.22, 0.11, 8.95]} color={frame} metal={0.28}/>
    <Panel at={[-5.87, 3.71, -0.87]} size={[0.17, 0.55, 8.95]} color={paint}/>
    {[-5.31, -3.08, -0.85, 1.38, 3.6].map((z, index) => <group key={z}>
      <Panel at={[-5.87, 2.025, z]} size={[0.145, 2.66, 0.061]} color={frame} metal={0.25}/>
      {index < 4 && <mesh position={[-5.875, 2.025, z + 1.115]} rotation={[0, Math.PI / 2, 0]}>
        <planeGeometry args={[2.19, 2.62]}/>
        <meshStandardMaterial color="#a5bad6" transparent opacity={0.25} roughness={0.23}
          metalness={0.24} depthWrite={false}/>
      </mesh>}
    </group>)}
    <Panel at={[-5.84, 1.49, -0.87]} size={[0.032, 0.018, 8.85]} color="#d4dce8"/>
  </>;
}

function BackWall() {
  return <>
    <Panel at={[0, 1.98, -5.38]} size={[11.87, 3.96, 0.14]} color={paint}/>
    <Panel at={[0, 0.27, -5.287]} size={[11.8, 0.54, 0.064]} color="#b2b9c1"/>
    <Panel at={[0, 0.095, -5.246]} size={[11.8, 0.13, 0.052]} color={graphite}/>
    <Panel at={[0, 3.84, -5.29]} size={[11.82, 0.24, 0.17]} color="#bcc3ce"/>
    <Panel at={[0, 3.705, -5.183]} size={[11.58, 0.025, 0.026]} color="#efefff" glow/>
    <Panel at={[-0.71, 1.92, -5.281]} size={[4.56, 2.49, 0.06]} color="#d7d9dd"/>
    <Panel at={[-0.71, 3.15, -5.232]} size={[4.55, 0.045, 0.037]} color="#a7aebb" metal={0.32}/>
    <Panel at={[-0.71, 0.69, -5.232]} size={[4.55, 0.038, 0.037]} color="#a7aebb" metal={0.32}/>
    {[-2.96, -1.82, -0.68, 0.46, 1.57].map(x =>
      <Panel key={x} at={[x, 1.92, -5.244]} size={[0.018, 2.45, 0.018]} color="#afb5bf" metal={0.2}/>
    )}
    <WallSign at={[-0.77, 3.355, -5.292]} title="Quantum Forge" subtitle="MAIN QUANTUM LABORATORY" width={4.15} mark/>
    <WallSign at={[-4.18, 2.81, -5.286]} title="Optical systems" subtitle="PHOTONICS" width={2.66}/>
    <WallSign at={[3.79, 2.84, -5.286]} title="Control systems" subtitle="INSTRUMENTATION" width={2.85}/>
    <Panel at={[-4.43, 1.27, -5.25]} size={[1.84, 0.083, 0.13]} color="#777f8d" metal={0.23}/>
    <Panel at={[3.72, 1.2, -5.25]} size={[3.85, 0.083, 0.13]} color="#777f8d" metal={0.23}/>
    {[-5.07, -3.84, 2.32, 3.57, 4.82].map(x => <group key={x}>
      <Panel at={[x, 1.267, -5.171]} size={[0.102, 0.061, 0.023]} color="#eaedf4"/>
      <Panel at={[x, 1.267, -5.157]} size={[0.027, 0.021, 0.006]} color="#626d80"/>
    </group>)}
  </>;
}

function RightWall() {
  return <>
    <Panel at={[5.887, 1.98, -2.78]} size={[0.15, 3.96, 5.15]} color={paint}/>
    <Panel at={[5.794, 0.12, -2.78]} size={[0.06, 0.22, 5.13]} color={graphite}/>
    <Panel at={[5.787, 2.23, -3.23]} size={[0.064, 1.87, 2.66]} color="#c1c7d3"/>
    <Panel at={[5.748, 2.23, -3.23]} size={[0.026, 1.75, 2.52]} color="#5a6a87" metal={0.42}/>
    <Panel at={[5.728, 2.23, -3.23]} size={[0.011, 1.69, 2.46]} color="#657a9c" metal={0.35}/>
    {[-4.46, -3.64, -2.82, -2].map(z =>
      <Panel key={z} at={[5.718, 2.23, z]} size={[0.034, 1.76, 0.024]} color="#b4bed2" metal={0.34}/>
    )}
    <Panel at={[5.78, 3.45, -2.81]} size={[0.038, 0.046, 4.71]} color="#dcdeff" glow/>
    <Panel at={[5.85, 1.98, -0.22]} size={[0.21, 3.96, 0.15]} color="#8b96a9" metal={0.28}/>
  </>;
}

function CeilingFixtures() {
  return <>
    <Panel at={[0, 3.985, -4.36]} size={[11.94, 0.15, 1.96]} color="#d3d6dd"/>
    <Panel at={[-5.42, 3.985, -0.25]} size={[1.12, 0.15, 8.9]} color="#d3d6dd"/>
    <Panel at={[5.52, 3.985, -2.53]} size={[0.87, 0.15, 5.58]} color="#d3d6dd"/>
    {[-3.08, -0.08, 2.94].map(x => <group key={x}>
      <Panel at={[x, 3.78, -2.19]} size={[0.1, 0.13, 2.68]} color="#a1a9b8" metal={0.31}/>
      <Panel at={[x, 3.707, -2.19]} size={[0.158, 0.044, 2.65]} color="#ecedf3"/>
      <Panel at={[x, 3.682, -2.19]} size={[0.116, 0.009, 2.57]} color="#fcf6ed" glow/>
      {[-1.25, -3.23].map(z =>
        <Panel key={z} at={[x, 3.884, z]} size={[0.027, 0.14, 0.025]} color="#929bad" metal={0.31}/>
      )}
    </group>)}
    <Panel at={[-4.5, 3.73, 0.41]} size={[0.11, 0.07, 2.94]} color="#a1a9b8" metal={0.33}/>
    <Panel at={[-4.5, 3.68, 0.41]} size={[0.088, 0.021, 2.9]} color="#f0f5ff" glow/>
  </>;
}

export function LabRoom({lowGraphics}: {lowGraphics: boolean}) {
  const {gl, scene, invalidate} = useThree();
  useEffect(() => {
    const room = new RoomEnvironment();
    const generator = new PMREMGenerator(gl);
    const environment = generator.fromScene(room, 0.035, 0.1, 100, {size: 128});
    room.dispose();
    generator.dispose();
    scene.environment = environment.texture;
    scene.environmentIntensity = 0.69;
    invalidate();
    return () => {
      scene.environment = null;
      environment.dispose();
    };
  }, [gl, scene, invalidate]);

  return <>
    <color attach="background" args={['#c8ced7']}/>
    <hemisphereLight args={['#edf1fd', '#6c6d79', 0.52]}/>
    <directionalLight position={[0.2, 6.2, 4.4]} color="#fff3e3" intensity={1.87}
      castShadow={!lowGraphics} shadow-mapSize={[1024, 1024]} shadow-normalBias={0.024}
      shadow-camera-left={-6.5} shadow-camera-right={6.5} shadow-camera-top={6.5}
      shadow-camera-bottom={-6.5} shadow-camera-far={24}/>
    <directionalLight position={[-7, 4, -2.6]} color="#dbeaff" intensity={1.02}/>
    <pointLight position={[3.6, 3.04, -3.4]} color="#b8c4ff" intensity={8} distance={6}/>
    <Floor/>
    <BackWall/>
    <Windows/>
    <RightWall/>
    <CeilingFixtures/>
  </>;
}
