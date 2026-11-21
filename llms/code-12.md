# simulacra-americana: source and docs, part 12 of 17

Generated from commit `61ba45dc3c4c` (2026-11-20) of github.com/partyhat-ai/simulacra-americana by `scripts/llms_digest.py`, which `.github/workflows/llms-digest.yml` reruns on every push to `main`, so this text matches the code at that commit.
Files `src/lib/robot/blast.ts` to `src/lib/simulacra/KindChips.svelte`. Lines are numbered as in the repository.

## `src/lib/robot/blast.ts`

```ts
    1| // Shots from the robot's chest reactor, on demand (a tap on the robot): one
    2| // streamlined bolt in the shot's colour inside a soft sheath of the same
    3| // shape, a flash and a light at the chest as it leaves, and a small recoil of
    4| // the whole robot. Sizes are in robot heights, so it fires to its own scale.
    5| import {
    6|   AdditiveBlending,
    7|   Color,
    8|   DoubleSide,
    9|   Group,
   10|   IcosahedronGeometry,
   11|   LatheGeometry,
   12|   Mesh,
   13|   MeshBasicMaterial,
   14|   PointLight,
   15|   type Scene,
   16|   ShaderMaterial,
   17|   Vector2,
   18|   Vector3,
   19| } from 'three';
   20| 
   21| /** Seconds a shot lives; it fades over the last FADE_S. */
   22| export const SHOT_LIFE_S = 1.6;
   23| const FADE_S = 0.25;
   24| /** The muzzle flash's burst, seconds. */
   25| export const FLASH_S = 0.22;
   26| /** The shot stretches from compressed to full length over this, seconds. */
   27| const STRETCH_S = 0.1;
   28| /** The recoil eases out at this rate, per second (1 → 0 in 0.2s). */
   29| const RECOIL_RATE = 5;
   30| 
   31| /** The bolt's radius at `t` along it (0 the tail's point, 1 the nose), as a fraction of its widest. */
   32| export function boltProfile(t: number): number {
   33|   return Math.sin(Math.PI * t ** 1.6) ** 0.8;
   34| }
   35| 
   36| /** How far a shot fired at `speed` has gone after `t` seconds: fast off the chest, easing a touch. */
   37| export function shotTravel(speed: number, t: number): number {
   38|   return speed * (t - 0.08 * t * t);
   39| }
   40| 
   41| /** A shot's opacity factor at `t`: whole until the last FADE_S of its life. */
   42| export function shotFade(t: number, life: number = SHOT_LIFE_S): number {
   43|   return Math.max(0, Math.min(1, (life - t) / FADE_S));
   44| }
   45| 
   46| /** The recoil left after `dt` seconds from `kick` (0..1). */
   47| export function recoilAfter(kick: number, dt: number): number {
   48|   return Math.max(0, kick - dt * RECOIL_RATE);
   49| }
   50| 
   51| /** A streamlined bolt along +Y: a rounded nose tapering to a point at the tail. */
   52| function boltGeometry(radius: number, length: number): LatheGeometry {
   53|   const pts: Vector2[] = [];
   54|   for (let i = 0; i <= 24; i++) {
   55|     const t = i / 24;
   56|     pts.push(new Vector2(Math.max(radius * boltProfile(t), 1e-4), (t - 0.62) * length));
   57|   }
   58|   return new LatheGeometry(pts, 20);
   59| }
   60| 
   61| /**
   62|  * The muzzle flash's material: additive, in the shot's colour, and faded out
   63|  * through the half of the sphere farther from the camera (measured from its
   64|  * centre in view space), so where it sinks into the chest it dissolves
   65|  * instead of being cut by the robot's geometry.
   66|  */
   67| function flashMaterial(color: string, radius: number): ShaderMaterial {
   68|   return new ShaderMaterial({
   69|     uniforms: { uColor: { value: new Color(color) }, uOpacity: { value: 1 }, uRadius: { value: radius } },
   70|     vertexShader: `
   71|       uniform float uRadius;
   72|       varying float vDepth;
   73|       void main() {
   74|         vec4 mv = modelViewMatrix * vec4(position, 1.0);
   75|         vec4 centre = modelViewMatrix * vec4(0.0, 0.0, 0.0, 1.0);
   76|         float r = uRadius * length((modelViewMatrix * vec4(1.0, 0.0, 0.0, 0.0)).xyz);
   77|         vDepth = (mv.z - centre.z) / r;   // +1 nearest the camera, -1 farthest
   78|         gl_Position = projectionMatrix * mv;
   79|       }`,
   80|     fragmentShader: `
   81|       uniform vec3 uColor;
   82|       uniform float uOpacity;
   83|       varying float vDepth;
   84|       void main() {
   85|         gl_FragColor = vec4(uColor, uOpacity * smoothstep(-0.05, 0.6, vDepth));
   86|       }`,
   87|     transparent: true,
   88|     blending: AdditiveBlending,
   89|     depthWrite: false,
   90|     side: DoubleSide,
   91|   });
   92| }
   93| 
   94| const glowMaterial = (color: string, opacity: number) =>
   95|   new MeshBasicMaterial({ color, transparent: true, opacity, blending: AdditiveBlending, depthWrite: false });
   96| 
   97| interface Shot {
   98|   readonly shot: Group;
   99|   readonly parts: readonly { readonly mesh: Mesh<LatheGeometry, MeshBasicMaterial>; readonly opacity: number }[];
  100|   readonly flash: Mesh<IcosahedronGeometry, ShaderMaterial>;
  101|   readonly light: PointLight;
  102|   readonly origin: Vector3;
  103|   readonly dir: Vector3;
  104|   readonly speed: number;
  105|   t: number;
  106| }
  107| 
  108| export interface FireOptions {
  109|   /** World space. */
  110|   readonly origin: Vector3;
  111|   readonly direction: Vector3;
  112|   /** The robot's height in world units. */
  113|   readonly size: number;
  114|   /** #rrggbb. */
  115|   readonly color: string;
  116| }
  117| 
  118| export interface ChestBlast {
  119|   fire(options: FireOptions): void;
  120|   /** Advance every shot by dt seconds; whether any is still flying. */
  121|   update(dt: number): boolean;
  122|   /** The recoil (1 just after firing, easing to 0), for the robot to rock back by. */
  123|   recoil(): number;
  124|   dispose(): void;
  125| }
  126| 
  127| export function createChestBlast(scene: Scene): ChestBlast {
  128|   const group = new Group();
  129|   group.name = 'Chest blasts';
  130|   scene.add(group);
  131|   const up = new Vector3(0, 1, 0);
  132|   const shots: Shot[] = [];
  133|   let kick = 0;
  134| 
  135|   function remove(s: Shot): void {
  136|     group.remove(s.shot, s.flash, s.light);
  137|     for (const { mesh } of s.parts) {
  138|       mesh.geometry.dispose();
  139|       mesh.material.dispose();
  140|     }
  141|     s.flash.geometry.dispose();
  142|     s.flash.material.dispose();
  143|     s.light.dispose();
  144|   }
  145| 
  146|   return {
  147|     fire({ origin, direction, size, color }) {
  148|       const r = size * 0.03;
  149|       const dir = direction.clone().normalize();
  150|       const shot = new Group();
  151|       // The bolt and its sheath: one shape, the sheath wider and longer and fainter.
  152|       const parts = [
  153|         { mesh: new Mesh(boltGeometry(r * 1.3, r * 11), glowMaterial(color, 0.9)), opacity: 0.9 },
  154|         { mesh: new Mesh(boltGeometry(r * 2.2, r * 13), glowMaterial(color, 0.3)), opacity: 0.3 },
  155|       ];
  156|       for (const { mesh } of parts) shot.add(mesh);
  157|       shot.quaternion.setFromUnitVectors(up, dir);
  158|       shot.position.copy(origin);
  159|       const flash = new Mesh(new IcosahedronGeometry(r * 1.5, 2), flashMaterial(color, r * 1.5));
  160|       flash.position.copy(origin);
  161|       const light = new PointLight(color, 0, size * 1.2);
  162|       light.position.copy(origin);
  163|       group.add(shot, flash, light);
  164|       shots.push({ shot, parts, flash, light, origin: origin.clone(), dir, speed: size * 4.5, t: 0 });
  165|       kick = 1;
  166|     },
  167|     update(dt) {
  168|       kick = recoilAfter(kick, dt);
  169|       for (let i = shots.length - 1; i >= 0; i--) {
  170|         const s = shots[i];
  171|         if (!s) continue;
  172|         s.t += dt;
  173|         s.shot.position.copy(s.origin).addScaledVector(s.dir, shotTravel(s.speed, s.t));
  174|         // It leaves the chest compressed and stretches to full length.
  175|         s.shot.scale.set(1, 0.55 + 0.45 * Math.min(1, s.t / STRETCH_S), 1);
  176|         const fade = shotFade(s.t);
  177|         for (const { mesh, opacity } of s.parts) mesh.material.opacity = opacity * fade;
  178|         // The muzzle flash: a burst at the chest.
  179|         const f = Math.min(1, s.t / FLASH_S);
  180|         s.flash.visible = f < 1;
  181|         s.flash.scale.setScalar(1 + f * 1.6);
  182|         const uOpacity = s.flash.material.uniforms.uOpacity;
  183|         if (uOpacity) uOpacity.value = 1 - f;
  184|         s.light.intensity = 30 * Math.max(0, 1 - s.t / 0.3);
  185|         s.light.position.copy(s.shot.position);
  186|         if (s.t >= SHOT_LIFE_S) {
  187|           remove(s);
  188|           shots.splice(i, 1);
  189|         }
  190|       }
  191|       return shots.length > 0;
  192|     },
  193|     recoil: () => kick * kick,
  194|     dispose() {
  195|       for (const s of shots) remove(s);
  196|       shots.length = 0;
  197|       scene.remove(group);
  198|     },
  199|   };
  200| }
```

## `src/lib/robot/camera.test.ts`

```ts
    1| import { PerspectiveCamera, Vector3 } from 'three';
    2| import { describe, expect, test } from 'vitest';
    3| import {
    4|   BASE_SHOT,
    5|   biasFraming,
    6|   computeFraming,
    7|   createFloat,
    8|   mirroredAzimuth,
    9|   mirroredOffset,
   10|   orbitDirection,
   11|   stageRect,
   12|   viewOffset,
   13| } from './camera';
   14| import { ATLAS } from './characters';
   15| 
   16| const ASPECT = 200 / 260;
   17| 
   18| describe('mirroring', () => {
   19|   test('a mirrored stage swings the orbit the other way', () => {
   20|     expect(mirroredAzimuth(29.8, true)).toBe(-29.8);
   21|     expect(mirroredAzimuth(29.8, false)).toBe(29.8);
   22|   });
   23| 
   24|   test('a mirrored stage reflects only the camera offset’s x', () => {
   25|     expect(mirroredOffset([3.3, 1, -2], true)).toEqual([-3.3, 1, -2]);
   26|     expect(mirroredOffset([3.3, 1, -2], false)).toEqual([3.3, 1, -2]);
   27|   });
   28| 
   29|   test('the mirrored framing is the unmirrored one reflected in x', () => {
   30|     const plain = computeFraming(ATLAS, ASPECT, false);
   31|     const mirrored = computeFraming(ATLAS, ASPECT, true);
   32|     expect(mirrored.position.x - plain.position.x).toBeCloseTo(-2 * ATLAS.camOffset[0], 10);
   33|     expect(mirrored.target.x - plain.target.x).toBeCloseTo(-2 * ATLAS.camOffset[0], 10);
   34|     expect(mirrored.position.y).toBeCloseTo(plain.position.y, 10);
   35|     expect(mirrored.shift).toEqual(plain.shift);
   36|   });
   37| 
   38|   test('a mirrored orbit is the plain orbit reflected in x', () => {
   39|     const withOrbit = { ...ATLAS, orbit: [30, 80] as const };
   40|     const plain = computeFraming(withOrbit, ASPECT, false);
   41|     const mirrored = computeFraming(withOrbit, ASPECT, true);
   42|     const plainDir = plain.position.clone().sub(plain.target);
   43|     const mirroredDir = mirrored.position.clone().sub(mirrored.target);
   44|     expect(mirroredDir.x).toBeCloseTo(-plainDir.x, 10);
   45|     expect(mirroredDir.y).toBeCloseTo(plainDir.y, 10);
   46|     expect(mirroredDir.z).toBeCloseTo(plainDir.z, 10);
   47|   });
   48| });
   49| 
   50| describe('orbitDirection', () => {
   51|   test('azimuth 0 at the horizon looks from the front (+Z)', () => {
   52|     const d = orbitDirection(0, 90);
   53|     expect(d.x).toBeCloseTo(0, 10);
   54|     expect(d.y).toBeCloseTo(0, 10);
   55|     expect(d.z).toBeCloseTo(1, 10);
   56|   });
   57| 
   58|   test('azimuth 90 looks from +X; polar 0 from overhead', () => {
   59|     expect(orbitDirection(90, 90).x).toBeCloseTo(1, 10);
   60|     expect(orbitDirection(45, 0).y).toBeCloseTo(1, 10);
   61|   });
   62| });
   63| 
   64| describe('biasFraming', () => {
   65|   test('an identity layout on a target on the axis keeps the shot and needs no lens shift', () => {
   66|     const position = new Vector3(8, 6, 15);
   67|     const target = new Vector3(0, 3, 0);
   68|     const f = biasFraming(position, target, { x: 0, y: 0, zoom: 1 }, 30, ASPECT);
   69|     expect(f.position.distanceTo(position)).toBeCloseTo(0, 10);
   70|     expect(f.target.distanceTo(target)).toBeCloseTo(0, 10);
   71|     expect(f.shift.x).toBeCloseTo(0, 10);
   72|     expect(f.shift.y).toBeCloseTo(0, 10);
   73|   });
   74| 
   75|   test('zoom backs the camera off along its line', () => {
   76|     const position = new Vector3(8, 6, 15);
   77|     const target = new Vector3(0, 3, 0);
   78|     const f = biasFraming(position, target, { x: 0, y: 0, zoom: 2 }, 30, ASPECT);
   79|     expect(f.position.distanceTo(f.target)).toBeCloseTo(2 * position.distanceTo(target), 8);
   80|   });
   81| 
   82|   test('the target always lands on the character’s vertical axis', () => {
   83|     const f = biasFraming(new Vector3(...BASE_SHOT.position), new Vector3(...BASE_SHOT.target), { x: 0.1, y: 0.2, zoom: 1 }, 30, ASPECT);
   84|     expect(f.target.x).toBe(0);
   85|     expect(f.target.z).toBe(0);
   86|   });
   87| 
   88|   test('the lens shift lands the axis point where the unpivoted shot had it', () => {
   89|     const position = new Vector3(...BASE_SHOT.position);
   90|     const target = new Vector3(...BASE_SHOT.target);
   91|     const f = biasFraming(position, target, { x: 0, y: 0, zoom: 1 }, 30, ASPECT);
   92|     // The shot as authored: from `position`, looking at `target` (off the axis).
   93|     const authored = new PerspectiveCamera(30, ASPECT, 0.1, 400);
   94|     authored.position.copy(position);
   95|     authored.lookAt(target);
   96|     authored.updateMatrixWorld();
   97|     const p = f.target.clone().project(authored);
   98|     expect(f.shift.x).not.toBe(0);
   99|     expect(f.shift.x).toBeCloseTo(p.x, 6);
  100|     expect(f.shift.y).toBeCloseTo(p.y, 6);
  101|   });
  102| });
  103| 
  104| describe('stage box and lens', () => {
  105|   const stage = { right: 300, bottom: 40, width: 200, height: 260, mirror: true, yaw: 40 };
  106| 
  107|   test('stageRect measures from the canvas’s bottom-right', () => {
  108|     expect(stageRect(stage, 1200, 900)).toEqual({ left: 700, top: 600, width: 200, height: 260 });
  109|   });
  110| 
  111|   test('viewOffset makes the stage the full view inside the canvas', () => {
  112|     const box = stageRect(stage, 1200, 900);
  113|     expect(viewOffset(box, { x: 0, y: 0 }, 1200, 900)).toEqual([200, 260, -700, -600, 1200, 900]);
  114|     expect(viewOffset(box, { x: 0.5, y: -0.5 }, 1200, 900)).toEqual([200, 260, -750, -665, 1200, 900]);
  115|   });
  116| });
  117| 
  118| describe('createFloat', () => {
  119|   test('restores the camera exactly after the float', () => {
  120|     const camera = new PerspectiveCamera(30, ASPECT, 0.1, 400);
  121|     const target = new Vector3(0, 3, 0);
  122|     camera.position.set(5, 6, 14);
  123|     camera.lookAt(target);
  124|     const before = camera.position.clone();
  125|     const float = createFloat(() => 0.25);
  126|     float.apply(camera, target, 12.5);
  127|     expect(camera.position.distanceTo(before)).toBeGreaterThan(0);
  128|     float.restore(camera, target);
  129|     expect(camera.position.distanceTo(before)).toBe(0);
  130|   });
  131| 
  132|   test('the float stays a small swing about the target', () => {
  133|     const camera = new PerspectiveCamera(30, ASPECT, 0.1, 400);
  134|     const target = new Vector3(0, 3, 0);
  135|     camera.position.set(5, 6, 14);
  136|     const distance = camera.position.distanceTo(target);
  137|     const float = createFloat(() => 0.5);
  138|     for (const t of [0, 10, 100, 1000]) {
  139|       float.apply(camera, target, t);
  140|       expect(Math.abs(camera.position.distanceTo(target) / distance - 1)).toBeLessThan(0.005);
  141|       float.restore(camera, target);
  142|     }
  143|   });
  144| });
```

