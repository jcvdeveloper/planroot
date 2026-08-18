// Lightfall — fundo animado WebGL (sem dependências externas).
// Mantém a paleta "Petróleo Raiz" do site: streaks em teal sobre #0B2B2B.
// Renderiza num canvas fixo atrás de todo o conteúdo (#lightfall-bg).

const MAX_COLORS = 8;

const hexToRGB = (hex) => {
  const c = hex.replace("#", "").padEnd(6, "0");
  return [
    parseInt(c.slice(0, 2), 16) / 255,
    parseInt(c.slice(2, 4), 16) / 255,
    parseInt(c.slice(4, 6), 16) / 255,
  ];
};

const prepColors = (input) => {
  const base = (input && input.length ? input : ["#2DD4BF", "#5EEAD4", "#14b8a6"]).slice(0, MAX_COLORS);
  const count = base.length;
  const arr = [];
  for (let i = 0; i < MAX_COLORS; i++) arr.push(hexToRGB(base[Math.min(i, base.length - 1)]));
  const avg = [0, 0, 0];
  for (let i = 0; i < count; i++) {
    avg[0] += arr[i][0];
    avg[1] += arr[i][1];
    avg[2] += arr[i][2];
  }
  avg[0] /= count;
  avg[1] /= count;
  avg[2] /= count;
  return { arr, count, avg };
};

const vertex = `
attribute vec2 position;
attribute vec2 uv;
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = vec4(position, 0.0, 1.0);
}
`;

const fragment = `
precision highp float;

uniform vec3  iResolution;
uniform vec2  iMouse;
uniform float iTime;

uniform vec3  uColor0;
uniform vec3  uColor1;
uniform vec3  uColor2;
uniform vec3  uColor3;
uniform vec3  uColor4;
uniform vec3  uColor5;
uniform vec3  uColor6;
uniform vec3  uColor7;
uniform int   uColorCount;

uniform vec3  uBgColor;
uniform vec3  uMouseColor;
uniform float uSpeed;
uniform int   uStreakCount;
uniform float uStreakWidth;
uniform float uStreakLength;
uniform float uGlow;
uniform float uDensity;
uniform float uTwinkle;
uniform float uZoom;
uniform float uBgGlow;
uniform float uOpacity;
uniform float uMouseEnabled;
uniform float uMouseStrength;
uniform float uMouseRadius;

varying vec2 vUv;

vec3 palette(float h) {
  int count = uColorCount;
  if (count < 1) count = 1;
  int idx = int(floor(clamp(h, 0.0, 0.999999) * float(count)));
  if (idx <= 0) return uColor0;
  if (idx == 1) return uColor1;
  if (idx == 2) return uColor2;
  if (idx == 3) return uColor3;
  if (idx == 4) return uColor4;
  if (idx == 5) return uColor5;
  if (idx == 6) return uColor6;
  return uColor7;
}

vec3 tanhv(vec3 x) {
  vec3 e = exp(-2.0 * x);
  return (1.0 - e) / (1.0 + e);
}

vec2 sceneC(vec2 frag, vec2 r) {
  vec2 P = (frag + frag - r) / r.x;
  float z = 0.0;
  float d = 1e3;
  vec4 O = vec4(0.0);
  for (int k = 0; k < 39; k++) {
    if (d <= 1e-4) break;
    O = z * normalize(vec4(P, uZoom, 0.0)) - vec4(0.0, 4.0, 1.0, 0.0) / 4.5;
    d = 1.0 - sqrt(length(O * O));
    z += d;
  }
  return vec2(O.x, atan(O.z, O.y));
}

void mainImage(out vec4 o, vec2 C) {
  vec2 r = iResolution.xy;
  vec2 uv0 = (C + C - r) / r.x;
  float T = 0.1 * iTime * uSpeed + 9.0;
  float angRings = max(1.0, floor(6.28318530718 * max(uDensity, 0.05) + 0.5));
  vec2 Y = vec2(5e-3, 6.28318530718 / angRings);

  vec2 c0 = sceneC(C, r);
  vec2 cdx = sceneC(C + vec2(1.0, 0.0), r);
  vec2 cdy = sceneC(C + vec2(0.0, 1.0), r);
  vec2 dCx = cdx - c0;
  vec2 dCy = cdy - c0;
  dCx.y -= 6.28318530718 * floor(dCx.y / 6.28318530718 + 0.5);
  dCy.y -= 6.28318530718 * floor(dCy.y / 6.28318530718 + 0.5);
  vec2 fw = abs(dCx) + abs(dCy);
  C = c0;

  vec2 P = vec2(2.0, 1.0) * uv0 - (r / r.x) * vec2(0.0, 1.0);
  vec4 O = vec4(uBgColor * 90.0 * uBgGlow / (1e3 * dot(P, P) + 6.0), 0.0);

  float mGlow = 0.0;
  if (uMouseEnabled > 0.5) {
    vec2 mN = (iMouse + iMouse - r) / r.x;
    float md = length(uv0 - mN);
    mGlow = exp(-md * md / max(uMouseRadius * uMouseRadius, 1e-4)) * uMouseStrength;
    O.rgb += uMouseColor * mGlow * 0.25;
  }

  float zr = 5e-4 * uStreakWidth;
  vec2 rr = vec2(max(length(fw), 1e-5));
  float tail = 19.0 / max(uStreakLength, 0.05);

  for (int m = 0; m < 16; m++) {
    if (m >= uStreakCount) break;
    float jf = float(m) + 1.0;
    float ic = fract(sin(dot(vec2(jf, floor(C.x / Y.x + 0.5)), vec2(7.0, 11.0)) * 73.0));
    vec2 Pp = C - (T + T * ic) * vec2(0.0, 1.0);
    Pp -= floor(Pp / Y + 0.5) * Y;
    float h = fract(8663.0 * ic);
    vec3 col = palette(h);
    float weight = mix(1.5, 1.0 + sin(T + 7.0 * h + 4.0), uTwinkle);
    weight *= (1.0 + mGlow * 2.0);
    vec2 inner = vec2(length(max(Pp, vec2(-1.0, 0.0))), length(Pp) - zr) - zr;
    vec2 sm = vec2(1.0) - smoothstep(-rr, rr, inner);
    O.rgb += dot(sm, vec2(exp(tail * Pp.y), 3.0)) * col * weight;
    C.x += Y.x / 8.0;
  }

  vec3 colr = sqrt(tanhv(max(O.rgb * uGlow - vec3(0.04, 0.08, 0.02), 0.0)));
  o = vec4(colr, uOpacity);
}

void main() {
  vec4 color;
  mainImage(color, vUv * iResolution.xy);
  gl_FragColor = color;
}
`;

