import { mkdirSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { deflateSync, crc32 } from "node:zlib";
import * as T from "../frontend/node_modules/three/build/three.module.js";
import { mergeGeometries } from "../frontend/node_modules/three/examples/jsm/utils/BufferGeometryUtils.js";

const modelDir = new URL("../frontend/public/lab/models/", import.meta.url);
mkdirSync(modelDir, { recursive: true });

const materials = [];
const color = (hex) => hex.match(/../g).map((part) => {
  const srgb = Number.parseInt(part, 16) / 255;
  return srgb <= 0.04045 ? srgb / 12.92 : ((srgb + 0.055) / 1.055) ** 2.4;
});
function material(name, hex, metallicFactor = 0, roughnessFactor = .55, texture, emission) {
  const id = materials.length;
  materials.push({
    gltf: { name, pbrMetallicRoughness: { baseColorFactor: [...color(hex), 1], metallicFactor, roughnessFactor },
      ...(emission ? { emissiveFactor: color(emission) } : {}) },
    texture,
  });
  return id;
}

function bitmap(width, height, background) {
  const pixels = Buffer.alloc(width * height * 3);
  const set = (x, y, rgb) => {
    if (x < 0 || x >= width || y < 0 || y >= height) return;
    const i = (y * width + x) * 3;
    for (let c = 0; c < 3; c++) pixels[i + c] = rgb[c];
  };
  const rect = (x, y, w, h, rgb) => {
    for (let row = y; row < y + h; row++) {
      for (let col = x; col < x + w; col++) set(col, row, rgb);
    }
  };
  rect(0, 0, width, height, background);
  return { width, height, pixels, set, rect };
}

const alphabet = {
  A:["01110","10001","10001","11111","10001","10001","10001"],
  B:["11110","10001","10001","11110","10001","10001","11110"],
  C:["01111","10000","10000","10000","10000","10000","01111"],
  D:["11110","10001","10001","10001","10001","10001","11110"],
  E:["11111","10000","10000","11110","10000","10000","11111"],
  F:["11111","10000","10000","11110","10000","10000","10000"],
  G:["01111","10000","10000","10111","10001","10001","01111"],
  H:["10001","10001","10001","11111","10001","10001","10001"],
  I:["11111","00100","00100","00100","00100","00100","11111"],
  J:["00111","00010","00010","00010","10010","10010","01100"],
  K:["10001","10010","10100","11000","10100","10010","10001"],
  L:["10000","10000","10000","10000","10000","10000","11111"],
  M:["10001","11011","10101","10101","10001","10001","10001"],
  N:["10001","11001","10101","10011","10001","10001","10001"],
  O:["01110","10001","10001","10001","10001","10001","01110"],
  P:["11110","10001","10001","11110","10000","10000","10000"],
  Q:["01110","10001","10001","10001","10101","10010","01101"],
  R:["11110","10001","10001","11110","10100","10010","10001"],
  S:["01111","10000","10000","01110","00001","00001","11110"],
  T:["11111","00100","00100","00100","00100","00100","00100"],
  U:["10001","10001","10001","10001","10001","10001","01110"],
  V:["10001","10001","10001","10001","10001","01010","00100"],
  W:["10001","10001","10001","10101","10101","11011","10001"],
  X:["10001","10001","01010","00100","01010","10001","10001"],
  Y:["10001","10001","01010","00100","00100","00100","00100"],
  Z:["11111","00001","00010","00100","01000","10000","11111"],
  0:["01110","10001","10011","10101","11001","10001","01110"],
  1:["00100","01100","00100","00100","00100","00100","01110"],
  2:["01110","10001","00001","00010","00100","01000","11111"],
  3:["11110","00001","00001","01110","00001","00001","11110"],
  4:["00010","00110","01010","10010","11111","00010","00010"],
  5:["11111","10000","10000","11110","00001","00001","11110"],
  6:["01110","10000","10000","11110","10001","10001","01110"],
  7:["11111","00001","00010","00100","01000","01000","01000"],
  8:["01110","10001","10001","01110","10001","10001","01110"],
  9:["01110","10001","10001","01111","00001","00001","01110"],
  "-":["00000","00000","00000","11111","00000","00000","00000"],
  "/":["00001","00001","00010","00100","01000","10000","10000"],
};
function lettering(image, x, y, label, ink, scale = 1) {
  for (const character of label) {
    alphabet[character]?.forEach((row, j) => [...row].forEach((pixel, i) => {
      if (pixel === "1") image.rect(x + i * scale, y + j * scale, scale, scale, ink);
    }));
    x += 6 * scale;
  }
}
function png({ width, height, pixels }) {
  const header = Buffer.alloc(13);
  header.writeUInt32BE(width, 0);
  header.writeUInt32BE(height, 4);
  header[8] = 8;
  header[9] = 2;
  const stride = width * 3;
  const rows = Buffer.alloc(height * (stride + 1));
  for (let y = 0; y < height; y++) pixels.copy(rows, y * (stride + 1) + 1, y * stride, (y + 1) * stride);
  const chunk = (type, data) => {
    const body = Buffer.concat([Buffer.from(type), data]);
    const result = Buffer.alloc(12 + data.length);
    result.writeUInt32BE(data.length, 0);
    body.copy(result, 4);
    result.writeUInt32BE(crc32(body), result.length - 4);
    return result;
  };
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk("IHDR", header),
    chunk("IDAT", deflateSync(rows, { level: 9 })), chunk("IEND", Buffer.alloc(0))]);
}