## `src/lib/robot/camera.ts`

```ts
    1| // The robot's camera: where it stands for the framed shot, the lens shift that
    2| // puts the robot in its stage box, and the slow float that keeps the shot alive.
    3| import { MathUtils, type PerspectiveCamera, Vector3 } from 'three';
    4| import type { Character } from './characters';
    5| import type { RobotStage } from './messages';
    6| 
    7| /** Where the robot sits in its box: pushed right / down by a fraction of the view, and a distance multiplier. */
    8| export interface Layout {
    9|   readonly x: number;
   10|   readonly y: number;
   11|   readonly zoom: number;
   12| }
   13| 
   14| /** The small framed robot's layout, before the character's own zoom. */
   15| export const DOCK_LAYOUT: Layout = { x: 0, y: 0.04, zoom: 0.6 };
   16| 
   17| /** The hand-set shot the idle and walk are framed from (world units; the model is 6.5 tall). */
   18| export const BASE_SHOT = {
   19|   position: [8.7, 5.8, 15.8],
   20|   target: [-0.35, 3.05, 0],
   21| } as const;
   22| 
   23| export interface LensShift {
   24|   x: number;
   25|   y: number;
   26| }
   27| 
   28| export interface Framing {
   29|   readonly position: Vector3;
   30|   readonly target: Vector3;
   31|   /** Lens shift as a fraction of the half-viewport (NDC). */
   32|   readonly shift: LensShift;
   33| }
   34| 
   35| export interface Box {
   36|   readonly left: number;
   37|   readonly top: number;
   38|   readonly width: number;
   39|   readonly height: number;
   40| }
   41| 
   42| const UP = new Vector3(0, 1, 0);
   43| 
   44| /** Azimuth reflected with the stage: a mirrored shot swings the other way. */
   45| export function mirroredAzimuth(azimuth: number, mirrored: boolean): number {
   46|   return mirrored ? -azimuth : azimuth;
   47| }
   48| 
   49| /** A world-space camera offset reflected with the stage (x only). */
   50| export function mirroredOffset(offset: readonly [number, number, number], mirrored: boolean): [number, number, number] {
   51|   const [x, y, z] = offset;
   52|   return [mirrored ? -x : x, y, z];
   53| }
   54| 
   55| /** Unit vector from the target to the camera: azimuth about world up from +Z, polar down from overhead (degrees). */
   56| export function orbitDirection(azimuth: number, polar: number): Vector3 {
   57|   const az = MathUtils.degToRad(azimuth);
   58|   const pol = MathUtils.degToRad(polar);
   59|   return new Vector3(Math.sin(pol) * Math.sin(az), Math.cos(pol), Math.sin(pol) * Math.cos(az));
   60| }
   61| 
   62| /**
   63|  * Orbit about the character's own vertical axis (x = 0, z = 0): the camera
   64|  * slides, same direction and depth, until it looks straight at the axis, and
   65|  * the lens shift moves the image back so that point lands where the framing had it.
   66|  */
   67| export function pivotOnAxis(
   68|   position: Vector3,
   69|   direction: Vector3,
   70|   right: Vector3,
   71|   up: Vector3,
   72|   height: number,
   73|   fov: number,
   74|   aspect: number,
   75| ): Framing {
   76|   const pivot = new Vector3(0, height, 0);
   77|   const v = pivot.clone().sub(position);
   78|   const depth = Math.max(1, -v.dot(direction));
   79|   const tangent = Math.tan(MathUtils.degToRad(fov / 2));
   80|   const shift = { x: v.dot(right) / (depth * tangent * aspect), y: v.dot(up) / (depth * tangent) };
   81|   return { position: pivot.clone().addScaledVector(direction, depth), target: pivot, shift };
   82| }
   83| 
   84| /**
   85|  * Push a shot to where the layout wants the model: the target slides along the
   86|  * camera's right / up by a fraction of the view, and the camera backs off by
   87|  * the layout zoom. { x: 0, y: 0, zoom: 1 } leaves the shot as it was.
   88|  */
   89| export function biasFraming(position: Vector3, target: Vector3, layout: Layout, fov: number, aspect: number): Framing {
   90|   const direction = position.clone().sub(target).normalize();
   91|   const distance = position.distanceTo(target) * layout.zoom;
   92|   const right = new Vector3().crossVectors(UP, direction).normalize();
   93|   const up = new Vector3().crossVectors(direction, right).normalize();
   94|   const tangent = Math.tan(MathUtils.degToRad(fov / 2));
   95|   const biased = target
   96|     .clone()
   97|     .addScaledVector(right, -2 * distance * tangent * aspect * layout.x)
   98|     .addScaledVector(up, 2 * distance * tangent * layout.y);
   99|   return pivotOnAxis(biased.clone().addScaledVector(direction, distance), direction, right, up, target.y, fov, aspect);
  100| }
  101| 
  102| /** The character's framed shot for a stage of the given aspect, mirrored or not. */
  103| export function computeFraming(character: Character, aspect: number, mirrored: boolean): Framing {
  104|   const layout = { ...DOCK_LAYOUT, zoom: DOCK_LAYOUT.zoom * character.zoom };
  105|   const base = biasFraming(
  106|     new Vector3(...BASE_SHOT.position),
  107|     new Vector3(...BASE_SHOT.target),
  108|     layout,
  109|     character.fov,
  110|     aspect,
  111|   );
  112|   let position = base.position;
  113|   if (character.orbit) {
  114|     const [azimuth, polar] = character.orbit;
  115|     const depth = base.position.distanceTo(base.target);
  116|     position = base.target.clone().addScaledVector(orbitDirection(mirroredAzimuth(azimuth, mirrored), polar), depth);
  117|   }
  118|   const [x, y, z] = mirroredOffset(character.camOffset, mirrored);
  119|   const offset = new Vector3(x, y, z);
  120|   return { position: position.clone().add(offset), target: base.target.clone().add(offset), shift: base.shift };
  121| }
  122| 
  123| /** The stage's rect in canvas px: `right` / `bottom` measured from the canvas's bottom-right corner. */
  124| export function stageRect(stage: RobotStage, canvasWidth: number, canvasHeight: number): Box {
  125|   return {
  126|     left: canvasWidth - stage.right - stage.width,
  127|     top: canvasHeight - stage.bottom - stage.height,
  128|     width: stage.width,
  129|     height: stage.height,
  130|   };
  131| }
  132| 
  133| /**
  134|  * setViewOffset arguments that make the stage box the camera's full view and
  135|  * render the whole canvas around it, with the lens shift applied.
  136|  */
  137| export function viewOffset(
  138|   box: Box,
  139|   shift: LensShift,
  140|   canvasWidth: number,
  141|   canvasHeight: number,
  142| ): [number, number, number, number, number, number] {
  143|   return [
  144|     box.width,
  145|     box.height,
  146|     -box.left - (shift.x * box.width) / 2,
  147|     -box.top + (shift.y * box.height) / 2,
  148|     canvasWidth,
  149|     canvasHeight,
  150|   ];
  151| }
  152| 
  153| // The idle float: each axis sums sines with incommensurable periods, so the
  154| // drift never visibly loops. Amplitudes are angles (radians) and a dolly fraction.
  155| const FLOAT = {
  156|   azimuth: [
  157|     { amplitude: 0.013, rate: 0.11 },
  158|     { amplitude: 0.0062, rate: 0.191 },
  159|   ],
  160|   polar: [
  161|     { amplitude: 0.0068, rate: 0.083 },
  162|     { amplitude: 0.0031, rate: 0.149 },
  163|   ],
  164|   dolly: [{ amplitude: 0.0042, rate: 0.067 }],
  165| } as const;
  166| 
  167| type Wave = readonly { readonly amplitude: number; readonly rate: number }[];
  168| 
  169| function waveAt(terms: Wave, phases: readonly number[], time: number): number {
  170|   return terms.reduce((total, term, i) => total + term.amplitude * Math.sin(time * term.rate + (phases[i] ?? 0)), 0);
  171| }
  172| 
  173| /**
  174|  * The float, layered on the camera for one render and taken off after, so it
  175|  * never feeds back into the framing. Phases are random per mount, so two tabs
  176|  * never drift in lockstep.
  177|  */
  178| export function createFloat(random: () => number = Math.random) {
  179|   const phases = (terms: Wave) => terms.map(() => random() * Math.PI * 2);
  180|   const phase = { azimuth: phases(FLOAT.azimuth), polar: phases(FLOAT.polar), dolly: phases(FLOAT.dolly) };
  181|   const basePosition = new Vector3();
  182|   const offset = new Vector3();
  183|   const right = new Vector3();
  184|   return {
  185|     /** Swing the camera about `target` for this frame's render. */
  186|     apply(camera: PerspectiveCamera, target: Vector3, time: number): void {
  187|       basePosition.copy(camera.position);
  188|       offset.subVectors(camera.position, target);
  189|       offset.applyAxisAngle(UP, waveAt(FLOAT.azimuth, phase.azimuth, time));
  190|       right.crossVectors(offset, UP).normalize();
  191|       offset.applyAxisAngle(right, waveAt(FLOAT.polar, phase.polar, time));
  192|       offset.multiplyScalar(1 + waveAt(FLOAT.dolly, phase.dolly, time));
  193|       camera.position.addVectors(target, offset);
  194|       camera.lookAt(target);
  195|       camera.updateMatrixWorld();
  196|     },
  197|     /** Put the camera back where the framing has it. */
  198|     restore(camera: PerspectiveCamera, target: Vector3): void {
  199|       camera.position.copy(basePosition);
  200|       camera.lookAt(target);
  201|     },
  202|   };
  203| }
```

## `src/lib/robot/characters.ts`

```ts
    1| // The narrator: ChatPro (character atlas-09) in its Americana model. The values
    2| // are the ones the original harness used for the small framed robot, baked in.
    3| // Paths are relative to ASSET_BASE (assets.ts).
    4| 
    5| export type Paint = 'history' | 'rerun';
    6| 
    7| /** Flat lighting values over the scene. Colours are CSS hex strings. */
    8| export interface Lighting {
    9|   readonly exposure: number;
   10|   readonly environment: number;
   11|   readonly hemi: number;
   12|   readonly hemiSky: string;
   13|   readonly hemiGround: string;
   14|   readonly key: number;
   15|   readonly keyColor: string;
   16|   readonly rim: number;
   17|   readonly rimColor: string;
   18|   readonly fill: number;
   19|   readonly fillColor: string;
   20| }
   21| 
   22| /** A bone that plays the idle on its own clock: multipliers on the idle's intensity and speed. */
   23| export interface IdleBone {
   24|   readonly intensity: number;
   25|   readonly speed: number;
   26| }
   27| 
   28| export interface Character {
   29|   readonly id: string;
   30|   /** The Americana GLB: rig, clips and the History paint. */
   31|   readonly model: string;
   32|   /** The Rerun paint: textures on the model's UVs plus overrides.json. */
   33|   readonly rerunPaint: { readonly dir: string; readonly version: number };
   34|   /** Lighting per paint. History is the original harness look; Rerun was tuned by eye. */
   35|   readonly lighting: Readonly<Record<Paint, Lighting>>;
   36|   /** Every model is scaled to this height (scene units) and stood on the origin. */
   37|   readonly height: number;
   38|   /** Multiplier on the layout's camera distance. */
   39|   readonly zoom: number;
   40|   /** Vertical field of view, degrees. */
   41|   readonly fov: number;
   42|   /** Camera moved this far in world space, target with it (a truck, not a swing). Mirrored in x with the stage. */
   43|   readonly camOffset: readonly [number, number, number];
   44|   /** [azimuth, polar] degrees to swing the camera round to, or null to keep the fitted direction. */
   45|   readonly orbit: readonly [number, number] | null;
   46|   readonly idleClip: string;
   47|   readonly walkClip: string;
   48|   /** How much of the idle's motion plays (1 = as authored). */
   49|   readonly idleIntensity: number;
   50|   /** How fast the idle plays (1 = as authored). */
   51|   readonly idleSpeed: number;
   52|   readonly idleBones: Readonly<Record<string, IdleBone>>;
   53|   /** The chest reactor's point light, before the power factor. */
   54|   readonly reactorLight: number;
   55| }
   56| 
   57| const ORIGINAL_LOOK = {
   58|   hemiSky: '#dfe6de',
   59|   hemiGround: '#303926',
   60|   keyColor: '#fff2d9',
   61|   rimColor: '#a3cad2',
   62|   fillColor: '#d7e1b8',
   63| } as const;
   64| 
   65| export const ATLAS: Character = {
   66|   id: 'atlas-09',
   67|   model: 'models/atlas-09-americana.glb?v=4',
   68|   rerunPaint: { dir: 'models/atlas-09-americana-rerun/', version: 2 },
   69|   lighting: {
   70|     history: { ...ORIGINAL_LOOK, exposure: 1.18, environment: 0.45, hemi: 1.3, key: 4.5, rim: 3.2, fill: 0.8 },
   71|     rerun: { ...ORIGINAL_LOOK, exposure: 0.75, environment: 0.4, hemi: 1, key: 1.2, rim: 3.6, fill: 3.55 },
   72|   },
   73|   height: 6.5,
   74|   zoom: 1.71,
   75|   fov: 29.5,
   76|   camOffset: [3.3, 0, 0],
   77|   orbit: null,
   78|   idleClip: 'Sentinel',
   79|   walkClip: 'Walk',
   80|   idleIntensity: 8.4,
   81|   idleSpeed: 2.1,
   82|   // The head at a third of the body's travel and pace.
   83|   idleBones: { head: { intensity: 1 / 3, speed: 1 / 3 } },
   84|   reactorLight: 3,
   85| };
```

## `src/lib/robot/lighting.ts`

