// The banner on every page: a cloth in the four site colours, lit dye on ink, in both themes. WebGL 1, no libraries.
// Each banner (site.css .banner) paints its CSS gradient first; the canvas stays transparent (opacity 0) until its first
// frame is drawn, then gets .on and fades in over a gradient of about the same brightness, so nothing flashes.
// data-seed picks the cloth (one per page group, the same on every visit). Every banner drifts slowly; with reduced motion,
// or data-still, it draws one frame and stops. A banner off screen or in a hidden tab does not draw.
(function () {
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var panels = document.querySelectorAll('canvas.cloth');
  for (var i = 0; i < panels.length; i++) mount(panels[i]);

  function mount(canvas) {
  var still = reduce || canvas.hasAttribute('data-still');
  var gl = canvas.getContext('webgl', { antialias: false, alpha: true, premultipliedAlpha: true, preserveDrawingBuffer: false });
  if (!gl) { canvas.remove(); return; } // the page background stands in

  var vs = 'attribute vec2 p; void main(){ gl_Position = vec4(p, 0.0, 1.0); }';
  var fs = [
    'precision highp float;',
    'uniform vec2 r; uniform float t; uniform vec2 m; uniform float seed; uniform float quiet;',
    'float hash(float n) { return fract(sin(n) * 43758.5453); }',
    // smooth value noise, for the slow warp that keeps the folds from looking like ruled lines
    'float noise(vec2 x) { vec2 i = floor(x), f = fract(x); f = f * f * (3.0 - 2.0 * f); float n = i.x + i.y * 57.0;',
    '  return mix(mix(hash(n), hash(n + 1.0), f.x), mix(hash(n + 57.0), hash(n + 58.0), f.x), f.y); }',
    // the drape: three folds at nearby angles, long to short, each a rounded crest over a tighter trough, on a warped plane
    'float drape(vec2 p) {',
    '  vec2 q = p + 0.45 * vec2(noise(p * 0.7 + seed * 3.1 + t * 0.012), noise(p * 0.7 - seed * 1.7 + 4.3 - t * 0.012)) - 0.22;',
    '  float a = 0.45 + hash(seed) * 0.9, h = 0.0;',
    '  for (int i = 0; i < 3; i++) {',
    '    float fi = float(i);',
    '    float ang = a + (hash(seed + fi * 7.3) - 0.5) * 0.7;',
    '    vec2 d = vec2(cos(ang), sin(ang));',
    '    float f = 2.3 * pow(1.7, fi), amp = pow(0.5, fi);',
    '    float u = dot(q, d) * f + t * (0.035 + 0.025 * fi) * (mod(fi, 2.0) * 2.0 - 1.0) + hash(seed + fi) * 6.283;',
    '    h += amp * (sin(u) - 0.28 * cos(2.0 * u));',
    '  }',
    '  return h;',
    '}',
    'void main() {',
    '  vec2 uv = gl_FragCoord.xy / r; vec2 p = uv * vec2(r.x / r.y, 1.0) * 1.15;',
    // the surface normal from the height field: the light, the sheen and the creases all come from it
    '  float e = 1.0 / r.y, h = drape(p);',
    '  float hx = drape(p + vec2(e, 0.0)) - h, hy = drape(p + vec2(0.0, e)) - h;',
    '  vec3 n = normalize(vec3(-hx / e * 0.2, -hy / e * 0.2, 1.0));',
    // light from across the main fold, raking low, so each fold has a lit face and a shaded one
    '  float a = 0.45 + hash(seed) * 0.9;',
    '  vec3 L = normalize(vec3(cos(a) + (m.x - 0.5) * 0.3, sin(a) + (m.y - 0.5) * 0.2, 0.85));',
    '  vec3 V = vec3(0.0, 0.0, 1.0), H = normalize(L + V);',
    '  float diff = clamp((dot(n, L) + 0.2) / 1.2, 0.0, 1.0);',
    '  float spec = pow(max(dot(n, H), 0.0), 36.0);',
    // satin: a broad soft highlight where the cloth turns away from the eye
    '  float sheen = pow(1.0 - max(dot(n, V), 0.0), 2.2);',
    '  float crease = 0.35 + 0.65 * smoothstep(-1.6, 0.9, h);',
    // dye: emerald in the folds, sapphire across the drape, a little gold where it rises highest
    '  vec3 emerald = vec3(0.01, 0.50, 0.38), sapphire = vec3(0.26, 0.50, 0.78), gold = vec3(0.78, 0.70, 0.42);',
    '  float tone = clamp(0.5 + 0.32 * h + 0.25 * (uv.x - 0.5), 0.0, 1.0);',
    '  vec3 dye = mix(emerald, sapphire, smoothstep(0.15, 0.7, tone + 0.25 * (hash(seed * 2.0) - 0.5)));',
    '  dye = mix(dye, gold, smoothstep(0.86, 1.0, tone) * 0.35);',
    '  vec3 ink = vec3(0.035, 0.038, 0.045);',
    '  vec3 c = ink + dye * (0.04 + 1.1 * pow(diff, 1.8)) * crease;',
    '  c += vec3(0.82, 0.88, 0.94) * spec * 0.2 * crease + dye * sheen * 0.32;',
    // a soft shoulder on the brightest light, so a highlight glows instead of clipping to white
    '  c = c / (1.0 + 0.55 * max(c.r, max(c.g, c.b) - 0.55));',
    // vignette, and a quieter left side where the headline sits
    '  float vig = smoothstep(1.5, 0.25, length((uv - vec2(0.62, 0.55)) * vec2(1.0, 1.3)));',
    '  float hush = 1.0 - smoothstep(0.6, 0.0, uv.x) * 0.5 * quiet;',
    '  c = mix(ink, c, (0.4 + 0.6 * vig) * hush);',
    // dither below one 8-bit step, so the long gradients never band
    '  c += (hash(dot(gl_FragCoord.xy, vec2(12.9898, 78.233))) - 0.5) / 255.0;',
    '  gl_FragColor = vec4(c, 1.0);',
    '}'
  ].join('\n');

  function sh(type, src) { var s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) { console.error('hero shader:', gl.getShaderInfoLog(s)); canvas.remove(); throw new Error('shader'); } return s; }
  var prog = gl.createProgram();
  gl.attachShader(prog, sh(gl.VERTEX_SHADER, vs)); gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, fs));
  gl.linkProgram(prog);
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) { console.error('hero link:', gl.getProgramInfoLog(prog)); canvas.remove(); return; }
  gl.useProgram(prog);
  var buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, 1,1]), gl.STATIC_DRAW);
  var loc = gl.getAttribLocation(prog, 'p'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
  var uR = gl.getUniformLocation(prog, 'r'), uT = gl.getUniformLocation(prog, 't'), uM = gl.getUniformLocation(prog, 'm');
  gl.uniform1f(gl.getUniformLocation(prog, 'seed'), parseFloat(canvas.getAttribute('data-seed')) || 0.013);
  gl.uniform1f(gl.getUniformLocation(prog, 'quiet'), canvas.hasAttribute('data-quiet') ? 1.0 : 0.0);

  var mx = 0.5, my = 0.5, tx = 0.5, ty = 0.5;
  window.addEventListener('pointermove', function (e) { tx = e.clientX / window.innerWidth; ty = 1 - e.clientY / window.innerHeight; }, { passive: true });

  function size() {
    // full resolution: a still frame up to 2x, the moving one up to 1.5x to keep the fan quiet
    var scale = Math.min(window.devicePixelRatio || 1, still ? 2 : 1.5);
    canvas.width = Math.max(1, Math.floor(canvas.clientWidth * scale)); canvas.height = Math.max(1, Math.floor(canvas.clientHeight * scale));
    gl.viewport(0, 0, canvas.width, canvas.height);
  }
  var start = performance.now(), visible = true, raf = 0, onscreen = true, shown = false;
  if ('IntersectionObserver' in window) { new IntersectionObserver(function (es) { onscreen = es[0].isIntersecting; if (onscreen && !still) { cancelAnimationFrame(raf); raf = requestAnimationFrame(frame); } }, { rootMargin: '80px' }).observe(canvas); }
  function frame(now) {
    mx += (tx - mx) * 0.015; my += (ty - my) * 0.015;
    gl.uniform2f(uR, canvas.width, canvas.height); gl.uniform1f(uT, (now - start) / 1000 + 40.0); gl.uniform2f(uM, mx, my);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    // the first frame is in the buffer: show the canvas from the next paint
    if (!shown) { shown = true; canvas.classList.add('on'); }
    if (!still && visible && onscreen) raf = requestAnimationFrame(frame);
  }
  size(); window.addEventListener('resize', function () { size(); if (still) frame(performance.now()); });
  document.addEventListener('visibilitychange', function () { visible = !document.hidden; if (visible && !still) { cancelAnimationFrame(raf); raf = requestAnimationFrame(frame); } });
  raf = requestAnimationFrame(frame);
  }
})();