function compile(gl, type, src) {
  const sh = gl.createShader(type);
  gl.shaderSource(sh, src);
  gl.compileShader(sh);
  if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) {
    console.error("Lightfall shader:", gl.getShaderInfoLog(sh));
  }
  return sh;
}

function initLightfall(container, opts = {}) {
  const cfg = {
    colors: ["#2DD4BF", "#5EEAD4", "#14b8a6"],
    backgroundColor: "#0B2B2B",
    speed: 0.45,
    streakCount: 3,
    streakWidth: 1,
    streakLength: 1,
    glow: 0.9,
    density: 0.6,
    twinkle: 1,
    zoom: 3,
    backgroundGlow: 0.45,
    opacity: 1,
    mouseInteraction: true,
    mouseStrength: 0.45,
    mouseRadius: 1,
    mouseDampening: 0.15,
    ...opts,
  };

  const canvas = document.createElement("canvas");
  canvas.style.cssText = "width:100%;height:100%;display:block";
  container.appendChild(canvas);

  const gl =
    canvas.getContext("webgl", { alpha: true, antialias: true, premultipliedAlpha: false }) ||
    canvas.getContext("experimental-webgl");
  if (!gl) return; // sem WebGL: o site simplesmente fica no fundo sólido --bg

  const program = gl.createProgram();
  gl.attachShader(program, compile(gl, gl.VERTEX_SHADER, vertex));
  gl.attachShader(program, compile(gl, gl.FRAGMENT_SHADER, fragment));
  gl.linkProgram(program);
  gl.useProgram(program);

  // Triângulo de tela cheia (mesmo layout do Triangle do ogl: uv 0..2).
  const buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  // x, y, u, v
  gl.bufferData(
    gl.ARRAY_BUFFER,
    new Float32Array([-1, -1, 0, 0, 3, -1, 2, 0, -1, 3, 0, 2]),
    gl.STATIC_DRAW
  );
  const stride = 16;
  const aPos = gl.getAttribLocation(program, "position");
  const aUv = gl.getAttribLocation(program, "uv");
  gl.enableVertexAttribArray(aPos);
  gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, stride, 0);
  gl.enableVertexAttribArray(aUv);
  gl.vertexAttribPointer(aUv, 2, gl.FLOAT, false, stride, 8);

  const u = (n) => gl.getUniformLocation(program, n);
  const { arr, count, avg } = prepColors(cfg.colors);

  // Uniforms estáticos.
  for (let i = 0; i < MAX_COLORS; i++) gl.uniform3fv(u("uColor" + i), arr[i]);
  gl.uniform1i(u("uColorCount"), count);
  gl.uniform3fv(u("uBgColor"), hexToRGB(cfg.backgroundColor));
  gl.uniform3fv(u("uMouseColor"), avg);
  gl.uniform1f(u("uSpeed"), cfg.speed);
  gl.uniform1i(u("uStreakCount"), Math.max(1, Math.min(16, Math.round(cfg.streakCount))));
  gl.uniform1f(u("uStreakWidth"), cfg.streakWidth);
  gl.uniform1f(u("uStreakLength"), cfg.streakLength);
  gl.uniform1f(u("uGlow"), cfg.glow);
  gl.uniform1f(u("uDensity"), cfg.density);
  gl.uniform1f(u("uTwinkle"), cfg.twinkle);
  gl.uniform1f(u("uZoom"), cfg.zoom);
  gl.uniform1f(u("uBgGlow"), cfg.backgroundGlow);
  gl.uniform1f(u("uOpacity"), cfg.opacity);
  gl.uniform1f(u("uMouseEnabled"), cfg.mouseInteraction ? 1 : 0);
  gl.uniform1f(u("uMouseStrength"), cfg.mouseStrength);
  gl.uniform1f(u("uMouseRadius"), cfg.mouseRadius);

  const uRes = u("iResolution");
  const uMouse = u("iMouse");
  const uTime = u("iTime");

  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const resize = () => {
    const rect = container.getBoundingClientRect();
    const w = Math.max(1, Math.round((rect.width || window.innerWidth) * dpr));
    const h = Math.max(1, Math.round((rect.height || window.innerHeight) * dpr));
    canvas.width = w;
    canvas.height = h;
    gl.viewport(0, 0, w, h);
    gl.uniform3f(uRes, w, h, 1);
  };
  resize();
  new ResizeObserver(resize).observe(container);
  window.addEventListener("resize", resize);

  const mouseTarget = [0, 0];
  const mouseCur = [0, 0];
  if (cfg.mouseInteraction) {
    window.addEventListener("pointermove", (e) => {
      const rect = canvas.getBoundingClientRect();
      mouseTarget[0] = (e.clientX - rect.left) * dpr;
      mouseTarget[1] = (rect.height - (e.clientY - rect.top)) * dpr;
      if (cfg.mouseDampening <= 0) {
        mouseCur[0] = mouseTarget[0];
        mouseCur[1] = mouseTarget[1];
      }
    });
  }

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let last = 0;
  const loop = (t) => {
    if (!reduceMotion) requestAnimationFrame(loop);
    gl.uniform1f(uTime, reduceMotion ? 8.0 : t * 0.001);
    if (cfg.mouseDampening > 0) {
      if (!last) last = t;
      const dt = (t - last) / 1000;
      last = t;
      let factor = 1 - Math.exp(-dt / Math.max(1e-4, cfg.mouseDampening));
      if (factor > 1) factor = 1;
      mouseCur[0] += (mouseTarget[0] - mouseCur[0]) * factor;
      mouseCur[1] += (mouseTarget[1] - mouseCur[1]) * factor;
    }
    gl.uniform2f(uMouse, mouseCur[0], mouseCur[1]);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  };
  requestAnimationFrame(loop);
}

const mount = document.getElementById("lightfall-bg");
if (mount) initLightfall(mount);