```ts
    1| // The robot's lights: the room environment, a hemisphere fill and three
    2| // directional lights whose values switch with the paint, plus the chest
    3| // reactor's point light.
    4| import {
    5|   DirectionalLight,
    6|   HemisphereLight,
    7|   PMREMGenerator,
    8|   PointLight,
    9|   type Scene,
   10|   type Texture,
   11|   type WebGLRenderer,
   12| } from 'three';
   13| import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
   14| import type { Lighting } from './characters';
   15| 
   16| /** The reactor's output, 0–1 (the original harness's slider default). */
   17| export const REACTOR_POWER = 0.84;
   18| 
   19| export interface Rig {
   20|   /** Set every light, the environment and the exposure from one paint's values. */
   21|   apply(values: Lighting): void;
   22|   dispose(): void;
   23| }
   24| 
   25| export function createLighting(renderer: WebGLRenderer, scene: Scene, reactorLight: number): Rig {
   26|   const pmrem = new PMREMGenerator(renderer);
   27|   const room = new RoomEnvironment();
   28|   const environment: Texture = pmrem.fromScene(room, 0.025).texture;
   29|   room.dispose();
   30|   pmrem.dispose();
   31|   scene.environment = environment;
   32| 
   33|   const hemisphere = new HemisphereLight('#ffffff', '#000000', 1);
   34|   const key = new DirectionalLight('#ffffff', 1);
   35|   key.position.set(-5, 10, 6);
   36|   key.castShadow = true;
   37|   key.shadow.mapSize.set(2048, 2048);
   38|   Object.assign(key.shadow.camera, { left: -7, right: 7, top: 10, bottom: -6, near: 0.1, far: 35 });
   39|   key.shadow.normalBias = 0.03;
   40|   key.shadow.bias = -0.0002;
   41|   const rim = new DirectionalLight('#ffffff', 1);
   42|   rim.position.set(5, 7, -4);
   43|   const fill = new DirectionalLight('#ffffff', 1);
   44|   fill.position.set(4, 3, 5);
   45|   // The chest reactor's glow on the armour around it.
   46|   const reactor = new PointLight('#63f4ff', REACTOR_POWER * reactorLight, 3, 2);
   47|   reactor.position.set(0, 4.35, 0.8);
   48|   scene.add(hemisphere, key, rim, fill, reactor);
   49| 
   50|   return {
   51|     apply(v) {
   52|       renderer.toneMappingExposure = v.exposure;
   53|       scene.environmentIntensity = v.environment;
   54|       hemisphere.intensity = v.hemi;
   55|       hemisphere.color.set(v.hemiSky);
   56|       hemisphere.groundColor.set(v.hemiGround);
   57|       key.intensity = v.key;
   58|       key.color.set(v.keyColor);
   59|       rim.intensity = v.rim;
   60|       rim.color.set(v.rimColor);
   61|       fill.intensity = v.fill;
   62|       fill.color.set(v.fillColor);
   63|     },
   64|     dispose() {
   65|       key.shadow.dispose();
   66|       environment.dispose();
   67|       scene.remove(hemisphere, key, rim, fill, reactor);
   68|     },
   69|   };
   70| }
```

## `src/lib/robot/messages.test.ts`

```ts
    1| import { describe, expect, test } from 'vitest';
    2| import { parseFrameMessage, parseHostMessage } from './messages';
    3| 
    4| const stage = { right: 312, bottom: 40, width: 200, height: 260, mirror: true, yaw: 37.4 };
    5| 
    6| describe('page → frame', () => {
    7|   test.each([
    8|     { type: 'robot:stage', stage },
    9|     { type: 'robot:stage', stage: null },
   10|     { type: 'robot:running', on: true },
   11|     { type: 'robot:running', on: false },
   12|     { type: 'robot:walk', on: true },
   13|     { type: 'robot:paint', paint: 'history' },
   14|     { type: 'robot:paint', paint: 'rerun' },
   15|     { type: 'robot:blast', color: '#ff3344' },
   16|     { type: 'robot:blast', color: '#FFFFFF' },
   17|   ])('parses $type', (message) => {
   18|     expect(parseHostMessage(message)).toEqual(message);
   19|   });
   20| 
   21|   test('the parsed stage keeps every field', () => {
   22|     const parsed = parseHostMessage({ type: 'robot:stage', stage });
   23|     expect(parsed?.type === 'robot:stage' ? parsed.stage : null).toEqual(stage);
   24|   });
   25| 
   26|   test.each([
   27|     ['an unknown paint', { type: 'robot:paint', paint: 'americana' }],
   28|     ['a missing paint', { type: 'robot:paint' }],
   29|     ['a string for a flag', { type: 'robot:walk', on: 'true' }],
   30|     ['a stage missing its yaw', { type: 'robot:stage', stage: { ...stage, yaw: undefined } }],
   31|     ['a stage with zero width', { type: 'robot:stage', stage: { ...stage, width: 0 } }],
   32|     ['a stage with an infinite edge', { type: 'robot:stage', stage: { ...stage, right: Number.POSITIVE_INFINITY } }],
   33|     ['a stage with NaN', { type: 'robot:stage', stage: { ...stage, bottom: Number.NaN } }],
   34|     ['a blast without a colour', { type: 'robot:blast' }],
   35|     ['a blast in a named colour', { type: 'robot:blast', color: 'red' }],
   36|     ['a blast in shorthand hex', { type: 'robot:blast', color: '#f34' }],
   37|     ['a blast in rgb()', { type: 'robot:blast', color: 'rgb(255, 51, 68)' }],
   38|     ['a blast with a colour and more', { type: 'robot:blast', color: '#ff3344; background: url(x)' }],
   39|     ['the old overlay blast', { type: 'mecha-overlay:blast', color: '#ff3344' }],
   40|     ['the old overlay protocol', { type: 'mecha-overlay:paint', paint: 'rerun' }],
   41|     ['a frame-bound message', { type: 'robot:ready' }],
   42|     ['a devtools message', { source: 'react-devtools-bridge', payload: {} }],
   43|     ['a bare string', 'robot:walk'],
   44|     ['null', null],
   45|     ['undefined', undefined],
   46|     ['a number', 7],
   47|   ])('rejects %s', (_label, message) => {
   48|     expect(parseHostMessage(message)).toBeNull();
   49|   });
   50| });
   51| 
   52| describe('frame → page', () => {
   53|   test.each([
   54|     { type: 'robot:ready' },
   55|     { type: 'robot:anchors', anchors: { centerX: 412.5, feetY: 618 } },
   56|     { type: 'robot:anchors', anchors: null },
   57|   ])('parses $type', (message) => {
   58|     expect(parseFrameMessage(message)).toEqual(message);
   59|   });
   60| 
   61|   test.each([
   62|     ['anchors without feet', { type: 'robot:anchors', anchors: { centerX: 1 } }],
   63|     ['anchors with a string', { type: 'robot:anchors', anchors: { centerX: '1', feetY: 2 } }],
   64|     ['anchors left out', { type: 'robot:anchors' }],
   65|     ['the old ready', { type: 'mecha-overlay:ready' }],
   66|     ['a page-bound message', { type: 'robot:walk', on: true }],
   67|     ['an array', [{ type: 'robot:ready' }]],
   68|     ['null', null],
   69|   ])('rejects %s', (_label, message) => {
   70|     expect(parseFrameMessage(message)).toBeNull();
   71|   });
   72| });
```

## `src/lib/robot/messages.ts`

```ts
    1| // Every postMessage between the page (RobotFrame) and the robot's frame
    2| // (/robot). Both ends are same-origin and check `event.source` before parsing;
    3| // anything that doesn't parse is someone else's message and is ignored quietly.
    4| //
    5| // Page → frame
    6| //   robot:stage    { stage: RobotStage | null }  where the robot stands (null: the default box)
    7| //   robot:running  { on }                        draw (true) or stop the render loop (false)
    8| //   robot:walk     { on }                        walk (working) or idle
    9| //   robot:paint    { paint: 'history' | 'rerun' }
   10| //   robot:blast    { color }                     a shot from the chest reactor, in #rrggbb
   11| // Frame → page
   12| //   robot:ready                                  the frame is listening; send the state
   13| //   robot:anchors  { anchors: RobotAnchors | null }  every frame; null while the model loads
   14| import { z } from 'zod';
   15| 
   16| const finite = z.number();
   17| 
   18| /**
   19|  * The box the robot is framed into, in CSS px inside the frame: `right` and
   20|  * `bottom` from the frame's bottom-right corner. `mirror` reflects the robot
   21|  * (and the camera's sideways moves) left-right; `yaw` turns it about its
   22|  * vertical axis in degrees, eased toward in the renderer.
   23|  */
   24| export const RobotStageSchema = z.object({
   25|   right: finite,
   26|   bottom: finite,
   27|   width: finite.positive(),
   28|   height: finite.positive(),
   29|   mirror: z.boolean(),
   30|   yaw: finite,
   31| });
   32| export type RobotStage = z.infer<typeof RobotStageSchema>;
   33| 
   34| /** Where the robot stands on screen, CSS px: its body's centre line and the floor under its feet. */
   35| export const RobotAnchorsSchema = z.object({
   36|   centerX: finite,
   37|   feetY: finite,
   38| });
   39| export type RobotAnchors = z.infer<typeof RobotAnchorsSchema>;
   40| 
   41| export const PaintSchema = z.enum(['history', 'rerun']);
   42| 
   43| /** A CSS colour as #rrggbb. */
   44| export const HexColorSchema = z.string().regex(/^#[0-9a-f]{6}$/i);
   45| 
   46| export const HostMessageSchema = z.discriminatedUnion('type', [
   47|   z.object({ type: z.literal('robot:stage'), stage: RobotStageSchema.nullable() }),
   48|   z.object({ type: z.literal('robot:running'), on: z.boolean() }),
   49|   z.object({ type: z.literal('robot:walk'), on: z.boolean() }),
   50|   z.object({ type: z.literal('robot:paint'), paint: PaintSchema }),
   51|   z.object({ type: z.literal('robot:blast'), color: HexColorSchema }),
   52| ]);
   53| export type HostMessage = z.infer<typeof HostMessageSchema>;
   54| 
   55| export const FrameMessageSchema = z.discriminatedUnion('type', [
   56|   z.object({ type: z.literal('robot:ready') }),
   57|   z.object({ type: z.literal('robot:anchors'), anchors: RobotAnchorsSchema.nullable() }),
   58| ]);
   59| export type FrameMessage = z.infer<typeof FrameMessageSchema>;
   60| 
   61| /** A message for the frame, or null for anything else. */
   62| export function parseHostMessage(data: unknown): HostMessage | null {
   63|   const result = HostMessageSchema.safeParse(data);
   64|   return result.success ? result.data : null;
   65| }
   66| 
   67| /** A message from the frame, or null for anything else. */
   68| export function parseFrameMessage(data: unknown): FrameMessage | null {
   69|   const result = FrameMessageSchema.safeParse(data);
   70|   return result.success ? result.data : null;
   71| }
```

## `src/lib/robot/motion.ts`

