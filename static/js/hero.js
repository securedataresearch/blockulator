// The banner on every page: a cloth in the four site colours, lit dye on ink, in both themes. WebGL 1, no libraries.
// Each banner (site.css .banner) paints its CSS gradient first; the canvas stays transparent (opacity 0) until its first
// frame is drawn, then gets .on and fades in over a gradient of about the same brightness, so nothing flashes.
// data-seed picks the cloth (one per page group, the same on every visit); data-still draws one frame and stops.
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
    'precision mediump float;',
    'uniform vec2 r; uniform float t; uniform vec2 m; uniform float seed; uniform float quiet;',
    'void main(){',
    '  vec2 uv = gl_FragCoord.xy / r; vec2 p = uv; p.x *= r.x / r.y;',
    // one wave, set at an angle, sliding across; angle, wavelength, lean, speed and dye come from the seed
    '  float h1 = fract(sin(seed * 12.9898) * 43758.5453);',
    '  float h2 = fract(sin(seed * 78.233) * 43758.5453);',
    '  float h3 = fract(sin(seed * 39.425) * 43758.5453);',
    '  float h4 = fract(sin(seed * 93.989) * 43758.5453);',
    '  float h5 = fract(sin(seed * 57.114) * 43758.5453);',
    '  float ang = 0.25 + h1 * 1.25;',
    '  vec2 dir = vec2(cos(ang), sin(ang));',
    '  float wl = 1.7 + h2 * 1.6;',
    '  float lean = 0.3 + h3 * 0.45;',
    '  float speed = (0.18 + h4 * 0.22) * (h5 > 0.5 ? 1.0 : -1.0);',
    '  float u = dot(p, dir) * wl - t * speed + seed;',
    // a slumped fold: a sine with a little second harmonic so the crest leans
    '  float fold  = sin(u) + lean * sin(2.0 * u + 1.0);',
    '  float slope = cos(u) + 2.0 * lean * cos(2.0 * u + 1.0);',
    '  float ph = fract((u - 0.9) / 6.2831853);',
    '  float lipd = ph * 34.0; float lip = exp(-lipd * lipd);',
    '  float shd = (ph - 0.07) * 14.0; float tuck = exp(-shd * shd);',
    '  float light = clamp(0.5 + 0.5 * slope + (m.x - 0.5) * 0.15, 0.0, 1.0);',
    '  light = light * (1.0 - 0.85 * tuck) + 0.6 * lip;',
    '  float sheen = pow(light, 10.0);',
    // the weave follows the surface and bunches where the slope is steep
    '  vec2 perp = vec2(-dir.y, dir.x);',
    '  float along  = dot(p, dir)  + fold * 0.10;',
    '  float across = dot(p, perp) + fold * 0.04;',
    '  float squeeze = 1.0 + 0.9 * max(-slope, 0.0);',
    '  float wu = fract(along * 16.0 * squeeze); float wv = fract(across * 16.0);',
    '  float lineU = smoothstep(0.30, 0.5, abs(wu - 0.5)); float lineV = smoothstep(0.30, 0.5, abs(wv - 0.5));',
    '  float weave = 0.22 * max(lineU, lineV) * (0.4 + 0.6 * light);',
    // dye: emerald in the troughs, sapphire on the crests, a little gold on the very top
    '  vec3 emerald = vec3(0.0, 0.41, 0.31); vec3 sapphire = vec3(0.25, 0.44, 0.63); vec3 gold = vec3(0.63, 0.60, 0.38);',
    '  float h = clamp(0.5 + 0.5 * fold / 1.4, 0.0, 1.0);',
    '  vec3 trough = mix(emerald, sapphire, h4);',
    '  vec3 crest  = mix(sapphire, mix(emerald, gold, h2), h5);',
    '  vec3 dye = mix(trough, crest, h);',
    '  dye = mix(dye, gold, smoothstep(0.85, 1.0, h) * (0.2 + 0.4 * h3));',
    '  float vig = smoothstep(1.45, 0.3, length(uv - vec2(0.6, 0.5)));',
    // a quieter left side, where the headline sits
    '  float hush = 1.0 - smoothstep(0.55, 0.0, uv.x) * 0.45 * quiet;',
    '  vec3 ink = vec3(0.045, 0.045, 0.05);',
    '  vec3 c = ink + dye * (0.05 + 0.95 * light) * (1.0 - weave) + vec3(0.85, 0.88, 0.9) * (sheen * 0.25 + lip * 0.18);',
    '  gl_FragColor = vec4(mix(ink, c, (0.3 + 0.7 * vig) * hush), 1.0);',
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
    var dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    // render at reduced resolution; the cloth is soft and it keeps the fan quiet
    var scale = 0.6 * dpr;
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