function brushedMetal() {
  const image = bitmap(256, 256, [221, 221, 221]);
  for (let y = 0; y < image.height; y++) {
    const grain = 205 + 24 * Math.sin(y * 123.137) + 10 * Math.sin(y * 2.231);
    for (let x = 0; x < image.width; x++) {
      const light = Math.round(grain + 7 * Math.sin(x * .19 + y * 4.1));
      image.set(x, y, [light, light, light]);
    }
  }
  return png(image);
}
const panelLabels = [
  "QUANTUM FORGE", "VACUUM HEAD", "MIXING CHAMBER", "OPTICAL SOURCE",
  "PHOTODIODE", "REFERENCE ARM", "RF GENERATOR", "MICROWAVE CONTROL",
  "ACQUISITION", "CRYO READOUT", "PATCH PANEL", "TIMEBASE", "POWER DISTRIBUTION",
  "RF OUT", "TRIG", "INPUT A", "INPUT B", "SYNC", "CH 1", "CH 2",
  "IF OUT", "LO IN", "VACUUM", "STILL", "COLD PLATE", "THERMAL STAGE",
  "CONTROL STATION", "OPTICS", "REFLECTION", "DETECTOR", "OUTPUT", "STANDBY",
];
function labelAtlas() {
  const image = bitmap(256, 512, [28, 39, 49]);
  panelLabels.forEach((label, index) => {
    const y = index * 16;
    image.rect(1, y + 1, 254, 14, [34, 48, 59]);
    image.rect(2, y + 2, 2, 12, [85, 142, 162]);
    lettering(image, 9, y + 4, label, [214, 228, 229]);
  });
  return png(image);
}
function monitorTexture() {
  const image = bitmap(512, 288, [14, 26, 37]);
  const pale = [211, 228, 232];
  const blue = [88, 164, 183];
  const grid = [32, 56, 67];
  image.rect(0, 0, 512, 30, [30, 52, 65]);
  image.rect(0, 30, 512, 2, blue);
  lettering(image, 18, 8, "QUANTUM FORGE", pale, 2);
  lettering(image, 379, 11, "CONTROL STATION", pale, 1);
  image.rect(14, 46, 122, 204, [25, 42, 53]);
  ["SCHEMATIC", "PREPARE", "ENTANGLE", "MEASURE"].forEach((label, i) => {
    const y = 62 + i * 36;
    image.rect(22, y, 106, 22, i === 0 ? [46, 77, 94] : [32, 55, 68]);
    lettering(image, 28, y + 7, label, pale);
  });
  for (let x = 151; x < 493; x += 12) image.rect(x, 53, 1, 189, grid);
  for (let y = 53; y < 243; y += 12) image.rect(151, y, 342, 1, grid);
  lettering(image, 168, 67, "CIRCUIT SCHEMATIC", pale);
  for (const y of [124, 185]) image.rect(175, y, 297, 2, blue);
  lettering(image, 156, 121, "Q0", pale);
  lettering(image, 156, 182, "Q1", pale);
  image.rect(205, 112, 25, 26, blue);
  image.rect(207, 114, 21, 22, [27, 51, 65]);
  lettering(image, 215, 121, "H", pale);
  image.rect(302, 125, 2, 61, blue);
  image.rect(298, 120, 10, 10, blue);
  image.rect(296, 179, 14, 14, blue);
  image.rect(298, 181, 10, 10, [27, 51, 65]);
  image.rect(302, 180, 2, 12, blue);
  for (const y of [115, 176]) {
    image.rect(393, y, 24, 20, blue);
    image.rect(395, y + 2, 20, 16, [27, 51, 65]);
    lettering(image, 403, y + 6, "M", pale);
  }
  image.rect(0, 264, 512, 24, [30, 52, 65]);
  lettering(image, 18, 272, "ILLUSTRATIVE CIRCUIT VIEW", pale);
  return png(image);
}

const finish = brushedMetal();
const steel = material("Brushed stainless steel", "c3cbd0", .58, .39, finish);
const aluminum = material("Machined aluminum", "9ca9b0", .53, .43, finish);
const gold = material("Gold-plated copper", "e1aa4c", .53, .34, finish);
const copper = material("Copper thermal strap", "bf7753", .48, .46, finish);
const blue = material("Powder-coated blue steel", "314c61", .27, .52, finish);
const slate = material("Rack and instrument chassis", "424f59", .35, .48, finish);
const graphite = material("Anodized graphite", "262f36", .32, .47, finish);
const black = material("Black polymer and apertures", "1a2128", .08, .63);
const rubber = material("Rubber jacket", "20262d", .04, .85);
const cyan = material("Blue coax jacket", "5b8299", .1, .62);
const amber = material("Amber coax jacket", "b78c58", .14, .57);
const silverCable = material("Semi-rigid nickel coax", "b5bec3", .5, .38);
const warning = material("Amber enamel markings", "d9a85e", .1, .55);
const glass = material("Coated optic", "72a7b6", .43, .18);
const opticEdge = material("Beamsplitter coating", "a0bbc0", .55, .24);
const labels = material("Engraved instrument labels", "ffffff", .05, .72, labelAtlas());
const display = material("Illustrative circuit diagram", "ffffff", .03, .72, monitorTexture(), "a2a2a2");
const laminate = material("Cool light gray desk laminate", "c6c9c8", .07, .58, finish);
const cloth = material("Woven chair upholstery", "3b4b55", .02, .91, finish);