```ts
    1| // The robot's motion: its idle, exaggerated and sped up for the small framed
    2| // robot (the head on a slower clock of its own), and a walk it crossfades into
    3| // while the page is working.
    4| import {
    5|   type AnimationAction,
    6|   type AnimationClip,
    7|   AnimationMixer,
    8|   Interpolant,
    9|   type KeyframeTrack,
   10|   LoopRepeat,
   11|   type Object3D,
   12|   PropertyBinding,
   13|   Quaternion,
   14|   Vector3,
   15| } from 'three';
   16| import type { Character, IdleBone } from './characters';
   17| 
   18| /** Seconds of crossfade between the idle and the walk. */
   19| export const WALK_FADE = 0.7;
   20| 
   21| export interface Motion {
   22|   /** Advance by dt seconds: the mixer, then the idle edits on top. */
   23|   update(dt: number): void;
   24|   /** Walk (true) or go back to the idle it walked out of (false). */
   25|   setWalking(on: boolean): void;
   26|   dispose(): void;
   27| }
   28| 
   29| // three assigns `createInterpolant` per track at runtime (glTF cubic splines
   30| // bring their own), and its type declarations leave it out.
   31| function interpolantOf(track: KeyframeTrack): Interpolant | null {
   32|   const factory: unknown = Reflect.get(track, 'createInterpolant');
   33|   if (typeof factory !== 'function') return null;
   34|   const made: unknown = factory.call(track);
   35|   return made instanceof Interpolant ? made : null;
   36| }
   37| 
   38| function sample(interpolant: Interpolant, t: number): ArrayLike<number> {
   39|   const values: ArrayLike<number> = interpolant.evaluate(t);
   40|   return values;
   41| }
   42| 
   43| interface IdleClock {
   44|   readonly spec: IdleBone;
   45|   t: number;
   46| }
   47| 
   48| interface BoneRef {
   49|   readonly bone: Object3D;
   50|   q: Quaternion | null;
   51|   qi: Interpolant | null;
   52|   p: Vector3 | null;
   53|   pi: Interpolant | null;
   54|   clock: IdleClock | null;
   55| }
   56| 
   57| export function createMotion(model: Object3D, clips: readonly AnimationClip[], character: Character): Motion {
   58|   const mixer = new AnimationMixer(model);
   59|   const actions = new Map<string, AnimationAction>();
   60|   for (const clip of clips) actions.set(clip.name, mixer.clipAction(clip));
   61| 
   62|   let active: AnimationAction | null = null;
   63|   let clipName = '';
   64|   // While walking: the idle it walked out of, so the idle edits fade out with
   65|   // that idle's weight instead of landing on the walk.
   66|   let heldIdle: AnimationAction | null = null;
   67|   let walking = false;
   68|   let walkedFrom: string | null = null;
   69| 
   70|   const idle = actions.get(character.idleClip);
   71|   if (idle) {
   72|     idle.setLoop(LoopRepeat, Number.POSITIVE_INFINITY);
   73|     idle.clampWhenFinished = false;
   74|     idle.reset().setEffectiveWeight(1).setEffectiveTimeScale(1).play();
   75|     active = idle;
   76|     clipName = character.idleClip;
   77|   }
   78| 
   79|   const idleTarget = (): AnimationAction | null => {
   80|     if (heldIdle) return heldIdle;
   81|     return active && active.loop === LoopRepeat ? active : null;
   82|   };
   83| 
   84|   // The idle edits work on bones AFTER the mixer, and the mixer skips writes
   85|   // for constant tracks, so an edit left in place would build on itself frame
   86|   // after frame. Every edited bone goes back to the mixer's pose first.
   87|   const saved = new Map<Object3D, { q: Quaternion; p: Vector3 }>();
   88|   const keep = (bone: Object3D) => {
   89|     if (!saved.has(bone)) saved.set(bone, { q: bone.quaternion.clone(), p: bone.position.clone() });
   90|   };
   91|   const restore = () => {
   92|     for (const [bone, v] of saved) {
   93|       bone.quaternion.copy(v.q);
   94|       bone.position.copy(v.p);
   95|     }
   96|     saved.clear();
   97|   };
   98| 
   99|   // Idle speed: the idle plays this much faster than authored.
  100|   function applyIdleSpeed(): void {
  101|     const target = idleTarget();
  102|     if (target && target.getEffectiveTimeScale() !== character.idleSpeed) target.setEffectiveTimeScale(character.idleSpeed);
  103|   }
  104| 
  105|   // Idle intensity: each animated bone's travel away from the idle's first
  106|   // keyframe, scaled. Read off the clip's tracks (not the live bones), so it
  107|   // stays right through a crossfade, and weighted by the idle's weight.
  108|   let refAction: AnimationAction | null = null;
  109|   let refs: BoneRef[] = [];
  110|   let clocks: IdleClock[] = [];
  111|   function captureRefs(target: AnimationAction | null): void {
  112|     refAction = target;
  113|     refs = [];
  114|     clocks = [];
  115|     if (!target) return;
  116|     const byBone = new Map<Object3D, BoneRef>();
  117|     const byName = new Map<string, IdleClock>();
  118|     for (const track of target.getClip().tracks) {
  119|       const { nodeName, propertyName } = PropertyBinding.parseTrackName(track.name);
  120|       if (propertyName !== 'quaternion' && propertyName !== 'position') continue;
  121|       const bone = model.getObjectByName(nodeName);
  122|       if (!bone) continue;
  123|       const ref = byBone.get(bone) ?? { bone, q: null, qi: null, p: null, pi: null, clock: null };
  124|       if (propertyName === 'quaternion') {
  125|         ref.q = new Quaternion().fromArray(track.values, 0);
  126|         ref.qi = interpolantOf(track);
  127|       } else {
  128|         ref.p = new Vector3().fromArray(track.values, 0);
  129|         ref.pi = interpolantOf(track);
  130|       }
  131|       const spec = character.idleBones[bone.name];
  132|       if (spec) {
  133|         let clock = byName.get(bone.name);
  134|         if (!clock) {
  135|           clock = { spec, t: target.time };
  136|           byName.set(bone.name, clock);
  137|         }
  138|         ref.clock = clock;
  139|       }
  140|       byBone.set(bone, ref);
  141|     }
  142|     refs = [...byBone.values()];
  143|     clocks = [...byName.values()];
  144|   }
  145| 
  146|   const sampleQ = new Quaternion();
  147|   const atIdleQ = new Quaternion();
  148|   const deltaQ = new Quaternion();
  149|   const stepQ = new Quaternion();
  150|   const sampleP = new Vector3();
  151|   const stepP = new Vector3();
  152|   function applyIdleIntensity(dt: number): void {
  153|     const target = idleTarget();
  154|     if (target !== refAction) captureRefs(target);
  155|     if (!target) return;
  156|     const w = target.getEffectiveWeight();
  157|     if (w <= 0) return;
  158|     const k = character.idleIntensity;
  159|     const duration = target.getClip().duration || 0;
  160|     if (duration > 0) {
  161|       for (const c of clocks) c.t = (c.t + dt * target.getEffectiveTimeScale() * c.spec.speed) % duration;
  162|     }
  163|     for (const r of refs) {
  164|       const clock = duration > 0 ? r.clock : null;
  165|       const e = ((clock ? k * clock.spec.intensity : k) - 1) * w;
  166|       if (!clock && e === 0) continue;
  167|       const t = clock ? clock.t : target.time;
  168|       keep(r.bone);
  169|       if (r.qi && r.q) {
  170|         sampleQ.fromArray(sample(r.qi, t));
  171|         if (clock) {
  172|           // The bone on its own clock: the step from the idle's time to its clock's.
  173|           atIdleQ.fromArray(sample(r.qi, target.time));
  174|           r.bone.quaternion.multiply(stepQ.identity().slerp(deltaQ.copy(atIdleQ).invert().multiply(sampleQ), w));
  175|         }
  176|         if (e) r.bone.quaternion.multiply(stepQ.identity().slerp(deltaQ.copy(r.q).invert().multiply(sampleQ), e));
  177|       }
  178|       if (r.pi && r.p) {
  179|         sampleP.fromArray(sample(r.pi, t));
  180|         if (clock) r.bone.position.addScaledVector(stepP.fromArray(sample(r.pi, target.time)).negate().add(sampleP), w);
  181|         if (e) r.bone.position.addScaledVector(stepP.copy(sampleP).sub(r.p), e);
  182|       }
  183|     }
  184|   }
  185| 
  186|   // A crossfade that can reverse halfway: each side fades from the weight it
  187|   // has now, and a clip still fading out is picked back up where it is.
  188|   function blendTo(name: string, fade: number): boolean {
  189|     const next = actions.get(name);
  190|     if (!next || !active || next === active) return false;
  191|     const prev = active;
  192|     const live = next.enabled && next.isRunning() && next.getEffectiveWeight() > 0;
  193|     const from = live ? next.getEffectiveWeight() : 0;
  194|     const out = prev.getEffectiveWeight();
  195|     if (!live) next.reset();
  196|     next.setLoop(LoopRepeat, Number.POSITIVE_INFINITY);
  197|     next.clampWhenFinished = false;
  198|     next.setEffectiveTimeScale(1).setEffectiveWeight(1).play();
  199|     next._scheduleFading(Math.max(0.05, fade * (1 - from)), from, 1);
  200|     prev.stopFading();
  201|     prev._scheduleFading(Math.max(0.05, fade * out), out, 0);
  202|     active = next;
  203|     clipName = name;
  204|     heldIdle = null;
  205|     return true;
  206|   }
  207| 
  208|   return {
  209|     update(dt) {
  210|       restore();
  211|       applyIdleSpeed();
  212|       mixer.update(dt);
  213|       applyIdleIntensity(dt);
  214|     },
  215|     setWalking(on) {
  216|       const walkName = character.walkClip;
  217|       if (!actions.has(walkName) || on === walking) return;
  218|       if (on) {
  219|         const from = active;
  220|         if (!from || from.loop !== LoopRepeat || clipName === walkName) return;
  221|         walkedFrom = clipName;
  222|         if (!blendTo(walkName, WALK_FADE)) return;
  223|         heldIdle = from;
  224|         walking = true;
  225|         return;
  226|       }
  227|       walking = false;
  228|       if (clipName === walkName && walkedFrom) blendTo(walkedFrom, WALK_FADE);
  229|       walkedFrom = null;
  230|     },
  231|     dispose() {
  232|       restore();
  233|       mixer.stopAllAction();
  234|       mixer.uncacheRoot(model);
  235|       actions.clear();
  236|     },
  237|   };
  238| }
```

## `src/lib/robot/paint.test.ts`

```ts
    1| import { describe, expect, test } from 'vitest';
    2| import { normalizeAssetBase, DEFAULT_ASSET_BASE } from './assets';
    3| import { overrideFor, parseOverrides, partOf } from './paint';
    4| 
    5| // The shape of the Rerun paint's overrides.json as published.
    6| const published = {
    7|   Armor: { roughnessFactor: 1, metallicFactor: 1, emissiveFactor: [1, 1, 1] },
    8|   'Joint housings — navy': { baseColor: [0.0704, 0.0561, 0.0331], roughness: 0.917, metal: 0.12 },
    9|   'Actuator collars — navy': { baseColor: [0.18, 0.14, 0.065], roughness: 0.5, metal: 0.8 },
   10| };
   11| 
   12| describe('parseOverrides', () => {
   13|   test('reads glTF factor names and short names alike', () => {
   14|     const o = parseOverrides(published);
   15|     expect(o.Armor).toEqual({ color: undefined, emissive: [1, 1, 1], roughness: 1, metalness: 1 });
   16|     expect(o['Joint housings — navy']).toEqual({
   17|       color: [0.0704, 0.0561, 0.0331],
   18|       emissive: undefined,
   19|       roughness: 0.917,
   20|       metalness: 0.12,
   21|     });
   22|   });
   23| 
   24|   test('takes an RGBA factor', () => {
   25|     expect(parseOverrides({ Visor: { baseColorFactor: [0.1, 0.2, 0.3, 1] } }).Visor?.color).toEqual([0.1, 0.2, 0.3, 1]);
   26|   });
   27| 
   28|   test('malformed or missing overrides mean none', () => {
   29|     expect(parseOverrides({ Armor: { baseColor: [1, 1] } })).toEqual({});
   30|     expect(parseOverrides({ Armor: { roughness: 'high' } })).toEqual({});
   31|     expect(parseOverrides(null)).toEqual({});
   32|     expect(parseOverrides('{}')).toEqual({});
   33|   });
   34| });
   35| 
   36| describe('partOf / overrideFor', () => {
   37|   test('armour and joints materials by name', () => {
   38|     expect(partOf('Armor_Reactor_Emission')).toBe('armor');
   39|     expect(partOf('armor_reactor_emission.001')).toBe('armor');
   40|     expect(partOf('Weathered joints')).toBe('joints');
   41|     expect(partOf('Joint housings — navy')).toBeNull();
   42|   });
   43| 
   44|   test("armour without its own entry takes 'Armor'; others only their own", () => {
   45|     const o = parseOverrides(published);
   46|     expect(overrideFor(o, 'Armor_Reactor_Emission.001')?.metalness).toBe(1);
   47|     expect(overrideFor(o, 'Actuator collars — navy')?.metalness).toBe(0.8);
   48|     expect(overrideFor(o, 'Weathered joints')).toBeUndefined();
   49|   });
   50| });
   51| 
   52| describe('normalizeAssetBase', () => {
   53|   test('defaults when unset or blank', () => {
   54|     expect(normalizeAssetBase(undefined)).toBe(DEFAULT_ASSET_BASE);
   55|     expect(normalizeAssetBase('  ')).toBe(DEFAULT_ASSET_BASE);
   56|   });
   57| 
   58|   test('ends in exactly one slash', () => {
   59|     expect(normalizeAssetBase('https://cdn.example/robot')).toBe('https://cdn.example/robot/');
   60|     expect(normalizeAssetBase('https://cdn.example/robot/')).toBe('https://cdn.example/robot/');
   61|   });
   62| });
```

## `src/lib/robot/paint.ts`

```ts
    1| // The robot's two paints on one loaded model. History is the GLB's own; Rerun
    2| // is a folder of textures on the same UVs plus overrides.json. setPaint swaps
    3| // maps and factors on the loaded materials: no reload, rig and clip untouched.
    4| import {
    5|   type Color,
    6|   LinearSRGBColorSpace,
    7|   type Material,
    8|   MeshStandardMaterial,
    9|   NoColorSpace,
   10|   SRGBColorSpace,
   11|   type Texture,
   12|   TextureLoader,
   13| } from 'three';
   14| import { z } from 'zod';
   15| import { assetUrl } from './assets';
   16| import type { Character, Paint } from './characters';
   17| 
   18| const Vec3Schema = z.tuple([z.number(), z.number(), z.number()]).rest(z.number());
   19| 
   20| // One material's scalars, under glTF factor names or short ones.
   21| const OverrideSchema = z
   22|   .object({
   23|     baseColorFactor: Vec3Schema.optional(),
   24|     baseColor: Vec3Schema.optional(),
   25|     emissiveFactor: Vec3Schema.optional(),
   26|     emissive: Vec3Schema.optional(),
   27|     roughnessFactor: z.number().optional(),
   28|     roughness: z.number().optional(),
   29|     metallicFactor: z.number().optional(),
   30|     metalness: z.number().optional(),
   31|     metal: z.number().optional(),
   32|   })
   33|   .transform((o) => ({
   34|     color: o.baseColorFactor ?? o.baseColor,
   35|     emissive: o.emissiveFactor ?? o.emissive,
   36|     roughness: o.roughnessFactor ?? o.roughness,
   37|     metalness: o.metallicFactor ?? o.metalness ?? o.metal,
   38|   }));
   39| 
   40| /** overrides.json: material name (or 'Armor' for both armour materials) → scalars. */
   41| export const PaintOverridesSchema = z.record(z.string(), OverrideSchema);
   42| export type PaintOverrides = z.infer<typeof PaintOverridesSchema>;
   43| export type PaintOverride = PaintOverrides[string];
   44| 
   45| /** overrides.json parsed, or no overrides when it is missing or malformed. */
   46| export function parseOverrides(data: unknown): PaintOverrides {
   47|   const result = PaintOverridesSchema.safeParse(data);
   48|   return result.success ? result.data : {};
   49| }
   50| 
   51| const ARMOR = /^armor_reactor_emission/i;
   52| const JOINTS = /^weathered joints/i;
   53| 
   54| export type Part = 'armor' | 'joints' | null;
   55| 
   56| /** Which texture set a material takes, by its name in the GLB. */
   57| export function partOf(materialName: string): Part {
   58|   if (ARMOR.test(materialName)) return 'armor';
   59|   if (JOINTS.test(materialName)) return 'joints';
   60|   return null;
   61| }
   62| 
   63| /** The override for a material: its own entry, else 'Armor' for armour materials. */
   64| export function overrideFor(overrides: PaintOverrides, materialName: string): PaintOverride | undefined {
   65|   return overrides[materialName] ?? (partOf(materialName) === 'armor' ? overrides.Armor : undefined);
   66| }
   67| 
   68| interface PaintSet {
   69|   readonly armor: { readonly map: Texture; readonly emissiveMap: Texture; readonly orm: Texture };
   70|   readonly joints: { readonly map: Texture; readonly orm: Texture };
   71|   readonly overrides: PaintOverrides;
   72| }
   73| 
   74| interface Snapshot {
   75|   readonly map: Texture | null;
   76|   readonly emissiveMap: Texture | null;
   77|   readonly roughnessMap: Texture | null;
   78|   readonly metalnessMap: Texture | null;
   79|   readonly aoMap: Texture | null;
   80|   readonly color: Color;
   81|   readonly emissive: Color;
   82|   readonly roughness: number;
   83|   readonly metalness: number;
   84| }
   85| 
   86| export interface PaintSwitch {
   87|   /** Note each material's own maps and factors (History), once the model is in. */
   88|   capture(materials: Iterable<Material>): void;
   89|   /** Start fetching Rerun in the background, so the first switch is instant. */
   90|   preload(): void;
   91|   /** Swap to a paint. Resolves once it's on (or once it's clear Rerun can't load). */
   92|   set(paint: Paint): Promise<void>;
   93|   readonly current: Paint;
   94|   dispose(): void;
   95| }
   96| 
   97| export function createPaintSwitch(character: Character, maxAnisotropy: number): PaintSwitch {
   98|   let current: Paint = 'history';
   99|   let base: Map<MeshStandardMaterial, Snapshot> | null = null;
  100|   let rerun: Promise<PaintSet | null> | null = null;
  101|   const textures: Texture[] = [];
  102| 
  103|   function load(): Promise<PaintSet | null> {
  104|     if (rerun) return rerun;
  105|     const { dir, version } = character.rerunPaint;
  106|     const url = (file: string) => assetUrl(`${dir}${file}?v=${version}`);
  107|     const loader = new TextureLoader();
  108|     const tex = (file: string, srgb: boolean) =>
  109|       loader.loadAsync(url(file)).then((t) => {
  110|         t.flipY = false; // glTF's convention, as the GLB's own images
  111|         t.colorSpace = srgb ? SRGBColorSpace : NoColorSpace;
  112|         t.anisotropy = Math.min(maxAnisotropy, 8);
  113|         textures.push(t);
  114|         return t;
  115|       });
  116|     const overrides = fetch(url('overrides.json'))
  117|       .then((r): Promise<unknown> => (r.ok ? r.json() : Promise.resolve({})))
  118|       .then(parseOverrides)
  119|       .catch((): PaintOverrides => ({}));
  120|     const pending = Promise.all([
  121|       tex('armor_basecolor.jpg', true),
  122|       tex('armor_emissive.png', true),
  123|       tex('armor_orm.png', false),
  124|       tex('joints_basecolor.png', true),
  125|       tex('joints_orm.png', false),
  126|       overrides,
  127|     ])
  128|       .then(([armorMap, armorEmissive, armorOrm, jointsMap, jointsOrm, parsed]): PaintSet => ({
  129|         armor: { map: armorMap, emissiveMap: armorEmissive, orm: armorOrm },
  130|         joints: { map: jointsMap, orm: jointsOrm },
  131|         overrides: parsed,
  132|       }))
  133|       .catch((err: unknown) => {
  134|         console.warn("[robot] the Rerun paint didn't load; keeping the model's own.", err);
  135|         rerun = null;
  136|         return null;
  137|       });
  138|     rerun = pending;
  139|     return pending;
  140|   }
  141| 
  142|   function apply(set: PaintSet | null): void {
  143|     if (!base) return;
  144|     for (const [m, b] of base) {
  145|       m.map = b.map;
  146|       m.emissiveMap = b.emissiveMap;
  147|       m.roughnessMap = b.roughnessMap;
  148|       m.metalnessMap = b.metalnessMap;
  149|       m.aoMap = b.aoMap;
  150|       m.color.copy(b.color);
  151|       m.emissive.copy(b.emissive);
  152|       m.roughness = b.roughness;
  153|       m.metalness = b.metalness;
  154|       if (set) {
  155|         const part = partOf(m.name);
  156|         if (part === 'armor') {
  157|           m.map = set.armor.map;
  158|           m.emissiveMap = set.armor.emissiveMap;
  159|         } else if (part === 'joints') {
  160|           m.map = set.joints.map;
  161|         }
  162|         // ORM: R occlusion (where the GLB had one), G roughness, B metal.
  163|         const orm = part === null ? null : set[part].orm;
  164|         if (orm) {
  165|           m.roughnessMap = orm;
  166|           m.metalnessMap = orm;
  167|           if (b.aoMap) m.aoMap = orm;
  168|         }
  169|         const o = overrideFor(set.overrides, m.name);
  170|         if (o?.color) m.color.setRGB(o.color[0], o.color[1], o.color[2], LinearSRGBColorSpace);
  171|         if (o?.emissive) m.emissive.setRGB(o.emissive[0], o.emissive[1], o.emissive[2], LinearSRGBColorSpace);
  172|         if (o?.roughness !== undefined) m.roughness = o.roughness;
  173|         if (o?.metalness !== undefined) m.metalness = o.metalness;
  174|       }
  175|       m.needsUpdate = true;
  176|     }
  177|   }
  178| 
  179|   return {
  180|     capture(materials) {
  181|       base = new Map();
  182|       for (const m of materials) {
  183|         if (!(m instanceof MeshStandardMaterial)) continue;
  184|         base.set(m, {
  185|           map: m.map,
  186|           emissiveMap: m.emissiveMap,
  187|           roughnessMap: m.roughnessMap,
  188|           metalnessMap: m.metalnessMap,
  189|           aoMap: m.aoMap,
  190|           color: m.color.clone(),
  191|           emissive: m.emissive.clone(),
  192|           roughness: m.roughness,
  193|           metalness: m.metalness,
  194|         });
  195|       }
  196|     },
  197|     preload() {
  198|       void load();
  199|     },
  200|     async set(paint) {
  201|       current = paint;
  202|       if (!base) return; // applied once the model is in
  203|       if (paint === 'history') {
  204|         apply(null);
  205|         return;
  206|       }
  207|       const set = await load();
  208|       if (set && current === paint) apply(set);
  209|     },
  210|     get current() {
  211|       return current;
  212|     },
  213|     dispose() {
  214|       for (const t of textures) t.dispose();
  215|       textures.length = 0;
  216|       base = null;
  217|       rerun = null;
  218|     },
  219|   };
  220| }
```

