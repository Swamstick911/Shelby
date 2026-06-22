/* ============================================================
   Shelby — Flashlight in the Dark
   The real Sprig 3D model (sprig.glb, the same asset the Hack Club
   site uses) running the live firmware on its screen, lit in the
   dark by a torch that follows the cursor.
   ============================================================ */
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { W, H, createState, drawScreen, press, RENDER } from "./screens.js";
import { loadEmulator } from "./emu.js";

/* ---------- the flashlight ---------- */
const dark = document.querySelector(".dark");
const torch = document.querySelector(".torch");
let mx = innerWidth / 2, my = innerHeight * 0.38, tx = mx, ty = my;
const setLight = (x, y) => { mx = x; my = y; };
window.addEventListener("pointermove", (e) => setLight(e.clientX, e.clientY));
window.addEventListener("pointerdown", (e) => setLight(e.clientX, e.clientY));
(function lightLoop() {
  tx += (mx - tx) * 0.35; ty += (my - ty) * 0.35;
  dark.style.setProperty("--mx", mx + "px"); dark.style.setProperty("--my", my + "px");
  torch.style.setProperty("--mx", tx + "px"); torch.style.setProperty("--my", ty + "px");
  requestAnimationFrame(lightLoop);
})();

/* ---------- live firmware buffers ---------- */
const state = createState();
let t = 0;
function makeBuffer() {
  const c = document.createElement("canvas"); c.width = W; c.height = H;
  const g = c.getContext("2d"); g.imageSmoothingEnabled = false;
  return { c, g };
}
function blit(canvas, buf) {
  const ctx = canvas.getContext("2d"); ctx.imageSmoothingEnabled = false;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(buf, 0, 0, W, H, 0, 0, canvas.width, canvas.height);
}
// the screen texture for the 3D model
const screenBuf = makeBuffer();
const screenTex = new THREE.CanvasTexture(screenBuf.c);
screenTex.magFilter = THREE.NearestFilter; screenTex.minFilter = THREE.NearestFilter;
screenTex.colorSpace = THREE.SRGBColorSpace; screenTex.flipY = false;

// the scattered single screen app canvases (CSS LCD bezels)
const statics = [];
document.querySelectorAll("canvas[data-screen]").forEach((canvas) =>
  statics.push({ canvas, buf: makeBuffer(), name: canvas.dataset.screen }));

/* ---------- the real firmware emulator (falls back to the JS renderer) ---------- */
let emu = null;
let thumbsReady = false;
function paintThumb(s, src) {
  const ctx = s.canvas.getContext("2d");
  ctx.imageSmoothingEnabled = false;
  ctx.clearRect(0, 0, s.canvas.width, s.canvas.height);
  ctx.drawImage(src, 0, 0, W, H, 0, 0, s.canvas.width, s.canvas.height);
}
function captureThumbs() {
  // snapshot each real firmware app screen once into its tile, then leave the
  // device back on the clock (this runs synchronously between render frames)
  for (const s of statics) {
    try { emu.showScreen(s.name); paintThumb(s, emu.screen); } catch (e) {}
  }
  try { emu.showScreen("clock"); } catch (e) {}   // leave the device on the clock
  thumbsReady = true;
}
loadEmulator()
  .then((e) => { emu = e; console.log("Shelby emulator running on the device screen."); captureThumbs(); })
  .catch((err) => console.warn("emulator unavailable, using JS renderer:", err));
// keep the clock tile live whenever the device itself is showing the clock
setInterval(() => {
  if (!emu || !thumbsReady) return;
  const c = statics.find((s) => s.name === "clock");
  if (c && emu.getView && emu.getView() === "Clock") paintThumb(c, emu.screen);
}, 1000);

/* ---------- input ---------- */
const DEVICE_KEYS = new Set(["W", "A", "S", "D", "I", "J", "K", "L"]);
window.addEventListener("keydown", (e) => {
  const k = e.key.toUpperCase();
  if (!DEVICE_KEYS.has(k)) return;
  const tag = (document.activeElement && document.activeElement.tagName) || "";
  if (tag === "INPUT" || tag === "TEXTAREA") return;
  e.preventDefault();
  if (emu) emu.setKey(k, true); else press(state, k);
});
window.addEventListener("keyup", (e) => {
  const k = e.key.toUpperCase();
  if (!DEVICE_KEYS.has(k)) return;
  if (emu) emu.setKey(k, false);
});