const parts = new Map();
function add(geometry, finish, position = [0, 0, 0], rotation = [0, 0, 0]) {
  geometry.rotateX(rotation[0]).rotateY(rotation[1]).rotateZ(rotation[2]).translate(...position);
  if (!parts.has(finish)) parts.set(finish, []);
  parts.get(finish).push(geometry);
}
function box(w, h, d, x, y, z, finish, rotation) {
  add(new T.BoxGeometry(w, h, d), finish, [x, y, z], rotation);
}
function plate(w, h, d, x, y, z, finish, bevel = .004, rotation) {
  const outline = new T.Shape();
  outline.moveTo(-w / 2 + bevel, -h / 2);
  outline.lineTo(w / 2 - bevel, -h / 2);
  outline.lineTo(w / 2, -h / 2 + bevel);
  outline.lineTo(w / 2, h / 2 - bevel);
  outline.lineTo(w / 2 - bevel, h / 2);
  outline.lineTo(-w / 2 + bevel, h / 2);
  outline.lineTo(-w / 2, h / 2 - bevel);
  outline.lineTo(-w / 2, -h / 2 + bevel);
  outline.closePath();
  const geometry = new T.ExtrudeGeometry(outline, {
    depth: d - 2 * bevel, bevelEnabled: true, bevelSize: bevel * .55, bevelThickness: bevel,
    bevelSegments: 1, steps: 1,
  }).translate(0, 0, -d / 2 + bevel);
  const indices = Array.from({ length: geometry.attributes.position.count }, (_, i) => i);
  geometry.setIndex(indices);
  const uv = geometry.attributes.uv;
  const p = geometry.attributes.position;
  for (let i = 0; i < uv.count; i++) uv.setXY(i, p.getX(i) / w + .5, p.getY(i) / h + .5);
  add(geometry, finish, [x, y, z], rotation);
}
function cyl(rt, rb, height, x, y, z, finish, sides = 16, rotation) {
  add(new T.CylinderGeometry(rt, rb, height, sides), finish, [x, y, z], rotation);
}
function lathe(profile, x, y, z, finish, segments = 32, rotation, start = 0, angle = Math.PI * 2) {
  add(new T.LatheGeometry(profile.map(([r, h]) => new T.Vector2(r, h)), segments, start, angle),
    finish, [x, y, z], rotation);
}
function ring(r, thickness, height, x, y, z, finish, rotation, sides = 28) {
  const inner = r - thickness;
  const h = height / 2;
  const bevel = Math.min(thickness, height) * .19;
  lathe([[inner, h - bevel], [inner, -h + bevel], [inner + bevel, -h], [r - bevel, -h],
    [r, -h + bevel], [r, h - bevel], [r - bevel, h], [inner + bevel, h], [inner, h - bevel]],
    x, y, z, finish, sides, rotation);
}
function rod(from, to, radius, finish, sides = 10) {
  const begin = new T.Vector3(...from);
  const end = new T.Vector3(...to);
  const vector = end.clone().sub(begin);
  const center = begin.addScaledVector(vector, .5);
  const mesh = new T.CylinderGeometry(radius, radius, vector.length(), sides);
  mesh.applyQuaternion(new T.Quaternion().setFromUnitVectors(new T.Vector3(0, 1, 0), vector.normalize()));
  add(mesh, finish, center.toArray());
}
function tube(points, radius, finish, segments = 20, sides = 7) {
  const curve = new T.CatmullRomCurve3(points.map((point) => new T.Vector3(...point)));
  add(new T.TubeGeometry(curve, segments, radius, sides), finish);
}
const face = [Math.PI / 2, 0, 0];
const horizontal = [-Math.PI / 2, 0, 0];
function fastener(x, y, z, radius = .007, front = false, finish = steel) {
  cyl(radius * 1.22, radius * 1.22, radius * .21, x, y, z, finish, 10, front ? face : undefined);
  cyl(radius, radius * 1.04, radius * .69, x, y + (front ? 0 : radius * .31),
    z + (front ? radius * .31 : 0), finish, 6, front ? face : undefined);
  if (front) box(radius * .92, radius * .23, .001, x, y, z + radius * .665, black);
}
function sign(label, w, h, x, y, z, rotation) {
  const slot = panelLabels.indexOf(label);
  if (slot < 0) throw new Error(`Unknown equipment label: ${label}`);
  const geom = new T.PlaneGeometry(w, h);
  const uv = geom.attributes.uv;
  const contentWidth = 15 + label.length * 6;
  for (let i = 0; i < uv.count; i++) {
    uv.setXY(i, (1 + uv.getX(i) * contentWidth) / 256, (slot * 16 + 15 - uv.getY(i) * 14) / 512);
  }
  add(geom, labels, [x, y, z], rotation);
}
function connector(x, y, z, scale = 1) {
  cyl(.013 * scale, .013 * scale, .006, x, y, z, slate, 12, face);
  cyl(.0095 * scale, .0095 * scale, .007, x, y, z + .005, steel, 6, face);
  ring(.0085 * scale, .003 * scale, .009, x, y, z + .013, steel, face, 14);
  cyl(.0053 * scale, .0053 * scale, .001, x, y, z + .014, black, 12, face);
  cyl(.0015 * scale, .0015 * scale, .001, x, y, z + .0147, gold, 8, face);
}