## `src/lib/robot/scene.ts`

```ts
    1| // The robot's scene, drawn into a transparent canvas that fills the frame.
    2| // The robot is framed into a stage box inside it (the page decides where);
    3| // the canvas stays full-size so the box can sit anywhere in the frame.
    4| import {
    5|   ACESFilmicToneMapping,
    6|   Box3,
    7|   type BufferGeometry,
    8|   Group,
    9|   type Material,
   10|   MathUtils,
   11|   Mesh,
   12|   MeshStandardMaterial,
   13|   type Object3D,
   14|   PCFShadowMap,
   15|   PerspectiveCamera,
   16|   Scene,
   17|   Texture,
   18|   Vector2,
   19|   Vector3,
   20|   WebGLRenderer,
   21| } from 'three';
   22| import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
   23| import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
   24| import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
   25| import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
   26| import { assetUrl } from './assets';
   27| import { createChestBlast } from './blast';
   28| import { computeFraming, createFloat, type LensShift, stageRect, viewOffset } from './camera';
   29| import { ATLAS, type Character, type Paint } from './characters';
   30| import { createLighting, REACTOR_POWER } from './lighting';
   31| import type { RobotAnchors, RobotStage } from './messages';
   32| import { createMotion, type Motion } from './motion';
   33| import { createPaintSwitch } from './paint';
   34| import { easeToward } from './stage';
   35| 
   36| export interface MountOptions {
   37|   readonly canvas: HTMLCanvasElement;
   38|   /** The current stage box, read every frame. */
   39|   readonly stage: () => RobotStage;
   40|   readonly character?: Character;
   41| }
   42| 
   43| export interface RobotApp {
   44|   /** The stage changed: re-fit the renderer and lens at the start of the next frame. */
   45|   restage(): void;
   46|   /** Start or stop the render loop. Nothing draws or animates while stopped. */
   47|   setRunning(on: boolean): void;
   48|   setWalking(on: boolean): void;
   49|   setPaint(paint: Paint): void;
   50|   /**
   51|    * A shot out of the chest reactor in `color` (#rrggbb), the way the robot
   52|    * faces: mostly across the screen, a little toward the viewer, so it stays
   53|    * in the picture. False before the model loads.
   54|    */
   55|   blast(color: string): boolean;
   56|   /** Called every frame with the robot's anchors in canvas px, or null while it loads. */
   57|   onAnchors(listener: (anchors: RobotAnchors | null) => void): () => void;
   58|   dispose(): void;
   59| }
   60| 
   61| function materialsOf(mesh: Mesh): Material[] {
   62|   return Array.isArray(mesh.material) ? mesh.material : [mesh.material];
   63| }
   64| 
   65| function disposeModel(root: Object3D): void {
   66|   const geometries = new Set<BufferGeometry>();
   67|   const materials = new Set<Material>();
   68|   const textures = new Set<Texture>();
   69|   root.traverse((o) => {
   70|     if (!(o instanceof Mesh)) return;
   71|     geometries.add(o.geometry);
   72|     for (const m of materialsOf(o)) materials.add(m);
   73|   });
   74|   for (const m of materials) {
   75|     for (const value of Object.values(m)) if (value instanceof Texture) textures.add(value);
   76|     m.dispose();
   77|   }
   78|   for (const t of textures) t.dispose();
   79|   for (const g of geometries) g.dispose();
   80| }
   81| 
   82| export function mountRobot({ canvas, stage, character = ATLAS }: MountOptions): RobotApp {
   83|   const width = () => canvas.clientWidth || innerWidth;
   84|   const height = () => canvas.clientHeight || innerHeight;
   85| 
   86|   const renderer = new WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance' });
   87|   renderer.setPixelRatio(Math.min(devicePixelRatio, 1.75));
   88|   renderer.setSize(width(), height(), false);
   89|   renderer.setClearColor(0x000000, 0);
   90|   renderer.shadowMap.enabled = true;
   91|   renderer.shadowMap.type = PCFShadowMap;
   92|   renderer.toneMapping = ACESFilmicToneMapping;
   93| 
   94|   // No background and no fog: the page shows through around the robot.
   95|   const scene = new Scene();
   96|   const initial = stage();
   97|   const camera = new PerspectiveCamera(character.fov, initial.width / initial.height, 0.1, 400);
   98|   const lights = createLighting(renderer, scene, character.reactorLight);
   99|   const paint = createPaintSwitch(character, renderer.capabilities.getMaxAnisotropy());
  100|   lights.apply(character.lighting[paint.current]);
  101| 
  102|   const composer = new EffectComposer(renderer);
  103|   composer.addPass(new RenderPass(scene, camera));
  104|   composer.addPass(new OutputPass());
  105| 
  106|   // The robot's turntable: mirrored and turned with the stage.
  107|   const hero = new Group();
  108|   scene.add(hero);
  109|   // Shots from the chest reactor (blast()), and the robot rocking back from the last one.
  110|   const chestBlast = createChestBlast(scene);
  111|   const recoilDir = new Vector3();
  112|   let recoilSize = 0;
  113| 
  114|   const target = new Vector3();
  115|   const lens: LensShift = { x: 0, y: 0 };
  116|   const float = createFloat();
  117|   let model: Object3D | null = null;
  118|   let chestBone: Object3D | null = null;
  119|   let motion: Motion | null = null;
  120|   let modelHeight = 0;
  121|   let emitters: { mat: MeshStandardMaterial; intensity: number }[] = [];
  122|   let walkWanted = false;
  123|   let restagePending = false;
  124|   let disposed = false;
  125| 
  126|   function applyLens(): void {
  127|     camera.setViewOffset(...viewOffset(stageRect(stage(), width(), height()), lens, width(), height()));
  128|   }
  129| 
  130|   function resetCamera(): void {
  131|     const framing = computeFraming(character, camera.aspect, stage().mirror);
  132|     target.copy(framing.target);
  133|     camera.position.copy(framing.position);
  134|     lens.x = framing.shift.x;
  135|     lens.y = framing.shift.y;
  136|     applyLens();
  137|     camera.lookAt(target);
  138|   }
  139| 
  140|   // The renderer at the canvas's size and the lens re-applied. setSize clears
  141|   // the canvas, so it's skipped when the size hasn't changed.
  142|   const sizeNow = new Vector2();
  143|   function fitRenderer(): void {
  144|     const w = width();
  145|     const h = height();
  146|     renderer.getSize(sizeNow);
  147|     if (sizeNow.x !== w || sizeNow.y !== h) {
  148|       renderer.setSize(w, h, false);
  149|       composer.setSize(w, h);
  150|     }
  151|     const s = stage();
  152|     camera.aspect = s.width / s.height;
  153|     applyLens();
  154|   }
  155| 
  156|   const anchorListeners = new Set<(anchors: RobotAnchors | null) => void>();
  157|   const projected = new Vector3();
  158|   const toScreen = (x: number, y: number, z: number) => {
  159|     projected.set(x, y, z).project(camera);
  160|     return { x: ((projected.x + 1) / 2) * width(), y: ((1 - projected.y) / 2) * height() };
  161|   };
  162|   // The body's centre line (head over feet, on the model's own vertical axis)
  163|   // and the floor under it, from the camera as rendered, float included.
  164|   function emitAnchors(): void {
  165|     if (anchorListeners.size === 0) return;
  166|     let anchors: RobotAnchors | null = null;
  167|     if (model) {
  168|       const head = toScreen(0, modelHeight, 0);
  169|       const feet = toScreen(0, 0, 0);
  170|       anchors = { centerX: (head.x + feet.x) / 2, feetY: feet.y };
  171|     }
  172|     for (const listener of anchorListeners) listener(anchors);
  173|   }
  174| 
  175|   async function load(): Promise<void> {
  176|     const gltf = await new GLTFLoader().loadAsync(assetUrl(character.model));
  177|     if (disposed) {
  178|       disposeModel(gltf.scene);
  179|       return;
  180|     }
  181|     const root = gltf.scene;
  182|     // Scaled to the character's height, centred on the vertical axis, feet on y = 0.
  183|     const box = new Box3().setFromObject(root);
  184|     const size = box.getSize(new Vector3());
  185|     const scale = character.height / size.y;
  186|     root.scale.setScalar(scale);
  187|     const center = box.getCenter(new Vector3());
  188|     root.position.set(-center.x * scale, -box.min.y * scale, -center.z * scale);
  189|     hero.add(root);
  190|     modelHeight = size.y * scale;
  191| 
  192|     const materials = new Set<Material>();
  193|     const maxAnisotropy = Math.min(renderer.capabilities.getMaxAnisotropy(), 8);
  194|     root.traverse((o) => {
  195|       if (!(o instanceof Mesh)) return;
  196|       o.castShadow = true;
  197|       o.receiveShadow = true;
  198|       o.frustumCulled = false;
  199|       for (const m of materialsOf(o)) materials.add(m);
  200|     });
  201|     emitters = [];
  202|     for (const m of materials) {
  203|       if (!(m instanceof MeshStandardMaterial)) continue;
  204|       if (m.map) m.map.anisotropy = maxAnisotropy;
  205|       const name = m.name.toLowerCase();
  206|       if (name.includes('reactor') || name.includes('emission')) emitters.push({ mat: m, intensity: m.emissiveIntensity || 1 });
  207|     }
  208|     paint.capture(materials);
  209|     if (paint.current === 'history') paint.preload();
  210|     else void paint.set(paint.current);
  211| 
  212|     model = root;
  213|     chestBone = root.getObjectByName('chest') ?? null;
  214|     motion = createMotion(root, gltf.animations, character);
  215|     if (walkWanted) motion.setWalking(true);
  216|     resetCamera();
  217|   }
  218| 
  219|   let last = performance.now();
  220|   let time = 0;
  221|   function frame(now: number): void {
  222|     const dt = Math.min((now - last) / 1000, 0.05);
  223|     last = now;
  224|     time += dt;
  225|     if (restagePending) {
  226|       restagePending = false;
  227|       fitRenderer();
  228|     }
  229|     const s = stage();
  230|     const mirror = s.mirror ? -1 : 1;
  231|     if (hero.scale.x !== mirror) {
  232|       hero.scale.x = mirror;
  233|       if (model) resetCamera();
  234|     }
  235|     hero.rotation.y = easeToward(hero.rotation.y, MathUtils.degToRad(s.yaw), dt);
  236|     motion?.update(dt);
  237|     chestBlast.update(dt);
  238|     hero.position.copy(recoilDir).multiplyScalar(-chestBlast.recoil() * recoilSize * 0.025);
  239|     const glow = REACTOR_POWER * (1 + Math.sin(time * 2.3) * 0.06);
  240|     for (const { mat, intensity } of emitters) mat.emissiveIntensity = intensity * glow;
  241|     camera.lookAt(target);
  242|     float.apply(camera, target, time);
  243|     emitAnchors();
  244|     composer.render();
  245|     float.restore(camera, target);
  246|   }
  247| 
  248|   resetCamera();
  249|   fitRenderer();
  250|   renderer.setAnimationLoop(frame);
  251|   load().catch((err: unknown) => {
  252|     if (!disposed) console.error('[robot] the model did not load', err);
  253|   });
  254| 
  255|   // With a stage the framing is the stage's, so a resize only re-fits the lens.
  256|   const onResize = () => fitRenderer();
  257|   window.addEventListener('resize', onResize);
  258|   const resizeObserver = new ResizeObserver(onResize);
  259|   resizeObserver.observe(canvas);
  260| 
  261|   return {
  262|     restage() {
  263|       restagePending = true;
  264|     },
  265|     setRunning(on) {
  266|       if (on) last = performance.now();
  267|       renderer.setAnimationLoop(on ? frame : null);
  268|     },
  269|     setWalking(on) {
  270|       walkWanted = on;
  271|       motion?.setWalking(on);
  272|     },
  273|     setPaint(next) {
  274|       lights.apply(character.lighting[next]);
  275|       void paint.set(next);
  276|     },
  277|     blast(color) {
  278|       if (!model || !chestBone) return false;
  279|       model.updateMatrixWorld(true);
  280|       const box = new Box3().setFromObject(model);
  281|       const size = box.max.y - box.min.y || 10;
  282|       const fwd = new Vector3(0, 0, 1).transformDirection(model.matrixWorld);
  283|       fwd.y = 0;
  284|       fwd.normalize();
  285|       const view = camera.getWorldDirection(new Vector3());
  286|       const direction = fwd.clone().addScaledVector(view, -fwd.dot(view) * 0.75).normalize();
  287|       // The chest bone sits below the reactor: the shot leaves 0.17 robot heights up.
  288|       const origin = chestBone.getWorldPosition(new Vector3()).addScaledVector(fwd, size * 0.07);
  289|       origin.y += size * 0.17;
  290|       chestBlast.fire({ origin, direction, size, color });
  291|       recoilDir.copy(direction);
  292|       recoilSize = size;
  293|       return true;
  294|     },
  295|     onAnchors(listener) {
  296|       anchorListeners.add(listener);
  297|       return () => anchorListeners.delete(listener);
  298|     },
  299|     dispose() {
  300|       disposed = true;
  301|       renderer.setAnimationLoop(null);
  302|       window.removeEventListener('resize', onResize);
  303|       resizeObserver.disconnect();
  304|       anchorListeners.clear();
  305|       chestBlast.dispose();
  306|       motion?.dispose();
  307|       if (model) disposeModel(model);
  308|       paint.dispose();
  309|       lights.dispose();
  310|       composer.dispose();
  311|       renderer.dispose();
  312|     },
  313|   };
  314| }
```

