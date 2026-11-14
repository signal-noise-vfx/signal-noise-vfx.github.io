// Signal/Noise banners: try each official image in order, fall back to generated art.
(function () {
  function rng(seed) { var h = 2166136261; for (var i = 0; i < seed.length; i++) { h ^= seed.charCodeAt(i); h = Math.imul(h, 16777619); } return function () { h ^= h << 13; h ^= h >>> 17; h ^= h << 5; return ((h >>> 0) % 10000) / 10000; }; }
  var PAL = [["#ff3b30", "#ff9f0a", "#1a0608"], ["#34d3ee", "#7c3aed", "#050a18"], ["#00e676", "#00b8d4", "#03140d"], ["#ff00c8", "#ffb020", "#14030f"], ["#2962ff", "#34d3ee", "#030616"], ["#ffe600", "#ff3b30", "#140f02"]];
  function art(box) {
    var label = box.getAttribute("data-label") || "Signal/Noise", r = rng(label);
    var c = document.createElement("canvas"), w = 1200, h = 460; c.width = w; c.height = h;
    var x = c.getContext("2d"), p = PAL[Math.floor(r() * PAL.length)];
    x.fillStyle = p[2]; x.fillRect(0, 0, w, h);
    for (var i = 0; i < 3; i++) { // soft light blooms
      var gx = r() * w, gy = r() * h, g = x.createRadialGradient(gx, gy, 0, gx, gy, 260 + r() * 300);
      g.addColorStop(0, p[i % 2] + "aa"); g.addColorStop(1, p[i % 2] + "00"); x.fillStyle = g; x.fillRect(0, 0, w, h);
    }
    x.globalCompositeOperation = "lighter"; // light streaks
    var ang = (r() - 0.5) * 0.9;
    for (var k = 0; k < 26; k++) {
      var y0 = r() * h * 1.6 - h * 0.3, len = 300 + r() * 900, x0 = r() * w - 200;
      x.strokeStyle = p[k % 2] + (r() > 0.8 ? "cc" : "40"); x.lineWidth = r() > 0.85 ? 3 : 1;
      x.shadowColor = p[k % 2]; x.shadowBlur = 18;
      x.beginPath(); x.moveTo(x0, y0); x.lineTo(x0 + len, y0 + len * Math.tan(ang)); x.stroke();
    }
    x.shadowBlur = 0; x.globalCompositeOperation = "source-over";
    x.fillStyle = "rgba(255,255,255,.06)"; // dot grid
    for (var gx2 = 0; gx2 < w; gx2 += 24) for (var gy2 = 0; gy2 < h; gy2 += 24) x.fillRect(gx2, gy2, 1.5, 1.5);
    x.fillStyle = "rgba(0,0,0,.18)"; // scanlines
    for (var s = 0; s < h; s += 4) x.fillRect(0, s, w, 1);
    var im = x.getImageData(0, 0, w, h), d = im.data; // grain
    for (var q = 0; q < d.length; q += 4) { var n = (Math.random() - 0.5) * 22; d[q] += n; d[q + 1] += n; d[q + 2] += n; }
    x.putImageData(im, 0, 0);
    c.className = "art"; box.insertBefore(c, box.firstChild); box.classList.add("gen");
  }
  function load(box) {
    var list = (box.getAttribute("data-src") || "").split("|").filter(Boolean), cr = (box.getAttribute("data-credit") || "").split("|");
    var i = 0, img = box.querySelector("img"), tag = box.querySelector(".cr");
    function next() {
      if (i >= list.length) { if (img) img.remove(); if (tag) tag.remove(); art(box); return; }
      var u = list[i], who = cr[i] || cr[0] || ""; i++;
      var t = new Image(); t.referrerPolicy = "no-referrer";
      t.onload = function () { if (t.naturalWidth < 500) return next(); img.src = u; if (tag) tag.textContent = who ? "Image: " + who : ""; box.classList.add("ok"); };
      t.onerror = next; t.src = u;
    }
    next();
  }
  document.querySelectorAll(".banner[data-label]").forEach(load);
})();