function dilutionRefrigerator() {
  const frameWidth = .738;
  for (const x of [-frameWidth, frameWidth]) {
    for (const z of [-.583, .43]) {
      plate(.092, .035, .154, x, .018, z, black, .003);
      box(.055, 2.67, .055, x, 1.377, z, blue);
      for (const y of [.12, 2.57]) {
        box(.07, .10, .062, x, y, z, slate);
        for (const offset of [-.027, .027]) fastener(x, y + offset, z + .032, .009, true);
      }
      box(.004, 2.45, .005, x, 1.37, z + .028, aluminum);
    }
    box(.055, .06, 1.19, x, 2.68, -.063, blue);
    box(.057, .07, 1.11, x, .167, -.07, blue);
    box(.048, .057, 1.06, x, 2.11, -.074, blue);
  }
  for (const z of [-.583, .43]) {
    box(1.53, .061, .055, 0, 2.68, z, blue);
    box(1.53, .07, .055, 0, .167, z, blue);
  }
  rod([-.69, .28, -.595], [.69, 1.76, -.595], .015, blue);
  rod([.69, .28, -.604], [-.69, 1.76, -.604], .015, blue);
  plate(1.45, .114, .039, 0, 2.632, .447, slate, .007);
  sign("QUANTUM FORGE", .28, .042, -.483, 2.637, .468);
  sign("VACUUM HEAD", .23, .035, .445, 2.637, .468);

  lathe([[.001, 0], [.477, 0], [.493, .015], [.493, .042], [.466, .05], [.455, .072],
    [.455, .252], [.448, .283], [.411, .311], [.001, .311]],
  0, 2.43, -.045, steel, 64);
  ring(.484, .052, .018, 0, 2.715, -.045, aluminum, undefined, 56);
  ring(.502, .047, .029, 0, 2.438, -.045, steel, undefined, 56);
  ring(.472, .038, .011, 0, 2.412, -.045, graphite, undefined, 56);
  for (let i = 0; i < 20; i++) {
    const a = 2 * Math.PI * i / 20;
    fastener(.473 * Math.sin(a), 2.456, -.045 + .473 * Math.cos(a), .011);
  }
  for (const [x, z, r] of [[-.29, -.15, .054], [.25, -.26, .064], [.05, .20, .044]]) {
    cyl(r, r * 1.11, .055, x, 2.766, z, slate, 20);
    ring(r * 1.03, .012, .024, x, 2.807, z, steel, undefined, 24);
    cyl(r * .63, r * .63, .012, x, 2.823, z, black, 18);
  }
  cyl(.083, .083, .073, .44, 2.57, -.045, steel, 22, [0, 0, Math.PI / 2]);
  ring(.093, .024, .019, .478, 2.57, -.045, aluminum, [0, 0, Math.PI / 2]);
  cyl(.06, .06, .025, .492, 2.57, -.045, graphite, 22, [0, 0, Math.PI / 2]);

  // A rear arc suggests the vacuum can's wall while exposing the stages to the visitor.
  const cutStart = Math.PI * .42;
  const cutSweep = Math.PI * 1.16;
  lathe([[.474, 1.162], [.474, .011], [.485, 0], [.501, 0], [.509, .014],
    [.509, 1.162], [.498, 1.176], [.482, 1.176], [.474, 1.162]],
  0, 1.224, -.098, aluminum, 36, undefined, cutStart, cutSweep);
  for (const a of [cutStart, cutStart + cutSweep]) {
    const x = .493 * Math.sin(a);
    const z = -.098 + .493 * Math.cos(a);
    rod([x, 1.231, z], [x, 2.394, z], .014, steel);
  }

  const stages = [
    { y: 2.349, r: .427, label: "VACUUM" },
    { y: 2.067, r: .394, label: "THERMAL STAGE" },
    { y: 1.755, r: .353, label: "STILL" },
    { y: 1.423, r: .308, label: "COLD PLATE" },
    { y: 1.078, r: .257, label: "MIXING CHAMBER" },
  ];
  stages.forEach(({ y, r, label }, index) => {
    const finish = index === 0 ? aluminum : gold;
    lathe([[.001, -.026], [r - .017, -.026], [r - .017, -.017], [r - .006, -.017], [r, -.011],
      [r, .014], [r - .005, .020], [r - .024, .020], [r - .024, .027], [.001, .027]],
    0, y, -.035, finish, 56);
    ring(r - .006, .018, .008, 0, y - .02, -.035, index === 0 ? steel : copper, undefined, 48);
    for (let i = 0; i < 18; i++) {
      const a = 2 * Math.PI * (i + .3) / 18;
      const x = (r - .016) * Math.sin(a);
      const z = -.035 + (r - .016) * Math.cos(a);
      fastener(x, y + .025, z, .008, false, index === 0 ? steel : gold);
    }
    plate(.145, .035, .012, 0, y - .012, r - .023, graphite, .003);
    sign(label, .132, .021, 0, y - .012, r - .016);
  });

  for (const a of [-1.41, 1.41, 2.65, -2.65]) {
    const aX = Math.sin(a);
    const aZ = Math.cos(a);
    for (let i = 0; i < stages.length - 1; i++) {
      const first = stages[i];
      const second = stages[i + 1];
      const r = second.r - .039;
      const x = r * aX;
      const z = -.035 + r * aZ;
      rod([x, second.y, z], [x, first.y, z], .013, steel);
      for (const y of [second.y + .034, first.y - .033]) {
        cyl(.023, .023, .017, x, y, z, gold, 6);
        cyl(.025, .025, .004, x, y - .009, z, copper, 12);
      }
    }
  }

  for (let i = 0; i < 14; i++) {
    const side = i < 7 ? 1 : -1;
    const lane = (i % 7) / 6;
    const points = [[side * (.152 + lane * .064), 2.421, .226 + lane * .056]];
    stages.forEach(({ y, r }, index) => {
      const azimuth = .28 + lane * 1.11;
      const x = side * (r - .019) * Math.sin(azimuth);
      const z = -.035 + (r - .012) * Math.cos(azimuth);
      const offset = .027 + (i % 3) * .012;
      points.push([x + side * offset, y + .125, z + offset * .8], [x, y + .028, z], [x, y - .041, z]);
      cyl(.011, .011, .029, x, y + .038, z, index % 2 ? gold : steel, 8);
      if (index !== stages.length - 1 && i % 2 === 0) {
        box(.044, .058, .034, x + side * .017, y - .115, z - .007, copper);
        fastener(x + side * .027, y - .115, z + .012, .005, true);
      }
    });
    points.push([side * (.057 + lane * .075), .973 + lane * .057, .126 - lane * .024]);
    tube(points, .004 + lane * .0014, [silverCable, cyan, amber, rubber][i % 4], 56, 7);
  }

  lathe([[.001, 0], [.083, 0], [.088, .008], [.088, .025], [.064, .032], [.064, .098],
    [.071, .103], [.071, .126], [.104, .126], [.104, .15], [.001, .15]],
  0, .889, -.035, gold, 32);
  plate(.122, .067, .096, 0, .922, .108, copper, .005);
  plate(.084, .046, .011, 0, .922, .162, gold, .003);
  for (const x of [-.037, .037]) {
    for (const y of [.908, .936]) fastener(x, y, .17, .004, true);
  }
  plate(.425, .105, .213, -.283, .222, -.329, graphite, .008);
  sign("VACUUM", .099, .024, -.36, .239, -.220);
  tube([[-.4, .24, -.29], [-.54, .37, -.35], [-.54, .82, -.34], [-.51, 1.46, -.31],
    [-.52, 2.24, -.22], [-.55, 2.56, -.04], [-.48, 2.58, -.045]], .025, rubber, 40, 10);
}

function perforatedBreadboard() {
  const width = 2.996;
  const depth = 1.18;
  const top = .83;
  const underside = .776;
  const columns = 60;
  const rows = 24;
  const dx = width / columns;
  const dz = depth / rows;
  const sides = 8;
  const radius = .0077;
  const positions = [];
  const normals = [];
  const uvs = [];
  const indices = [];
  const wallPositions = [];
  const wallNormals = [];
  const wallUVs = [];
  const wallIndices = [];
  for (let i = 0; i < columns; i++) {
    for (let j = 0; j < rows; j++) {
      const x = (i + .5) * dx - width / 2;
      const z = (j + .5) * dz - depth / 2;
      const start = positions.length / 3;
      const walls = wallPositions.length / 3;
      for (let k = 0; k < sides; k++) {
        const angle = Math.PI * 2 * k / sides;
        const nx = Math.cos(angle);
        const nz = -Math.sin(angle);
        const edge = .5 / Math.max(Math.abs(nx), Math.abs(nz));
        const innerX = x + radius * nx;
        const innerZ = z + radius * nz;
        const outerX = x + edge * dx * nx;
        const outerZ = z + edge * dz * nz;
        positions.push(innerX, top, innerZ, outerX, top, outerZ);
        normals.push(0, 1, 0, 0, 1, 0);
        uvs.push(innerX / width + .5, innerZ / depth + .5, outerX / width + .5, outerZ / depth + .5);
        wallPositions.push(innerX, top, innerZ, innerX, top - .012, innerZ);
        wallNormals.push(-nx, 0, -nz, -nx, 0, -nz);
        wallUVs.push(k / sides, 0, k / sides, 1);
        const a = start + k * 2;
        const b = start + ((k + 1) % sides) * 2;
        indices.push(a, a + 1, b + 1, a, b + 1, b);
        const c = walls + k * 2;
        const d = walls + ((k + 1) % sides) * 2;
        wallIndices.push(c, d, d + 1, c, d + 1, c + 1);
      }
    }
  }
  function indexedMesh(p, n, uv, ix) {
    const geometry = new T.BufferGeometry();
    geometry.setAttribute("position", new T.Float32BufferAttribute(p, 3));
    geometry.setAttribute("normal", new T.Float32BufferAttribute(n, 3));
    geometry.setAttribute("uv", new T.Float32BufferAttribute(uv, 2));
    geometry.setIndex(ix);
    return geometry;
  }
  add(indexedMesh(positions, normals, uvs, indices), steel);
  add(indexedMesh(wallPositions, wallNormals, wallUVs, wallIndices), graphite);
  box(width, .04, depth, 0, underside + .018, 0, slate);
  for (const z of [-depth / 2, depth / 2]) box(width, .049, .012, 0, top - .0245, z, aluminum);
  for (const x of [-width / 2, width / 2]) box(.012, .049, depth, x, top - .0245, 0, aluminum);
}