## `src/lib/robot/stage.test.ts`

```ts
    1| import { describe, expect, test } from 'vitest';
    2| import {
    3|   boxMoved,
    4|   DEFAULT_STAGE,
    5|   dragTurn,
    6|   easeToward,
    7|   nudgeToSlot,
    8|   ROBOT_YAW,
    9|   sameStage,
   10|   stageInSlot,
   11|   YAW_SWAY,
   12|   yawForYear,
   13| } from './stage';
   14| 
   15| const rect = (left: number, top: number, width: number, height: number) => ({
   16|   left,
   17|   top,
   18|   width,
   19|   right: left + width,
   20|   bottom: top + height,
   21| });
   22| 
   23| describe('yawForYear', () => {
   24|   test('the first and last elections turn the full sway either side of the resting yaw', () => {
   25|     expect(yawForYear(0, 60)).toBe(ROBOT_YAW - YAW_SWAY);
   26|     expect(yawForYear(59, 60)).toBe(ROBOT_YAW + YAW_SWAY);
   27|   });
   28| 
   29|   test('the middle of the time bar is the resting yaw', () => {
   30|     expect(yawForYear(2, 5)).toBe(40);
   31|   });
   32| 
   33|   test('rounds to a tenth of a degree', () => {
   34|     // 40 + (1/58 - 0.5) * 16 = 32.2758…
   35|     expect(yawForYear(1, 59)).toBe(32.3);
   36|   });
   37| 
   38|   test('an unknown year keeps the resting yaw', () => {
   39|     expect(yawForYear(-1, 60)).toBe(ROBOT_YAW);
   40|     expect(yawForYear(60, 60)).toBe(ROBOT_YAW);
   41|     expect(yawForYear(0, 1)).toBe(ROBOT_YAW);
   42|   });
   43| });
   44| 
   45| describe('easeToward', () => {
   46|   test('moves a fifth of the way per 1/25 s at the default rate', () => {
   47|     expect(easeToward(0, 1, 0.04)).toBeCloseTo(0.2, 10);
   48|   });
   49| 
   50|   test('never overshoots on a long frame', () => {
   51|     expect(easeToward(0, 1, 0.5)).toBe(1);
   52|   });
   53| 
   54|   test('converges on the target', () => {
   55|     let yaw = 0;
   56|     for (let i = 0; i < 120; i++) yaw = easeToward(yaw, 0.7, 1 / 60);
   57|     expect(yaw).toBeCloseTo(0.7, 4);
   58|   });
   59| 
   60|   test('a zero or negative frame leaves it where it is', () => {
   61|     expect(easeToward(0.3, 1, 0)).toBe(0.3);
   62|     expect(easeToward(0.3, 1, -1)).toBe(0.3);
   63|   });
   64| });
   65| 
   66| describe('stageInSlot', () => {
   67|   test('centres the 200px box on the slot with its floor on the slot’s bottom', () => {
   68|     const host = rect(0, 0, 1200, 900);
   69|     const slot = rect(100, 500, 300, 200); // centre x 250, bottom 700
   70|     const s = stageInSlot(host, slot, { x: 0, y: 0 }, 40);
   71|     expect(s).toEqual({ right: 1200 - 250 - 100, bottom: 200, width: 200, height: 260, mirror: true, yaw: 40 });
   72|   });
   73| 
   74|   test('a nudge moves the box right and down', () => {
   75|     const host = rect(0, 0, 1200, 900);
   76|     const slot = rect(100, 500, 300, 200);
   77|     const s = stageInSlot(host, slot, { x: 12, y: -5 }, 40);
   78|     expect(s.right).toBe(850 - 12);
   79|     expect(s.bottom).toBe(200 + 5);
   80|   });
   81| });
   82| 
   83| describe('nudgeToSlot', () => {
   84|   test('is the gap between the robot and the slot’s centre and floor', () => {
   85|     const slot = rect(100, 500, 300, 200);
   86|     expect(nudgeToSlot(slot, { centerX: 240, feetY: 690 })).toEqual({ x: 10, y: 4 });
   87|   });
   88| });
   89| 
   90| describe('sameStage', () => {
   91|   test('compares by value', () => {
   92|     expect(sameStage(DEFAULT_STAGE, { ...DEFAULT_STAGE })).toBe(true);
   93|     expect(sameStage(DEFAULT_STAGE, { ...DEFAULT_STAGE, yaw: 1 })).toBe(false);
   94|     expect(sameStage(null, null)).toBe(true);
   95|     expect(sameStage(null, DEFAULT_STAGE)).toBe(false);
   96|   });
   97| });
   98| 
   99| describe('dragTurn', () => {
  100|   test('a press that hasn’t moved 4px is still a tap', () => {
  101|     expect(dragTurn(0, false)).toBeNull();
  102|     expect(dragTurn(3, false)).toBeNull();
  103|     expect(dragTurn(-3.9, false)).toBeNull();
  104|   });
  105|   test('past 4px it turns 0.6° per px, to the whole degree', () => {
  106|     expect(dragTurn(4, false)).toBe(2);
  107|     expect(dragTurn(-10, false)).toBe(-6);
  108|     expect(dragTurn(101, false)).toBe(61);
  109|   });
  110|   test('once a drag, back under 4px still turns (and back to zero is zero)', () => {
  111|     expect(dragTurn(2, true)).toBe(1);
  112|     expect(dragTurn(0, true)).toBe(0);
  113|     expect(Object.is(dragTurn(-0.4, true), 0)).toBe(true);
  114|   });
  115|   test('held to half a turn either way', () => {
  116|     expect(dragTurn(1000, true)).toBe(180);
  117|     expect(dragTurn(-1000, true)).toBe(-180);
  118|   });
  119|   test('let go, the renderer eases the turn back to rest', () => {
  120|     const rest = (ROBOT_YAW * Math.PI) / 180;
  121|     let yaw = ((ROBOT_YAW + (dragTurn(300, true) ?? 0)) * Math.PI) / 180;
  122|     const start = Math.abs(yaw - rest);
  123|     for (let i = 0; i < 15; i++) yaw = easeToward(yaw, rest, 1 / 60);
  124|     // A quarter second in, most of the way back, never past rest.
  125|     expect(Math.abs(yaw - rest)).toBeLessThan(start * 0.3);
  126|     expect(yaw).toBeGreaterThan(rest);
  127|     for (let i = 0; i < 240; i++) yaw = easeToward(yaw, rest, 1 / 60);
  128|     expect(yaw).toBeCloseTo(rest, 6);
  129|   });
  130| });
  131| 
  132| describe('boxMoved', () => {
  133|   test('a turn alone is not a move', () => {
  134|     expect(boxMoved(DEFAULT_STAGE, { ...DEFAULT_STAGE, yaw: 123 })).toBe(false);
  135|     expect(boxMoved(DEFAULT_STAGE, { ...DEFAULT_STAGE })).toBe(false);
  136|   });
  137|   test.each(['right', 'bottom', 'width', 'height'] as const)('a changed %s is', (k) => {
  138|     expect(boxMoved(DEFAULT_STAGE, { ...DEFAULT_STAGE, [k]: DEFAULT_STAGE[k] + 1 })).toBe(true);
  139|   });
  140|   test('a flip is', () => {
  141|     expect(boxMoved(DEFAULT_STAGE, { ...DEFAULT_STAGE, mirror: !DEFAULT_STAGE.mirror })).toBe(true);
  142|   });
  143| });
```

## `src/lib/robot/stage.ts`

```ts
    1| // Pure placement math: the robot's box, its turn with the time bar and by
    2| // hand, and the page-side measuring that stands it in a slot.
    3| import type { RobotAnchors, RobotStage } from './messages';
    4| 
    5| /** The box the frame uses until the page sends one. */
    6| export const DEFAULT_STAGE: RobotStage = { right: 10, bottom: 26, width: 200, height: 260, mirror: false, yaw: 0 };
    7| 
    8| /** The robot's size on the page, CSS px. */
    9| export const STAGE_SIZE = { width: 200, height: 260 } as const;
   10| 
   11| /** The robot's resting turn, degrees. */
   12| export const ROBOT_YAW = 40;
   13| /**
   14|  * Its resting turn on a narrow window, where it stands above the what-if
   15|  * rather than beside it: a design choice, found by eye. WhatIf.svelte's
   16|  * narrow --figure-* lengths were measured at this turn.
   17|  */
   18| export const NARROW_ROBOT_YAW = 43;
   19| /** It turns ±this many degrees from the first election to the last. */
   20| export const YAW_SWAY = 8;
   21| /** How quickly the renderer eases toward a new yaw, per second. */
   22| export const YAW_EASE_RATE = 5;
   23| /** Degrees the robot turns per pixel of a drag across it. */
   24| export const DRAG_DEG_PER_PX = 0.6;
   25| /** A press moves this far, px, before it's a drag rather than a tap. */
   26| export const DRAG_START_PX = 4;
   27| 
   28| /**
   29|  * The robot's yaw for the election at `index` of `count` (the time bar),
   30|  * rounded to a tenth of a degree. Out-of-range input keeps the resting yaw.
   31|  */
   32| export function yawForYear(index: number, count: number, base: number = ROBOT_YAW, sway: number = YAW_SWAY): number {
   33|   if (count < 2 || index < 0 || index >= count) return base;
   34|   const fraction = index / (count - 1);
   35|   return Math.round((base + (fraction - 0.5) * 2 * sway) * 10) / 10;
   36| }
   37| 
   38| /** One frame of the yaw easing: `current` moves toward `target` (radians) by dt seconds' worth. */
   39| export function easeToward(current: number, target: number, dt: number, rate: number = YAW_EASE_RATE): number {
   40|   return current + (target - current) * Math.min(1, Math.max(0, dt) * rate);
   41| }
   42| 
   43| /**
   44|  * The turn a drag of `dx` px across the robot gives, degrees, or null while
   45|  * the press is still a tap (`started`: it's already a drag). Held to ±180° so
   46|  * the way back, eased by the renderer on release, is never more than half a turn.
   47|  */
   48| export function dragTurn(dx: number, started: boolean): number | null {
   49|   if (!started && Math.abs(dx) < DRAG_START_PX) return null;
   50|   return Math.max(-180, Math.min(180, Math.round(dx * DRAG_DEG_PER_PX))) || 0;
   51| }
   52| 
   53| export interface Rect {
   54|   readonly left: number;
   55|   readonly top: number;
   56|   readonly right: number;
   57|   readonly bottom: number;
   58|   readonly width: number;
   59| }
   60| 
   61| export interface Nudge {
   62|   readonly x: number;
   63|   readonly y: number;
   64| }
   65| 
   66| /**
   67|  * The stage that stands the robot in `slot`, measured from the frame's host
   68|  * element (`host`, the frame fills it): centred on the slot, feet on its
   69|  * floor, less any nudge, facing into the page (mirrored).
   70|  */
   71| export function stageInSlot(host: Rect, slot: Rect, nudge: Nudge, yaw: number): RobotStage {
   72|   return {
   73|     right: Math.round(host.right - (slot.left + slot.width / 2) - STAGE_SIZE.width / 2 - nudge.x),
   74|     bottom: Math.round(host.bottom - slot.bottom - nudge.y),
   75|     width: STAGE_SIZE.width,
   76|     height: STAGE_SIZE.height,
   77|     mirror: true,
   78|     yaw,
   79|   };
   80| }
   81| 
   82| /** Pixels the robot must move to be centred on the slot with its feet `floorGap` px above its floor. */
   83| export function nudgeToSlot(slot: Rect, anchors: RobotAnchors, floorGap = 6): Nudge {
   84|   return { x: slot.left + slot.width / 2 - anchors.centerX, y: slot.bottom - floorGap - anchors.feetY };
   85| }
   86| 
   87| /**
   88|  * Whether the box moved, resized or flipped between two stages: only then
   89|  * does the frame re-place its canvas. A turn alone is read live and eased.
   90|  */
   91| export function boxMoved(a: RobotStage, b: RobotStage): boolean {
   92|   return a.right !== b.right || a.bottom !== b.bottom || a.width !== b.width || a.height !== b.height || a.mirror !== b.mirror;
   93| }
   94| 
   95| export function sameStage(a: RobotStage | null, b: RobotStage | null): boolean {
   96|   if (a === null || b === null) return a === b;
   97|   return (
   98|     a.right === b.right &&
   99|     a.bottom === b.bottom &&
  100|     a.width === b.width &&
  101|     a.height === b.height &&
  102|     a.mirror === b.mirror &&
  103|     a.yaw === b.yaw
  104|   );
  105| }
```

## `src/lib/robot/style.css`

```css
    1| /* The robot's frame (/robot) is its own document: nothing but the canvas on
    2|    a transparent page, so the host page shows through around the robot.
    3|    color-scheme matches RobotFrame's iframe, or browsers paint the frame opaque. */
    4| html,
    5| body {
    6|   margin: 0;
    7|   height: 100%;
    8|   overflow: hidden;
    9|   background: transparent;
   10|   color-scheme: normal;
   11| }
   12| 
   13| .robot-scene {
   14|   position: fixed;
   15|   inset: 0;
   16|   display: block;
   17|   width: 100%;
   18|   height: 100%;
   19|   pointer-events: none;
   20|   touch-action: none;
   21| }
```

## `src/lib/simulacra/AboutSources.svelte`

