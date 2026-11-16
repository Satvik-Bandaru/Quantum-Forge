export type LabPhoto = {
  id: string;
  title: string;
  src: string;
  kind: 'photograph' | 'illustration';
  credit: string;
  source: string;
  description: string;
  equipment: string[];
};

export const labPhotos: LabPhoto[] = [
  {
    id: 'ornl-dilution-refrigerator',
    title: 'Inside a dilution refrigerator',
    src: '/lab/photos/ornl-dilution-refrigerator.jpg',
    kind: 'photograph',
    credit: 'Oak Ridge National Laboratory · CC BY 2.0 · Resized',
    source: 'https://commons.wikimedia.org/wiki/File:Quantum_lab_(53804358991).jpg',
    description: 'Exposed cooling stages and wiring in a closed cycle dilution refrigerator used for microscopy at millikelvin temperatures.',
    equipment: ['quantum', 'research'],
  },
  {
    id: 'ornl-pulse-optics',
    title: 'Optics for spin measurements',
    src: '/lab/photos/ornl-pulse-optics.jpg',
    kind: 'photograph',
    credit: 'Oak Ridge National Laboratory · CC BY 2.0 · Resized',
    source: 'https://commons.wikimedia.org/wiki/File:Quantum_lab_(53804603313).jpg',
    description: 'An optical setup generates two-color pulse sequences to measure spin lifetime and coherence in a dilution refrigerator.',
    equipment: ['optics', 'control', 'research'],
  },
  {
    id: 'fmn-cryostat-assembly',
    title: 'Assembling a quantum cryostat',
    src: '/lab/photos/fmn-cryostat-assembly.jpg',
    kind: 'photograph',
    credit: 'FMNLab · CC BY 4.0 · Resized',
    source: 'https://commons.wikimedia.org/wiki/File:Measuring_a_qubit_leaves_no_room_for_error.jpg',
    description: 'FMN Laboratory engineers assemble the cryogenic hardware and measurement wiring for a superconducting quantum system.',
    equipment: ['quantum', 'control', 'research'],
  },
  {
    id: 'main-hall-concept',
    title: 'Main Quantum Lab concept',
    src: '/lab/photos/main-hall-concept.png',
    kind: 'illustration',
    credit: 'User-supplied concept illustration',
    source: '',
    description: 'Design reference for the lab hall. The displays and readouts are illustrative.',
    equipment: ['quantum', 'optics', 'control', 'optimization', 'research'],
  },
  {
    id: 'circuit-workbench-concept',
    title: 'Quantum Circuit Studio concept',
    src: '/lab/photos/circuit-workbench-concept.png',
    kind: 'illustration',
    credit: 'User-supplied concept illustration',
    source: '',
    description: 'Design reference for the circuit workbench. The depicted circuit, graphs and readouts are illustrative.',
    equipment: ['quantum', 'control'],
  },
  {
    id: 'photonics-lab-reference',
    title: 'Photonics Lab concept',
    src: '/lab/photos/photonics-lab-reference.png',
    kind: 'illustration',
    credit: 'User-supplied concept illustration',
    source: '',
    description: 'Design reference for the photonics workbench. The light paths, graphs and readouts are illustrative.',
    equipment: ['optics'],
  },
];