function opticalBench() {
  perforatedBreadboard();
  for (const x of [-1.26, 1.26]) {
    box(.142, .061, .86, x, .032, 0, slate);
    for (const z of [-.385, .385]) {
      cyl(.062, .065, .031, x, .016, z, rubber, 16);
      cyl(.027, .029, .045, x, .054, z, steel, 12);
      box(.092, .683, .092, x, .41, z, blue);
      box(.013, .63, .006, x, .415, z + .047, aluminum);
      box(.12, .074, .12, x, .745, z, slate);
      for (const offset of [-.038, .038]) fastener(x + offset, .768, z + .062, .007, true);
    }
    box(.082, .067, .79, x, .217, 0, blue);
  }
  box(2.55, .076, .075, 0, .223, -.385, blue);
  plate(1.028, .073, .042, -.72, .747, .474, slate, .004);
  sign("OPTICS", .131, .03, -1.139, .745, .496);
  sign("REFERENCE ARM", .203, .03, -.598, .745, .496);
  for (const x of [-1.19, -.234]) fastener(x, .745, .496, .007, true);

  function rail(w, x, z, angle = 0) {
    const point = (s, t) => [x + s * Math.cos(angle) + t * Math.sin(angle), z - s * Math.sin(angle) + t * Math.cos(angle)];
    box(w, .024, .06, x, .843, z, graphite, [0, angle, 0]);
    for (const edge of [-.028, .028]) {
      const [qx, qz] = point(0, edge);
      box(w, .007, .01, qx, .858, qz, steel, [0, angle, 0]);
    }
    for (const end of [-w / 2 + .028, w / 2 - .028]) {
      const [qx, qz] = point(end, 0);
      fastener(qx, .857, qz, .007);
    }
  }
  rail(2.615, .001, .003);
  rail(.674, .27, .0, Math.PI / 2);
  rail(.817, .58, -.367);
  rail(.442, -.522, .235, Math.PI / 2);

  function post(x, z, y = 1.011) {
    plate(.118, .092, .019, x, .865, z, graphite, .004, horizontal);
    for (const dx of [-.044, .044]) for (const dz of [-.029, .029]) fastener(x + dx, .876, z + dz, .005);
    cyl(.029, .035, .02, x, .887, z, aluminum, 18);
    cyl(.018, .019, .084, x, .933, z, graphite, 16);
    rod([x, .95, z], [x, y, z], .01, steel, 12);
    cyl(.014, .014, .027, x + .023, .935, z, aluminum, 12, [0, 0, Math.PI / 2]);
    cyl(.019, .019, .01, x + .036, .935, z, slate, 12, [0, 0, Math.PI / 2]);
  }
  function lens(x, z, r) {
    const y = 1.053;
    post(x, z, y - r + .013);
    const axis = [0, 0, Math.PI / 2];
    ring(r, .016, .03, x, y, z, graphite, axis, 28);
    ring(r - .003, .009, .007, x - .016, y, z, steel, axis, 24);
    ring(r - .003, .009, .007, x + .016, y, z, aluminum, axis, 24);
    cyl(r - .014, r - .014, .006, x, y, z, glass, 28, axis);
    box(.022, .017, .054, x, y - r + .005, z, slate);
    fastener(x, y - r + .011, z + .030, .005, true);
  }
  function mirror(x, z, yaw) {
    post(x, z, .991);
    const y = 1.052;
    plate(.107, .113, .036, x, y, z, graphite, .005, [0, yaw, 0]);
    const turn = [Math.PI / 2, yaw, 0];
    const [dx, dz] = [Math.sin(yaw), Math.cos(yaw)];
    ring(.047, .008, .014, x + .017 * dx, y, z + .017 * dz, aluminum, turn, 24);
    cyl(.039, .039, .005, x + .024 * dx, y, z + .024 * dz, opticEdge, 26, turn);
    for (const [px, py] of [[.032, .039], [-.035, -.041]]) {
      const qx = x + Math.cos(yaw) * px - dx * .028;
      const qz = z - Math.sin(yaw) * px - dz * .028;
      cyl(.009, .009, .025, qx, y + py, qz, steel, 10, turn);
    }
  }
  function detector(x, z, yaw) {
    post(x, z, 1.005);
    plate(.085, .102, .102, x, 1.052, z, slate, .006, [0, yaw, 0]);
    const [dx, dz] = [Math.sin(yaw), Math.cos(yaw)];
    const turn = [Math.PI / 2, yaw, 0];
    ring(.032, .012, .023, x + dx * .055, 1.053, z + dz * .055, graphite, turn, 20);
    cyl(.02, .02, .005, x + dx * .061, 1.053, z + dz * .061, glass, 20, turn);
    sign("PHOTODIODE", .072, .018, x, 1.107, z, horizontal);
    const sx = x - dx * .053;
    const sz = z - dz * .053;
    cyl(.009, .009, .018, sx, 1.034, sz, steel, 10, turn);
    tube([[sx, 1.034, sz], [sx - dx * .08, 1.015, sz - dz * .08], [x + .093, .875, z + .08],
      [x + .163, .852, z + .15], [x + .15, .849, .52], [x + .10, .823, .588],
      [x + .04, .715, .605], [x - .1, .684, .553]], .005, rubber, 25);
  }

  const sourceX = -1.053;
  plate(.304, .161, .221, sourceX, 1.01, .003, slate, .009);
  plate(.336, .042, .246, sourceX, .89, .003, graphite, .006);
  for (const z of [-.093, .097]) {
    for (const x of [-1.183, -.922]) fastener(x, .913, z, .006);
  }
  for (let i = 0; i < 10; i++) box(.008, .005, .17, -1.155 + i * .021, 1.093, .003, black);
  sign("OPTICAL SOURCE", .155, .029, -1.079, 1.037, .116);
  plate(.066, .018, .003, -1.121, .982, .117, warning, .001);
  cyl(.01, .01, .006, -.94, .986, .118, black, 12, face);
  ring(.049, .015, .029, -.889, 1.053, .003, graphite, [0, 0, Math.PI / 2], 24);
  ring(.037, .008, .014, -.87, 1.053, .003, steel, [0, 0, Math.PI / 2], 20);
  cyl(.028, .028, .005, -.868, 1.053, .003, black, 20, [0, 0, Math.PI / 2]);
  cyl(.012, .012, .004, -.864, 1.053, .003, glass, 16, [0, 0, Math.PI / 2]);
  tube([[-1.2, .997, -.044], [-1.31, .957, -.093], [-1.321, .853, -.193],
    [-1.172, .851, -.379], [-1.03, .852, -.55], [-1.022, .79, -.601], [-1.041, .7, -.56]], .0075, rubber, 24);

  for (const [x, r] of [[-.689, .061], [-.413, .05], [.63, .053]]) lens(x, .003, r);
  post(.246, .003, 1.002);
  plate(.106, .096, .106, .246, 1.053, .003, glass, .003);
  plate(.138, .016, .126, .246, .999, .003, graphite, .003);
  plate(.139, .012, .007, .246, 1.053, .059, opticEdge, .001, [0, 0, Math.PI / 4]);
  mirror(.246, -.367, Math.PI * .25);
  mirror(-.117, .299, -Math.PI * .25);
  detector(1.078, .003, -Math.PI / 2);
  detector(.803, -.367, -Math.PI / 2);
  for (const [x, z] of [[-.477, .268], [.516, .291]]) {
    plate(.167, .075, .116, x, .877, z, slate, .005);
    sign("OUTPUT", .077, .024, x - .03, .892, z + .06);
    connector(x + .04, .869, z + .064, .73);
    for (const dx of [-.063, .063]) fastener(x + dx, .917, z - .037, .006);
  }
}