```svelte
    1| <script lang="ts">
    2|   // The About popover's Sources: every data source the page and the
    3|   // simulation draw on, grouped, folded until asked for.
    4| </script>
    5| 
    6| <details class="cite-box">
    7|   <summary class="cite-head">Sources</summary>
    8|   <h4 class="cite-group">Population</h4>
    9|   <ul class="cite">
   10|     <li>Schroeder, Jonathan, David Van Riper, Steven Manson, Grace Cooper, Zachary Krause, Tracy Kugler, Tsu Zhu, and Steven Ruggles. <em>IPUMS National Historical Geographic Information System: Version 21.0</em> [dataset]. Minneapolis, MN: IPUMS, 2026. <a href="https://doi.org/10.18128/D050.V21.0" target="_blank" rel="noopener">doi:10.18128/D050.V21.0</a>.</li>
   11|     <li>U.S. Bureau of the Census. <em>Fourteenth Census of the United States Taken in the Year 1920</em>, Vols. II–III, <em>Population</em>. Washington, DC: Government Printing Office, 1922.</li>
   12|   </ul>
   13|   <h4 class="cite-group">Election returns</h4>
   14|   <ul class="cite">
   15|     <li>Algara, Carlos, and Sharif Amlani. “Replication Data for: Partisanship &amp; Nationalization in American Elections: Evidence from Presidential, Senatorial, &amp; Gubernatorial Elections in the U.S. Counties, 1872–2020.” Harvard Dataverse, V1.1, 2022. <a href="https://doi.org/10.7910/DVN/DGUMFI" target="_blank" rel="noopener">doi:10.7910/DVN/DGUMFI</a>.</li>
   16|     <li>Dubin, Michael J. <em>United States Presidential Elections, 1788–1860: The Official Results by County and State</em>. Jefferson, NC: McFarland, 2002.</li>
   17|     <li>Page, William Tyler, Clerk of the House of Representatives. <em>Statistics of the Presidential and Congressional Election of November 2, 1920</em>. Washington, DC: Government Printing Office, 1921; and the 1924 edition, 1925.</li>
   18|     <li>Leip, David. <em>Dave Leip’s Atlas of U.S. Presidential Elections</em>, as tabulated in Wikipedia’s results-by-state tables (early elections and cross-checks).</li>
   19|     <li>Federal Election Commission. <em>Official 2024 Presidential General Election Results</em>. Washington, DC, 2025.</li>
   20|     <li>U.S. National Archives and Records Administration. <em>Electoral College Results</em>, 1789–2024. <a href="https://www.archives.gov/electoral-college" target="_blank" rel="noopener">archives.gov/electoral-college</a>.</li>
   21|   </ul>
   22|   <h4 class="cite-group">Who could vote</h4>
   23|   <ul class="cite">
   24|     <li>Gray, Thomas R., and Jeffery A. Jenkins. “Replication Data for: ‘Estimating Disenfranchisement in U.S. Elections, 1870–1970.’” Harvard Dataverse, V1, 2024. <a href="https://doi.org/10.7910/DVN/QIY9EM" target="_blank" rel="noopener">doi:10.7910/DVN/QIY9EM</a>.</li>
   25|     <li>Teele, Dawn Langan. “Replication Data for: How the West Was Won: Competition, Mobilization, and Women’s Enfranchisement in the United States.” Harvard Dataverse, V1, 2017. <a href="https://doi.org/10.7910/DVN/EVYI2H" target="_blank" rel="noopener">doi:10.7910/DVN/EVYI2H</a>.</li>
   26|     <li>Teele, Dawn Langan. “Replication Data for: Forging the Franchise: The Political Origins of Women’s Votes.” Harvard Dataverse, V1, 2018. <a href="https://doi.org/10.7910/DVN/JZYGRB" target="_blank" rel="noopener">doi:10.7910/DVN/JZYGRB</a>.</li>
   27|     <li>Keyssar, Alexander. <em>The Right to Vote: The Contested History of Democracy in the United States</em>. Rev. ed. New York: Basic Books, 2009.</li>
   28|     <li>Hayduk, Ron. <em>Democracy for All: Restoring Immigrant Voting Rights in the United States</em>. New York: Routledge, 2006.</li>
   29|     <li>Uggen, Christopher, Ryan Larson, and Sarah Shannon. <em>6 Million Lost Voters: State-Level Estimates of Felony Disenfranchisement, 2016</em>. Washington, DC: The Sentencing Project, 2016.</li>
   30|     <li>Corder, J. Kevin. “Replication Data for: Political Context and the Turnout of New Women Voters After Suffrage.” Harvard Dataverse, V1, 2021. <a href="https://doi.org/10.7910/DVN/QB526J" target="_blank" rel="noopener">doi:10.7910/DVN/QB526J</a>. Used as a check on women’s turnout.</li>
   31|   </ul>
   32|   <h4 class="cite-group">What voters read</h4>
   33|   <ul class="cite">
   34|     <li>Peters, Gerhard, and John T. Woolley. <em>The American Presidency Project</em>, party platforms, 1840–2024. Santa Barbara: University of California. <a href="https://www.presidency.ucsb.edu/documents/app-categories/elections-and-transitions/party-platforms" target="_blank" rel="noopener">presidency.ucsb.edu</a>.</li>
   35|     <li>U.S. National Archives. <em>Founders Online</em> (party positions before 1840). <a href="https://founders.archives.gov/" target="_blank" rel="noopener">founders.archives.gov</a>.</li>
   36|     <li>Janda, Kenneth. Party platform archive (Reform Party, 1996). <a href="https://www.janda.org/" target="_blank" rel="noopener">janda.org</a>.</li>
   37|     <li>Library of Congress. <em>Chronicling America: Historic American Newspapers</em>. <a href="https://chroniclingamerica.loc.gov/" target="_blank" rel="noopener">chroniclingamerica.loc.gov</a>.</li>
   38|   </ul>
   39|   <h4 class="cite-group">Portraits</h4>
   40|   <ul class="cite">
   41|     <li>Wikimedia Commons. Candidate portraits, public domain except as noted below. <a href="https://commons.wikimedia.org/" target="_blank" rel="noopener">commons.wikimedia.org</a>.</li>
   42|     <li>Franklin D. Roosevelt: photograph by Leon Perskie, <a href="https://commons.wikimedia.org/wiki/File:FDR-1944-Campaign-Portrait_(3x4_retouched,_cropped).jpg" target="_blank" rel="noopener">FDR-1944-Campaign-Portrait</a>, <a href="https://creativecommons.org/licenses/by/2.0" target="_blank" rel="noopener">CC BY 2.0</a>.</li>
   43|   </ul>
   44| </details>
   45| 
   46| <style>
   47|   /* Grouped references, hanging indent. */
   48|   .cite-box { margin-top: 12px; padding-top: 10px; border-top: 0.5px solid rgba(0, 0, 0, 0.15); }
   49|   .cite-head { display: flex; align-items: center; gap: 6px; font-weight: 600; color: #000; cursor: pointer; list-style: none; user-select: none; }
   50|   .cite-head::-webkit-details-marker { display: none; }
   51|   /* A chevron that turns when the list opens. */
   52|   .cite-head::after { content: ''; width: 4px; height: 4px; margin-top: -2px; margin-left: auto; margin-right: 2px; border-right: 1.5px solid rgba(0, 0, 0, 0.5); border-bottom: 1.5px solid rgba(0, 0, 0, 0.5); transform: rotate(45deg); transition: transform 0.18s ease; }
   53|   .cite-box[open] .cite-head::after { margin-top: 2px; transform: rotate(225deg); }
   54|   .cite-head:hover { opacity: 0.7; }
   55|   .cite-box[open] .cite-head { margin-bottom: 4px; }
   56|   .cite-group { margin: 8px 0 4px; font-size: 10.5px; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; color: rgba(0, 0, 0, 0.5); }
   57|   .cite { list-style: none; margin: 0; padding: 0; }
   58|   .cite li { margin: 0 0 6px; padding-left: 1.2em; text-indent: -1.2em; font-size: 11px; line-height: 1.4; color: rgba(0, 0, 0, 0.62); }
   59|   .cite a { color: #3876b7; text-decoration: none; word-break: break-all; }
   60|   .cite a:hover { text-decoration: underline; }
   61|   @media (prefers-reduced-motion: reduce) { .cite-head::after { transition: none; } }
   62| </style>
```

## `src/lib/simulacra/AbsentRow.svelte`

```svelte
    1| <script lang="ts">
    2|   // A group the year has no simulation for, held in its usual place on a
    3|   // narrow window so every year shows five rows (absentGroups in groups.ts):
    4|   // its name, why it's missing, and a faint dashed rule where SliceRow's dots
    5|   // go. Laid out as SliceRow's head, so it's as tall; nothing to tap or drag.
    6|   import GroupLabel from './GroupLabel.svelte';
    7|   import { type Absent, DOTS } from './groups';
    8| 
    9|   let { absent }: { absent: Absent } = $props();
   10| 
   11|   const N = DOTS;
   12| </script>
   13| 
   14| <div class="row" role="group" aria-label="{absent.label}: {absent.why}">
   15|   <div class="head">
   16|     <span class="who">
   17|       <span class="label"><GroupLabel label={absent.label} /></span>
   18|       <span class="cap">{absent.why}</span>
   19|     </span>
   20|     <svg class="strip" viewBox="0 0 {N * 10} 10" preserveAspectRatio="xMinYMid meet" aria-hidden="true">
   21|       <line x1="2" y1="5" x2={N * 10 - 2} y2="5" />
   22|     </svg>
   23|   </div>
   24| </div>
   25| 
   26| <style>
   27|   /* = SliceRow's narrow head (≤700px: the strip under the name), quieter. */
   28|   .row { position: relative; border-radius: 12px; }
   29|   .head {
   30|     display: grid;
   31|     grid-template-columns: minmax(0, 1fr);
   32|     row-gap: var(--strip-gap);
   33|     align-items: center;
   34|     min-height: var(--row-min);
   35|     padding: var(--row-pad-y) var(--row-pad-x);
   36|   }
   37|   .who { display: flex; flex-direction: column; gap: var(--who-gap); min-width: 0; }
   38|   .label { font-size: var(--name-size); font-weight: 600; line-height: var(--name-leading); color: rgba(0, 0, 0, 0.45); }
   39|   .cap { font-size: var(--note-size); line-height: var(--note-leading); color: rgba(0, 0, 0, 0.45); }
   40|   .strip { width: 100%; height: auto; display: block; overflow: visible; }
   41|   .strip line { stroke: rgba(0, 0, 0, 0.18); stroke-width: 1.2; stroke-dasharray: 4 6; stroke-linecap: round; }
   42|   /* 701-760px: SliceRow sets its dots beside the name; so does this. */
   43|   @media (min-width: 701px) {
   44|     .head { grid-template-columns: minmax(160px, 212px) minmax(0, 1fr) 124px; gap: 16px; }
   45|   }
   46| </style>
```

## `src/lib/simulacra/ElectionHeader.svelte`

```svelte
    1| <script lang="ts">
    2|   // The election at the top of the page: the two candidates with their
    3|   // portraits and electoral votes, the year and the map between them, the
    4|   // year's note and anyone else who won votes. With a rerun it shows the
    5|   // rerun's numbers, with history's beside them.
    6|   import { alsoRanOf, mapLabelOf, type Paints } from './header';
    7|   import type { Election } from './history';
    8|   import MiniMap from './MiniMap.svelte';
    9|   import Places from './Places.svelte';
   10|   import Portrait from './Portrait.svelte';
   11|   import type { ShownRun } from './state';
   12|   import type { Names } from './types';
   13| 
   14|   interface Props {
   15|     election: Election;
   16|     year: number;
   17|     rerun: ShownRun | null;
   18|     paints: Paints;
   19|     names: Names;
   20|     light: boolean;
   21|     /** State codes to light on the map (places named in the text being read). */
   22|     highlight: readonly string[];
   23|     /** A height to hold, px (0: none): the page's scrub hold. */
   24|     hold?: number;
   25|     /** The block's rendered height, px. */
   26|     height?: number;
   27|   }
   28| 
   29|   let { election: e, year, rerun, paints, names, light, highlight, hold = 0, height = $bindable(0) }: Props = $props();
   30| 
   31|   const A = $derived(e.candidates[0]);
   32|   const B = $derived(e.candidates[1] ?? null);
   33|   const colors = $derived(paints.colors);
   34|   const evNow = $derived<Record<'A' | 'B', number>>(rerun ? rerun.ev : { A: A.ev, B: B?.ev ?? 0 });
   35|   const winner = $derived(rerun ? rerun.winner : 'A');
   36|   const evByState = $derived(new Map(e.states.map((s) => [s.code, s.ev])));
   37|   const mapStates = $derived(rerun ? rerun.states.map((s) => ({ ...s, ev: evByState.get(s.code) })) : e.states);
   38|   const flips = $derived(rerun ? rerun.states.filter((s) => s.flipped).length : 0);
   39|   const mapLabel = $derived(mapLabelOf(year, !!rerun, e, mapStates, flips));
   40|   const alsoRan = $derived(alsoRanOf(e.candidates.slice(2)));
   41|   const matchup = $derived([{ c: A, k: 'A' as const }, ...(B ? [{ c: B, k: 'B' as const }] : [])]);
   42|   // In the Rerun view the note names what the last rerun ran: its chips'
   43|   // text, as the chips show it. History's note before any rerun, and for a
   44|   // rerun that applied no what-ifs (groups dragged by hand).
   45|   const ranText = $derived(rerun ? rerun.applied.map((a) => a.label).join(' · ') : '');
   46|   const note = $derived(ranText || e.note);
   47| </script>
   48| 
   49| <section class="election" aria-labelledby="sa-year" bind:offsetHeight={height} style:min-height={hold ? `${hold}px` : null}>
   50|   <div class="matchup" class:solo={!B}>
   51|     {#each matchup as { c, k } (k)}
   52|       <div class="cand" class:b={k === 'B'}>
   53|         <Portrait candidate={c} color={colors[k]} ink={paints.inks[k]} won={winner === k} {light} size={96} />
   54|         <div class="facts">
   55|           <p class="name">{c.name}{#if winner === k}<span class="sr">{' (won)'}</span>{/if}</p>
   56|           <p class="party">{c.partyLabel}</p>
   57|           <p class="num">{evNow[k]}</p>
   58|           <p class="ev">electoral vote{evNow[k] === 1 ? '' : 's'}</p>
   59|           {#if rerun}
   60|             <p class="sub">{c.ev} in history</p>
   61|           {:else if c.popular != null}
   62|             <p class="sub">{c.popular.toFixed(1)}% of the vote</p>
   63|           {:else}
   64|             <p class="sub sub-room" aria-hidden="true">&nbsp;</p>
   65|           {/if}
   66|         </div>
   67|       </div>
   68|       {#if k === 'A'}
   69|         <div class="center">
   70|           <h1 id="sa-year" class="year">{year}</h1>
   71|           <MiniMap {year} states={mapStates} {colors} {names} label={mapLabel} tile={12} {highlight} />
   72|           <p class="needed">{e.majority} to win{#if flips}<span class="flips">{` · `}<span class="dot" aria-hidden="true"></span>{`${flips} flipped`}</span>{/if}</p>
   73|         </div>
   74|       {/if}
   75|     {/each}
   76|   </div>
   77|   <!-- Always both, empty or not. On a narrow window .foot holds the room of
   78|        the longest pair (below); on a wide one it isn't a box at all. -->
   79|   <div class="foot">
   80|     <p class="note">{#if note}<Places text={note} />{/if}</p>
   81|     <p class="also">{#if alsoRan}Also ran: {alsoRan}{/if}</p>
   82|   </div>
   83| </section>
   84| 
   85| <style>
   86|   /* Zero jitter while scrubbing: the block reserves its tallest year (a
   87|      two-line note plus an also-ran line), so the page's height never changes
   88|      with the year. Measured across all 60 years at 1440px (189–246px);
   89|      narrower windows are covered by the page's scrub hold. */
   90|   .election { display: flex; flex-direction: column; align-items: center; text-align: center; min-height: 246px; }
   91|   .matchup {
   92|     margin-top: 6px;
   93|     display: grid;
   94|     grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
   95|     align-items: center;
   96|     gap: 28px;
   97|     width: 100%;
   98|   }
   99|   .matchup.solo { grid-template-columns: auto auto; justify-content: center; gap: 56px; }
  100|   .cand { display: flex; align-items: center; gap: 18px; min-width: 0; }
  101|   .cand.b { flex-direction: row-reverse; }
  102|   .facts { display: flex; flex-direction: column; align-items: flex-start; min-width: 0; text-align: left; }
  103|   .b .facts { align-items: flex-end; text-align: right; }
  104|   .facts p { margin: 0; }
  105|   .name { font-size: 17px; font-weight: 600; line-height: 1.2; }
  106|   .party { margin-top: 2px !important; font-size: 13px; color: rgba(0, 0, 0, 0.55); }
  107|   .num { margin-top: 10px !important; font-size: 32px; line-height: 1; font-weight: 700; letter-spacing: -0.01em; font-variant-numeric: tabular-nums; }
  108|   .ev { margin-top: 3px !important; font-size: 12px; color: rgba(0, 0, 0, 0.6); }
  109|   .sub { margin-top: 1px !important; font-size: 12px; color: rgba(0, 0, 0, 0.5); font-variant-numeric: tabular-nums; }
  110|   .center { display: flex; flex-direction: column; align-items: center; gap: 8px; }
  111|   .year {
  112|     margin: 0;
  113|     font-size: 44px;
  114|     line-height: 1;
  115|     font-weight: 700;
  116|     letter-spacing: 0.018em;
  117|     font-variant-numeric: tabular-nums;
  118|   }
  119|   .needed { margin: -2px 0 0; font-size: 12px; color: rgba(0, 0, 0, 0.5); font-variant-numeric: tabular-nums; }
  120|   /* The key to the map's flip mark: the same dot (black at 50%). */
  121|   .flips .dot { display: inline-block; width: 7px; height: 7px; margin: 0 4px 0 1px; border-radius: 999px; background: #00000080; vertical-align: 0.5px; }
  122|   .note { margin: 12px 0 0; max-width: 60ch; font-size: 15px; line-height: 1.45; color: rgba(0, 0, 0, 0.72); }
  123|   .also { margin: 6px 0 0; max-width: 70ch; font-size: 12px; line-height: 1.45; color: rgba(0, 0, 0, 0.5); }
  124|   .sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
  125| 
  126|   @media (max-width: 760px) {
  127|     .year { font-size: 40px; }
  128|     .matchup { grid-template-columns: 1fr 1fr; gap: 22px 12px; }
  129|     .matchup.solo { grid-template-columns: 1fr; gap: 22px 12px; } /* = .matchup: an unopposed year is as tall as any */
  130|     .center { grid-column: 1 / -1; grid-row: 1; }
  131|     /* The candidates sit 20px into the gap under the map. */
  132|     .cand, .cand.b { flex-direction: column; gap: 12px; margin-top: -20px; }
  133|     .facts, .b .facts { align-items: center; text-align: center; }
  134|     .name { font-size: 15px; }
  135|     /* Phones: the block is one height every year, so the what-if and the
  136|        robot below it never move with the year. Each part that varies holds
  137|        its most: two lines of name and party, three of note, two of also-ran
  138|        (measured over all 60 years at 320-430px). */
  139|     .name { min-height: calc(2 * 1.2em); }
  140|     .party { line-height: 1.25; min-height: calc(2 * 1.25em); }
  141|     /* The note sits 23px under the candidates at its own height, the
  142|        also-ran under it; the pair's room is their most (three lines of note,
  143|        two of also-ran), the spare at its foot, so the block stays one height. */
  144|     .note { margin-top: 23px; }
  145|     .foot {
  146|       display: flex;
  147|       flex-direction: column;
  148|       align-items: center;
  149|       width: 100%;
  150|       min-height: calc(23px + 3 * 1.45 * 15px + 6px + 2 * 1.45 * 12px);
  151|     }
  152|   }
  153|   /* The narrowest phones: a long name ("Charles Cotesworth Pinckney") takes three lines. */
  154|   @media (max-width: 359px) {
  155|     .name { min-height: calc(3 * 1.2em); }
  156|   }
  157|   /* Empty, they take no room on a wide window. */
  158|   @media (min-width: 761px) {
  159|     .foot { display: contents; }
  160|     .note:empty, .also:empty, .sub-room { display: none; }
  161|   }
  162| </style>
```