/* ---------- the real 3D Sprig ---------- */
const glCanvas = document.getElementById("sprig3d");
const renderer = new THREE.WebGLRenderer({ canvas: glCanvas, alpha: true, antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.2;

const scene = new THREE.Scene();
// image based lighting so the metallic / glossy board materials are not black;
// loaded dynamically so a failed fetch can't break the whole page
(async () => {
  try {
    const { RoomEnvironment } = await import("three/addons/environments/RoomEnvironment.js");
    const pmrem = new THREE.PMREMGenerator(renderer);
    scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  } catch (e) {
    console.warn("RoomEnvironment unavailable; using fallback lighting", e);
    scene.add(new THREE.HemisphereLight(0xe8eeff, 0x20262e, 1.6));
  }
})();

const camera = new THREE.PerspectiveCamera(34, 1, 0.1, 100);
camera.position.set(0, 0, 4.2);

scene.add(new THREE.AmbientLight(0xb9c6d6, 0.8));
const key = new THREE.DirectionalLight(0xfff3df, 2.4); key.position.set(2.5, 3.5, 4); scene.add(key);
const fill = new THREE.DirectionalLight(0x6f8cff, 1.0); fill.position.set(-3, -1, 2); scene.add(fill);
const glow = new THREE.PointLight(0x8fd14f, 6, 6); glow.position.set(0, 0, 1.2); scene.add(glow);

const pivot = new THREE.Group();
scene.add(pivot);

function sizeRenderer() {
  const w = glCanvas.clientWidth || 760, h = glCanvas.clientHeight || 460;
  renderer.setSize(w, h, false);
  camera.aspect = w / h; camera.updateProjectionMatrix();
}

let screenMesh = null;
const loader = new GLTFLoader();
loader.load(
  "assets/sprig.glb",
  (gltf) => {
    const model = gltf.scene;

    // scale to a comfortable size (centering happens after we orient it)
    const box = new THREE.Box3().setFromObject(model);
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z);
    model.scale.setScalar(3.0 / maxDim);

    // the lit screen uses the "Glow Glass" material in this model
    let glowMesh = null, named = null;
    model.traverse((o) => {
      if (!o.isMesh) return;
      const m = (o.material && o.material.name || "").toLowerCase();
      if (m === "glow glass") glowMesh = o;
      if (!named && /screen|lcd|display/.test(o.name.toLowerCase() + " " + m)) named = o;
    });
    screenMesh = glowMesh || named;
    if (screenMesh) screenMesh.material = new THREE.MeshBasicMaterial({ map: screenTex, toneMapped: false });

    // the board lies flat in the file; stand it up so the screen faces us
    model.rotation.x = Math.PI / 2;
    const orient = new THREE.Group();
    orient.rotation.z = Math.PI / 2;
    orient.add(model);
    // roll 180 about the view axis so the screen reads the right way up
    const mount = new THREE.Group();
    mount.rotation.z = Math.PI;
    mount.add(orient);
    // recenter the fully oriented object on the pivot
    const obox = new THREE.Box3().setFromObject(mount);
    mount.position.sub(obox.getCenter(new THREE.Vector3()));
    pivot.add(mount);
    sizeRenderer();
    t = 0; state.t = 0;   // restart the boot splash now that the screen is visible
  },
  undefined,
  (err) => console.error("SPRIG_LOAD_ERROR", err)
);

/* ---------- drag to rotate (with momentum, eases back to front) ---------- */
let rotY = 0, rotX = -0.12, velY = 0, velX = 0;
let down = false, lastX = 0, lastY = 0;
glCanvas.style.cursor = "grab";
glCanvas.addEventListener("pointerdown", (e) => {
  down = true; lastX = e.clientX; lastY = e.clientY; glCanvas.setPointerCapture(e.pointerId);
  glCanvas.style.cursor = "grabbing";
});
glCanvas.addEventListener("pointermove", (e) => {
  if (!down) return;
  const dx = e.clientX - lastX, dy = e.clientY - lastY; lastX = e.clientX; lastY = e.clientY;
  velY = dx * 0.008; velX = dy * 0.008;
  rotY += velY; rotX = THREE.MathUtils.clamp(rotX + velX, -0.8, 0.8);
});
glCanvas.addEventListener("pointerup", (e) => { down = false; glCanvas.style.cursor = "grab"; });
addEventListener("resize", sizeRenderer);

/* ---------- render loop ---------- */
let last = 0;
function frame(now) {
  if (now - last > 66) {
    last = now; t += 1; state.t = t;
    if (emu) {
      try { emu.step(); } catch (e) { /* keep rendering */ }
      screenBuf.g.drawImage(emu.screen, 0, 0);   // real firmware framebuffer
    } else {
      drawScreen(screenBuf.g, state);            // fallback JS renderer
    }
    screenTex.needsUpdate = true;
    if (!thumbsReady) {   // until the real-firmware tiles are ready, use the JS renderer
      for (const s of statics) {
        (RENDER[s.name] || RENDER.clock)(s.buf.g, { view: s.name, t, taskSel: 0, menuSel: 0 });
        blit(s.canvas, s.buf.c);
      }
    }
  }

  if (!down) {
    rotY += velY; rotX = THREE.MathUtils.clamp(rotX + velX, -0.8, 0.8);
    velY *= 0.93; velX *= 0.9;
    if (Math.abs(velY) < 0.004) {                       // settle to a gentle front-facing sway
      const restY = Math.sin(now * 0.0003) * 0.2;
      rotY += (restY - rotY) * 0.02;
      rotX += (-0.12 - rotX) * 0.02;
    }
  }
  pivot.rotation.y = rotY; pivot.rotation.x = rotX;

  renderer.render(scene, camera);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