function electronicsRack() {
  for (const x of [-.287, .287]) {
    for (const z of [-.365, .346]) {
      cyl(.032, .036, .035, x, .0175, z, rubber, 14);
      box(.046, 1.936, .044, x, 1.01, z, blue);
    }
    for (const y of [.06, 1.96]) box(.05, .06, .79, x, y, -.01, slate);
    plate(1.896, .699, .028, x, 1.021, -.032, blue, .006, [Math.PI / 2, 0, Math.PI / 2]);
    for (let i = 0; i < 14; i++) box(.002, .008, .082, x + Math.sign(x) * .016, 1.78 - .018 * i, -.25, black);
  }
  for (const z of [-.365, .346]) {
    box(.613, .048, .049, 0, 1.977, z, slate);
    box(.613, .05, .049, 0, .063, z, slate);
  }
  plate(.62, .822, .037, 0, 2.018, -.018, blue, .005, horizontal);
  plate(.62, .813, .04, 0, .075, -.015, graphite, .006, horizontal);
  plate(.514, 1.84, .025, 0, .99, -.383, slate, .007);
  for (const x of [-.246, .246]) {
    box(.029, 1.817, .026, x, 1.014, .363, aluminum);
    for (let i = 0; i < 36; i++) box(.011, .012, .001, x, .131 + i * .0502, .377, black);
  }

  const panelZ = .376;
  const panels = [
    { y: 1.86, h: .105, label: "TIMEBASE", material: graphite, ports: 4 },
    { y: 1.681, h: .234, label: "MICROWAVE CONTROL", material: slate, ports: 4, screen: true, knob: true },
    { y: 1.421, h: .264, label: "RF GENERATOR", material: aluminum, ports: 3, screen: true, knob: true },
    { y: 1.155, h: .246, label: "ACQUISITION", material: graphite, ports: 6, slots: 11 },
    { y: .899, h: .247, label: "CRYO READOUT", material: slate, ports: 4, screen: true, knob: true },
    { y: .658, h: .21, label: "PATCH PANEL", material: graphite, ports: 8, doubled: true },
    { y: .434, h: .208, label: "POWER DISTRIBUTION", material: slate, ports: 0, slots: 16 },
  ];
  panels.forEach(({ y, h, label, material, ports, screen, knob, slots, doubled }) => {
    plate(.465, h, .057, 0, y, panelZ - .028, material, .005);
    sign(label, Math.max(.135, label.length * .008), .021, -.146, y + h / 2 - .024, panelZ + .002);
    for (const x of [-.211, .211]) {
      for (const dy of [-h / 2 + .017, h / 2 - .017]) fastener(x, y + dy, panelZ + .004, .0055, true);
    }
    if (screen) {
      plate(.206, .067, .01, -.07, y + .013, panelZ + .007, graphite, .003);
      plate(.189, .051, .005, -.07, y + .013, panelZ + .013, black, .002);
      sign("STANDBY", .092, .016, -.105, y + .013, panelZ + .016);
    }
    if (knob) {
      ring(.032, .005, .005, .122, y + .024, panelZ + .006, aluminum, face, 24);
      cyl(.024, .025, .025, .122, y + .024, panelZ + .018, graphite, 18, face);
      cyl(.022, .023, .005, .122, y + .024, panelZ + .032, steel, 18, face);
      box(.002, .009, .002, .122, y + .035, panelZ + .036, black);
      for (const dy of [-.012, .012]) {
        plate(.016, .011, .004, .183, y + .015 + dy, panelZ + .005, graphite, .001);
      }
    }
    const portNames = ["RF OUT", "TRIG", "INPUT A", "INPUT B", "SYNC", "CH 1", "CH 2", "IF OUT", "LO IN"];
    for (let i = 0; i < ports; i++) {
      const x = -.175 + i * (ports === 8 ? .05 : .064);
      const dy = h > .16 ? -.051 : -.012;
      connector(x, y + dy, panelZ + .003);
      sign(portNames[i], .04, .009, x, y + dy - .019, panelZ + .002);
      if (doubled) connector(x, y + dy + .057, panelZ + .003, .85);
    }
    for (let i = 0; i < (slots || 0); i++) {
      box(.012, .036, .002, .19 - i * .019, y + .03, panelZ + .002, black);
      box(.012, .002, .002, .19 - i * .019, y + .01, panelZ + .0025, aluminum);
    }
  });
  plate(.465, .199, .056, 0, .224, .348, graphite, .005);
  for (let i = 0; i < 26; i++) {
    const x = -.183 + i * .0146;
    box(.007, .112, .002, x, .225, .378, black);
    box(.002, .108, .001, x - .004, .225, .3785, slate);
  }
  for (const x of [-.219, .219]) for (const y of [.146, .309]) fastener(x, y, .378, .0055, true);
  for (let i = 0; i < 6; i++) {
    const x = -.175 + i * .05;
    const left = i % 2 === 0;
    const edge = left ? -.221 : .223;
    const targetY = i % 3 === 0 ? 1.104 : .848;
    const targetX = -.175 + i % 4 * .064;
    const z = .414 + (i % 3) * .01;
    tube([[x, .607, .392], [x, .573, z], [edge * .83, .555 - .018 * i, z],
      [edge, .671, z], [edge, targetY - .122 - .014 * i, z], [targetX, targetY - .055, z + .01],
      [targetX, targetY, .394]], .0043, [cyan, amber, rubber][i % 3], 24, 7);
    cyl(.008, .008, .018, x, .607, .4, graphite, 10, face);
  }
  for (let i = 0; i < 5; i++) {
    const x = -.19 + i * .09;
    tube([[x, 1.87, -.406], [x, 1.82, -.439], [x + .021, 1.36, -.436],
      [x + .043, .85, -.427], [x + .04, .27, -.42], [x + .083, .139, -.398]], .005,
    i % 2 ? rubber : cyan, 25);
  }
}