## `src/lib/simulacra/GroupLabel.svelte`

```svelte
    1| <script lang="ts">
    2|   // A group's name. On a narrow window the word "citizens" is set small and
    3|   // italic, without the parentheses some years' names put round it ("Men
    4|   // outside the South (citizens)", 1972 on), so the name keeps to one line
    5|   // beside its result; a wide window sets the name as it is.
    6|   let { label }: { label: string } = $props();
    7| 
    8|   const parts = $derived(label.split(/(\(citizens\)|\bcitizens\b)/));
    9| </script>
   10| 
   11| {#each parts as part, i (i)}{#if part === '(citizens)'}<span class="paren">(</span><span class="small">citizens</span><span class="paren">)</span>{:else if part === 'citizens'}<span class="small">{part}</span>{:else}{part}{/if}{/each}
   12| 
   13| <style>
   14|   @media (max-width: 760px) {
   15|     .small { font-size: 8px; font-weight: normal; font-style: italic; }
   16|     .paren { display: none; }
   17|   }
   18| </style>
```

## `src/lib/simulacra/InfoPopover.svelte`

```svelte
    1| <script lang="ts">
    2|   // An info button that opens a short explanation — for terms (backtest, held
    3|   // out, leakage) that need a sentence, not a tooltip.
    4|   import { Info } from 'lucide-svelte';
    5|   import type { Snippet } from 'svelte';
    6|   import { toBody } from './actions';
    7| 
    8|   interface Props {
    9|     label?: string;
   10|     align?: 'start' | 'end';
   11|     children?: Snippet;
   12|   }
   13|   let { label = 'More information', align = 'start', children }: Props = $props();
   14| 
   15|   let open = $state(false);
   16|   let root = $state<HTMLElement | null>(null);
   17|   let pop = $state<HTMLElement | null>(null);
   18|   const outside = (e: PointerEvent) => {
   19|     if (!open || !root) return;
   20|     const path = e.composedPath();
   21|     if (!path.includes(root) && !(pop && path.includes(pop))) open = false;
   22|   };
   23|   const key = (e: KeyboardEvent) => {
   24|     if (open && e.key === 'Escape') {
   25|       e.stopPropagation();
   26|       open = false;
   27|     }
   28|   };
   29| 
   30|   // Always on top: the popover is moved to <body> and fixed under its button,
   31|   // so no stacking context in the page (the robot's frame, the time bar on
   32|   // <body>, a filtered wrapper) can cover it.
   33|   let pos = $state({ top: 0, left: 0, right: 0, max: 600 });
   34|   function place(): void {
   35|     const r = root?.getBoundingClientRect();
   36|     if (r) pos = { top: r.bottom + 6, left: r.left - 8, right: innerWidth - r.right - 8, max: innerHeight - r.bottom - 22 };
   37|   }
   38|   $effect(() => {
   39|     if (open) place();
   40|   });
   41|   const replace = () => {
   42|     if (open) place();
   43|   };
   44| </script>
   45| 
   46| <svelte:window onpointerdown={outside} onkeydown={key} onresize={replace} onscrollcapture={replace} />
   47| 
   48| <span class="info" bind:this={root}>
   49|   <button type="button" aria-label={label} aria-expanded={open} title={label} onclick={() => (open = !open)}>
   50|     <Info size={18} strokeWidth={2} aria-hidden="true" />
   51|   </button>
   52|   {#if open}
   53|     <div class="pop" role="dialog" aria-label={label} bind:this={pop} use:toBody
   54|       style:top="{pos.top}px" style:max-height="{pos.max}px" style:left={align === 'end' ? 'auto' : `${pos.left}px`} style:right={align === 'end' ? `${pos.right}px` : 'auto'}>
   55|       {@render children?.()}
   56|     </div>
   57|   {/if}
   58| </span>
   59| 
   60| <style>
   61|   .info { position: relative; display: inline-flex; }
   62|   button {
   63|     width: 28px;
   64|     height: 28px;
   65|     display: inline-flex;
   66|     align-items: center;
   67|     justify-content: center;
   68|     padding: 0;
   69|     border: none;
   70|     border-radius: 999px;
   71|     background: transparent;
   72|     color: rgba(0, 0, 0, 0.45);
   73|     cursor: pointer;
   74|   }
   75|   button:hover { color: #000; background: rgba(0, 0, 0, 0.06); }
   76|   button:focus-visible { outline: 2px solid #3876b7; outline-offset: 1px; }
   77|   .pop {
   78|     position: fixed;
   79|     width: 340px;
   80|     box-sizing: border-box;
   81|     overflow-y: auto;
   82|     overscroll-behavior: contain;
   83|     padding: 12px 14px;
   84|     border-radius: 12px;
   85|     background: rgba(255, 255, 255, 0.98);
   86|     border: 0.5px solid rgba(0, 0, 0, 0.2);
   87|     font-size: 12px;
   88|     line-height: 1.45;
   89|     color: rgba(0, 0, 0, 0.78);
   90|     z-index: 2147483647;
   91|     text-align: left;
   92|     font-weight: 400;
   93|     letter-spacing: 0;
   94|     text-transform: none;
   95|     font-family: 'Geist', -apple-system, sans-serif;
   96|   }
   97|   .pop :global(p) { margin: 0 0 8px; }
   98|   .pop :global(p:last-child) { margin-bottom: 0; }
   99|   .pop :global(strong) { color: #000; font-weight: 600; }
  100|   .pop :global(.fine) { font-size: 11px; color: rgba(0, 0, 0, 0.5); }
  101| </style>
```

## `src/lib/simulacra/KindChips.svelte`

```svelte
    1| <script lang="ts">
    2|   // The what-if suggestions: one row of chips, scrolled sideways (a vertical
    3|   // wheel scrolls it too, while it can go further that way); each edge fades
    4|   // while there's more past it. Chosen and run: tinted, a check. Chosen, not
    5|   // run yet: gray with a tint ring and its own glyph — queued for the next Rerun.
    6|   import { Check, MapPin, Newspaper, Vote } from 'lucide-svelte';
    7|   import type { Kind, WhatIf } from './schemas';
    8|   import { KIND_LABEL, reaches } from './whatif';
    9| 
   10|   interface Props {
   11|     whatIfs?: readonly WhatIf[];
   12|     /** Chosen what-if keys. */
   13|     selected?: readonly string[];
   14|     /** The what-ifs in the rerun on show. */
   15|     ran?: readonly string[];
   16|     /** An open group: the what-ifs that reach it stand out. */
   17|     slice?: string | null;
   18|     running?: boolean;
   19|     ontoggle?: (key: string) => void;
   20|   }
   21|   let { whatIfs = [], selected = [], ran = [], slice = null, running = false, ontoggle }: Props = $props();
   22| 
   23|   const KIND_ICON: Readonly<Record<Kind, typeof Vote>> = {
   24|     franchise: Vote,
   25|     population: MapPin,
   26|     issue: Newspaper,
   27|     candidate: Vote,
   28|   };
   29| 
   30|   let chipsEl = $state<HTMLElement | null>(null);
   31|   let chipsL = $state(false);
   32|   let chipsR = $state(false);
   33|   function chipEdges() {
   34|     if (!chipsEl) return;
   35|     chipsL = chipsEl.scrollLeft > 1;
   36|     chipsR = chipsEl.scrollWidth - chipsEl.scrollLeft - chipsEl.clientWidth > 1;
   37|   }
   38|   function chipRow(node: HTMLElement) {
   39|     const r = new ResizeObserver(chipEdges);
   40|     r.observe(node);
   41|     const wheel = (e: WheelEvent) => {
   42|       if (Math.abs(e.deltaY) <= Math.abs(e.deltaX)) return;
   43|       const max = node.scrollWidth - node.clientWidth;
   44|       if (max <= 0 || (e.deltaY < 0 && node.scrollLeft <= 0) || (e.deltaY > 0 && node.scrollLeft >= max - 1)) return;
   45|       e.preventDefault();
   46|       node.scrollLeft += e.deltaY;
   47|     };
   48|     node.addEventListener('wheel', wheel, { passive: false });
   49|     return {
   50|       destroy() {
   51|         r.disconnect();
   52|         node.removeEventListener('wheel', wheel);
   53|       },
   54|     };
   55|   }
   56|   // New chips (another year, a built what-if): measure the edges again.
   57|   $effect.pre(() => {
   58|     void whatIfs;
   59|     queueMicrotask(chipEdges);
   60|   });
   61| </script>
   62| 
   63| <div class="chips" class:l={chipsL} class:r={chipsR} bind:this={chipsEl} use:chipRow onscroll={chipEdges}>
   64|   {#each whatIfs as w (w.key)}
   65|     {@const on = selected.includes(w.key)}
   66|     {@const pending = on && !ran.includes(w.key)}
   67|     {@const Icon = KIND_ICON[w.kind]}
   68|     <button type="button" class="chip" class:on class:pending class:dim={!reaches(w, slice)} aria-pressed={on} disabled={running}
   69|       title="{KIND_LABEL[w.kind]}: {w.detail}{pending ? ' (not run yet)' : ''}" onclick={() => ontoggle?.(w.key)}>
   70|       {#if on && !pending}<Check size={14} strokeWidth={2.4} aria-hidden="true" />{:else}<Icon size={14} strokeWidth={2} aria-hidden="true" />{/if}
   71|       {w.label}
   72|     </button>
   73|   {/each}
   74| </div>
   75| 
   76| <style>
   77|   /* One row, scrolled sideways, no scrollbar. Each edge fades (a 40px band,
   78|      easing in via @property) only while there's more past it. The 4px of
   79|      padding top and bottom keeps a chip's focus ring inside the clip. */
   80|   @property --fl { syntax: '<length>'; inherits: false; initial-value: 0px; }
   81|   @property --fr { syntax: '<length>'; inherits: false; initial-value: 0px; }
   82|   .chips {
   83|     --band: 40px;
   84|     display: flex;
   85|     gap: 8px;
   86|     min-width: 0;
   87|     margin: -4px 0;
   88|     padding: 4px 0;
   89|     overflow-x: auto;
   90|     overflow-y: hidden;
   91|     overscroll-behavior-x: contain;
   92|     scrollbar-width: none;
   93|     -webkit-mask-image: linear-gradient(to right, transparent, #000 var(--fl), #000 calc(100% - var(--fr)), transparent);
   94|     mask-image: linear-gradient(to right, transparent, #000 var(--fl), #000 calc(100% - var(--fr)), transparent);
   95|     transition: --fl 0.25s ease, --fr 0.25s ease;
   96|   }
   97|   .chips::-webkit-scrollbar { display: none; }
   98|   .chips.l { --fl: var(--band); }
   99|   .chips.r { --fr: var(--band); }
  100|   .chips .chip { flex: none; }
  101|   /* The what-ifs, in the button hierarchy (filled > tinted > gray): at
  102|      rest gray (systemGray6), label text, glyphs in the tint; hover rings
  103|      it in the tint at 20%; a press dims it to systemGray5. Chosen is *tinted*, not filled: the tint at 15% over
  104|      white (#d9ebff), the label in the deeper blue (#0062cc, 4.8:1) and the
  105|      check carrying the state, with a faint tint ring to hold the shape on
  106|      the page's grey. Filled blue is Rerun's alone. */
  107|   .chip {
  108|     display: inline-flex;
  109|     align-items: center;
  110|     gap: 6px;
  111|     height: var(--control-h);
  112|     padding: 0 14px 0 12px;
  113|     border: none;
  114|     border-radius: 999px;
  115|     background: var(--fill);
  116|     color: var(--label);
  117|     font: inherit;
  118|     font-size: 13px;
  119|     font-weight: 500;
  120|     white-space: nowrap;
  121|     cursor: pointer;
  122|     transition: background-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s cubic-bezier(0.2, 0.9, 0.3, 1.3), opacity 0.15s ease, color 0.12s ease;
  123|   }
  124|   .chip :global(svg) { color: var(--tint); flex: none; transition: color 0.18s ease; }
  125|   /* Hover (pointers only): a 1px ring of the tint at 20%, drawn inside the
  126|      capsule so nothing shifts. */
  127|   @media (hover: hover) {
  128|     .chip:hover:not(:disabled):not(.on) { box-shadow: inset 0 0 0 1px rgba(0, 122, 255, 0.2); }
  129|   }
  130|   .chip:active:not(:disabled):not(.on) { background: var(--fill-press); transform: scale(0.97); box-shadow: none; }
  131|   .chip.on { background: #d9ebff; color: #0062cc; box-shadow: inset 0 0 0 1px rgba(0, 122, 255, 0.28); }
  132|   .chip.on :global(svg) { color: var(--tint); }
  133|   /* Chosen, not run yet: still the rest gray, ringed in the tint. */
  134|   .chip.on.pending { background: var(--fill); box-shadow: inset 0 0 0 1.5px var(--tint); }
  135|   .chip.dim { opacity: 0.45; }
  136|   .chip:disabled { cursor: default; }
  137|   .chip:focus-visible { outline: 2px solid #3876b7; outline-offset: 2px; }
  138|   /* Under the Rerun view's invert the glyphs are turned back (WhatIf.svelte). */
  139|   :global(.sa.dark) .chip:not(.on) :global(svg) { filter: invert(1) hue-rotate(180deg) saturate(66.7%); }
  140|   @media (prefers-reduced-motion: reduce) {
  141|     .chip { transition: none; }
  142|     .chips { transition: none; }
  143|   }
  144| </style>
```