function workstation() {
  const deskZ = -.322;
  plate(1.446, .712, .04, 0, .75, deskZ, laminate, .008, horizontal);
  for (const x of [-.627, .627]) {
    box(.059, .058, .589, x, .699, deskZ, slate);
    for (const z of [-.584, -.074]) {
      cyl(.027, .028, .031, x, .0155, z, rubber, 14);
      box(.051, .674, .055, x, .356, z, blue);
      box(.006, .631, .003, x, .36, z + .028, aluminum);
      for (const y of [.111, .673]) fastener(x, y, z + .031, .005, true);
    }
  }
  box(1.255, .073, .045, 0, .682, -.571, blue);
  plate(1.104, .186, .024, 0, .574, -.593, slate, .004);
  for (let i = 0; i < 18; i++) box(.008, .041, .002, -.43 + i * .05, .566, -.58, black);

  const screenX = -.155;
  const screenY = 1.172;
  const screenZ = -.51;
  plate(.305, .197, .018, screenX, .783, -.526, graphite, .006, horizontal);
  plate(.208, .112, .012, screenX, .794, -.532, aluminum, .003, horizontal);
  plate(.046, .272, .057, screenX, .925, -.551, slate, .004, [0, 0, .031]);
  box(.071, .081, .059, screenX, 1.083, -.556, graphite);
  plate(.637, .373, .042, screenX, screenY, screenZ, graphite, .01);
  plate(.619, .35, .008, screenX, screenY + .003, screenZ + .021, black, .003);
  const surface = new T.PlaneGeometry(.607, .336);
  const uv = surface.attributes.uv;
  for (let i = 0; i < uv.count; i++) uv.setY(i, 1 - uv.getY(i));
  add(surface, display, [screenX, screenY + .004, screenZ + .026]);
  box(.007, .003, .001, screenX + .274, screenY - .175, screenZ + .024, cyan);
  for (let i = 0; i < 14; i++) box(.011, .031, .002, screenX - .105 + i * .016, 1.104, -.533, black);
  tube([[screenX, 1.102, -.536], [screenX + .035, 1.057, -.577], [screenX + .04, .918, -.593],
    [screenX + .046, .793, -.609], [screenX + .162, .781, -.644], [.158, .769, -.657]], .004, rubber, 23);

  const keyboardX = -.157;
  const keyboardZ = -.099;
  plate(.459, .148, .016, keyboardX, .781, keyboardZ, graphite, .005, horizontal);
  for (let row = 0; row < 5; row++) {
    for (let i = 0; i < 14; i++) {
      if (row === 4 && i >= 4 && i <= 8) continue;
      const x = keyboardX - .202 + i * .031;
      const z = keyboardZ - .056 + row * .027;
      box(.025, .008, .022, x, .791, z, row === 0 ? slate : black);
      if (row < 4) box(.0045, .001, .0035, x - .005, .7955, z - .004, aluminum);
    }
  }
  box(.145, .008, .022, keyboardX - .016, .791, keyboardZ + .052, slate);
  plate(.14, .101, .012, .253, .778, -.097, graphite, .004, horizontal);
  box(.122, .001, .083, .253, .785, -.097, slate);
  plate(.104, .051, .103, .493, .796, -.411, graphite, .004);
  sign("SYNC", .056, .014, .487, .805, -.359);
  connector(.522, .786, -.358, .57);
  tube([[.51, .803, -.466], [.49, .785, -.51], [.423, .78, -.571], [.37, .779, -.653]], .0035, rubber, 16);

  const chairX = .048;
  const chairZ = .422;
  cyl(.041, .045, .116, chairX, .134, chairZ, slate, 14);
  cyl(.03, .032, .223, chairX, .279, chairZ, graphite, 14);
  cyl(.02, .02, .13, chairX, .407, chairZ, steel, 14);
  for (let i = 0; i < 5; i++) {
    const a = Math.PI * 2 * i / 5;
    const nx = Math.sin(a);
    const nz = Math.cos(a);
    const x = chairX + nx * .259;
    const z = chairZ + nz * .259;
    rod([chairX, .114, chairZ], [x, .065, z], .022, graphite, 10);
    cyl(.014, .015, .048, x, .054, z, graphite, 10);
    for (const offset of [-.013, .013]) {
      cyl(.029, .029, .013, x + nz * offset, .029, z - nx * offset, rubber, 14, [face[0], a + Math.PI / 2, 0]);
    }
  }
  plate(.471, .414, .045, chairX, .454, chairZ, graphite, .011, horizontal);
  plate(.441, .389, .049, chairX, .481, chairZ, cloth, .018, horizontal);
  tube([[chairX, .438, chairZ + .079], [chairX, .459, chairZ + .186],
    [chairX, .551, chairZ + .224], [chairX, .786, chairZ + .225]], .026, graphite, 18, 10);
  const backZ = chairZ + .209;
  plate(.402, .392, .049, chairX, .765, backZ, graphite, .019, [.105, 0, 0]);
  plate(.37, .352, .045, chairX, .771, backZ - .029, cloth, .017, [.105, 0, 0]);
  for (const x of [chairX - .237, chairX + .237]) {
    tube([[x, .456, chairZ + .035], [x, .508, chairZ + .087], [x, .601, chairZ + .071], [x, .635, chairZ + .031]],
      .016, graphite, 14, 9);
    plate(.063, .204, .027, x, .643, chairZ + .018, rubber, .008, horizontal);
  }
}

function exportModel(name, build) {
  parts.clear();
  build();
  const gltf = {
    asset: { version: "2.0", generator: "Quantum Forge equipment asset builder" },
    scene: 0, scenes: [{ nodes: [0] }], nodes: [{ name, mesh: 0 }],
    meshes: [{ name, primitives: [] }],
    materials: [], buffers: [], bufferViews: [], accessors: [],
    extras: { purpose: "Illustrative educational model", coordinateSystem: "Meters; y-up; +z faces visitors" },
  };
  const packed = [];
  let offset = 0;
  function pushView(array, target) {
    const bytes = Buffer.from(array.buffer, array.byteOffset, array.byteLength);
    const index = gltf.bufferViews.length;
    gltf.bufferViews.push({ buffer: 0, byteOffset: offset, byteLength: bytes.length, ...(target ? { target } : {}) });
    const pad = (4 - bytes.length % 4) % 4;
    packed.push(bytes, Buffer.alloc(pad));
    offset += bytes.length + pad;
    return index;
  }
  function accessor(attribute, type, componentType, bounds, target = 34962) {
    const index = gltf.accessors.length;
    gltf.accessors.push({
      bufferView: pushView(attribute.array, target), componentType, count: attribute.count, type, ...bounds,
    });
    return index;
  }

  const assembled = [...parts.entries()].map(([id, geometries]) => {
    const merged = mergeGeometries(geometries);
    if (!merged) throw new Error(`Could not merge ${name}: ${materials[id].gltf.name}`);
    merged.computeBoundingBox();
    return [id, merged];
  });
  const bounds = new T.Box3();
  for (const [, geometry] of assembled) bounds.union(geometry.boundingBox);
  const center = bounds.getCenter(new T.Vector3());
  const textures = new Map();
  let triangles = 0;
  for (const [id, geometry] of assembled) {
    geometry.translate(-center.x, -bounds.min.y, -center.z);
    geometry.computeBoundingBox();
    const data = materials[id];
    const exportedMaterial = structuredClone(data.gltf);
    if (data.texture) {
      if (!textures.has(data.texture)) {
        const index = textures.size;
        textures.set(data.texture, index);
        (gltf.images ??= []).push({ bufferView: pushView(data.texture), mimeType: "image/png" });
        (gltf.textures ??= []).push({ sampler: 0, source: index });
      }
      const index = textures.get(data.texture);
      exportedMaterial.pbrMetallicRoughness.baseColorTexture = { index };
      if (exportedMaterial.emissiveFactor) exportedMaterial.emissiveTexture = { index };
    }
    const material = gltf.materials.push(exportedMaterial) - 1;
    const attributes = geometry.attributes;
    const positions = accessor(attributes.position, "VEC3", 5126, {
      min: geometry.boundingBox.min.toArray(), max: geometry.boundingBox.max.toArray(),
    });
    const indices = geometry.index;
    triangles += indices.count / 3;
    gltf.meshes[0].primitives.push({
      material,
      attributes: {
        POSITION: positions, NORMAL: accessor(attributes.normal, "VEC3", 5126),
        TEXCOORD_0: accessor(attributes.uv, "VEC2", 5126),
      },
      indices: accessor(indices, "SCALAR", indices.array instanceof Uint32Array ? 5125 : 5123, {}, 34963),
    });
  }
  if (textures.size) gltf.samplers = [{ magFilter: 9729, minFilter: 9987, wrapS: 10497, wrapT: 10497 }];
  gltf.buffers.push({ byteLength: offset });
  const body = Buffer.from(JSON.stringify(gltf));
  const json = Buffer.concat([body, Buffer.alloc((4 - body.length % 4) % 4, 0x20)]);
  const header = Buffer.alloc(12);
  header.writeUInt32LE(0x46546c67, 0);
  header.writeUInt32LE(2, 4);
  header.writeUInt32LE(12 + 8 + json.length + 8 + offset, 8);
  function chunkHeader(size, type) {
    const bytes = Buffer.alloc(8);
    bytes.writeUInt32LE(size, 0);
    bytes.write(type, 4, "ascii");
    return bytes;
  }
  const file = Buffer.concat([header, chunkHeader(json.length, "JSON"), json, chunkHeader(offset, "BIN\0"), ...packed]);
  writeFileSync(new URL(`${name}.glb`, modelDir), file);
  console.log(`${name}: ${triangles.toLocaleString("en-US")} triangles, ${assembled.length} draws, ${textures.size} PNGs, ${(file.length / 1e6).toFixed(2)} MB, ${bounds.getSize(new T.Vector3()).toArray().map((n) => n.toFixed(3)).join(" × ")} m`);
}

const models = [
  ["dilution-refrigerator", dilutionRefrigerator],
  ["optical-bench", opticalBench],
  ["electronics-rack", electronicsRack],
  ["workstation", workstation],
];
for (const [name, build] of models) exportModel(name, build);
console.log(`Wrote assets to ${fileURLToPath(modelDir)}`);
