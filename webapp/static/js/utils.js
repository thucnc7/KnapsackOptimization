// Common utilities for the Knapsack visualizer webapp.

const Utils = {
  async fetchJson(url, opts) {
    const resp = await fetch(url, opts);
    if (!resp.ok) {
      const body = await resp.text().catch(() => '');
      throw new Error(`HTTP ${resp.status} ${resp.statusText} — ${body}`);
    }
    return resp.json();
  },

  async postJson(url, payload) {
    return Utils.fetchJson(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload || {}),
    });
  },

  el(tag, attrs = {}, children = []) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === 'class') node.className = v;
      else if (k === 'html') node.innerHTML = v;
      else if (k.startsWith('on') && typeof v === 'function') node.addEventListener(k.slice(2).toLowerCase(), v);
      else node.setAttribute(k, v);
    }
    for (const child of [].concat(children)) {
      if (child == null) continue;
      node.append(child instanceof Node ? child : document.createTextNode(String(child)));
    }
    return node;
  },

  fmt(v, digits = 4) {
    if (v == null || isNaN(v)) return '—';
    if (typeof v !== 'number') return String(v);
    if (Math.abs(v) >= 1000) return v.toLocaleString('en-US', { maximumFractionDigits: 2 });
    return v.toFixed(digits).replace(/\.?0+$/, '');
  },

  pct(v) {
    if (v == null) return '—';
    return `${(v * 100).toFixed(1)}%`;
  },

  destroyChart(key) {
    if (Utils._charts[key]) {
      Utils._charts[key].destroy();
      delete Utils._charts[key];
    }
  },

  chart(canvasId, config) {
    Utils.destroyChart(canvasId);
    const ctx = document.getElementById(canvasId).getContext('2d');
    Chart.defaults.color = '#8b96a3';
    Chart.defaults.borderColor = '#2a3441';
    Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    Utils._charts[canvasId] = new Chart(ctx, config);
    return Utils._charts[canvasId];
  },

  palette: ['#4f9eff', '#a371f7', '#3fb950', '#d29922', '#f85149', '#76b8ff', '#fdac54', '#e83e8c', '#20c997', '#6e7681'],

  algorithmColor(name) {
    const idx = (Utils._algoIndex.indexOf(name) + 1) || (Utils._algoIndex.push(name) && Utils._algoIndex.indexOf(name) + 1);
    return Utils.palette[(idx - 1) % Utils.palette.length];
  },

  _charts: {},
  _algoIndex: [],

  capacityBar(container, used, capacity) {
    const el = (typeof container === 'string') ? document.getElementById(container) : container;
    el.innerHTML = '';
    const ratio = capacity > 0 ? used / capacity : 0;
    const pct = Math.min(100, ratio * 100);
    const overflow = ratio > 1;
    const bar = Utils.el('div', { class: 'cap-bar' }, [
      Utils.el('div', { class: 'bar' }, [
        Utils.el('div', { class: 'bar-fill' + (overflow ? ' overflow' : ''), style: `width:${pct}%` }),
      ]),
      Utils.el('div', { class: 'label' }, `${Utils.fmt(used, 2)} / ${Utils.fmt(capacity, 2)} (${pct.toFixed(1)}%)`),
    ]);
    el.appendChild(bar);
  },

  startTimer(targetId, prefix = '⏱') {
    Utils.stopTimer(targetId);
    const target = document.getElementById(targetId);
    if (!target) return;
    const start = performance.now();
    target.innerHTML = `<span class="live-timer">${prefix} 0.0s</span>`;
    const handle = setInterval(() => {
      const sec = (performance.now() - start) / 1000;
      const span = target.querySelector('.live-timer');
      if (span) span.textContent = `${prefix} ${sec.toFixed(1)}s`;
    }, 100);
    Utils._timers[targetId] = handle;
    return handle;
  },

  stopTimer(targetId) {
    if (Utils._timers[targetId]) {
      clearInterval(Utils._timers[targetId]);
      delete Utils._timers[targetId];
    }
    const target = document.getElementById(targetId);
    if (target) target.innerHTML = '';
  },

  progressBar(percent, klass = '', label = null) {
    const cls = klass ? `progress-fill ${klass}` : 'progress-fill';
    const pct = Math.max(0, Math.min(100, percent));
    return Utils.el('div', { class: 'progress' }, [
      Utils.el('div', { class: cls, style: `width:${pct}%` }),
      Utils.el('div', { class: 'progress-text' }, label || `${pct.toFixed(1)}%`),
    ]);
  },

  showRunning(containerId, algorithm, timeoutSec, statusText = 'Đang thực thi…') {
    const root = (typeof containerId === 'string') ? document.getElementById(containerId) : containerId;
    if (!root) return;
    root.innerHTML = '';
    const banner = Utils.el('div', { class: 'running-banner', id: '__running_banner' }, [
      Utils.el('div', { class: 'spinner' }),
      Utils.el('div', { class: 'info' }, [
        Utils.el('div', { class: 'algo-name' }, `▶ ${algorithm}`),
        Utils.el('div', { class: 'status-text', id: '__running_status' }, statusText),
      ]),
      Utils.el('div', {}, [
        Utils.el('div', { class: 'big-timer', id: '__running_timer' }, '0.0s'),
        Utils.el('div', { class: 'timer-label' }, `budget ${timeoutSec}s`),
      ]),
      Utils.el('div', { class: 'timeout-bar' }, [
        Utils.el('div', { class: 'fill', id: '__running_fill', style: 'width:0%' }),
      ]),
    ]);
    root.appendChild(banner);

    const start = performance.now();
    const handle = setInterval(() => {
      const sec = (performance.now() - start) / 1000;
      const timer = document.getElementById('__running_timer');
      const fill = document.getElementById('__running_fill');
      if (!timer || !fill) { clearInterval(handle); return; }
      timer.textContent = sec.toFixed(1) + 's';
      const pct = Math.min(100, (sec / timeoutSec) * 100);
      fill.style.width = pct + '%';
      if (pct > 80) fill.classList.add('warn');
    }, 100);
    Utils._timers['__running_' + containerId] = handle;
  },

  hideRunning(containerId) {
    const key = '__running_' + containerId;
    if (Utils._timers[key]) {
      clearInterval(Utils._timers[key]);
      delete Utils._timers[key];
    }
  },

  _timers: {},

  async streamNdjson(url, opts, onEvent) {
    const resp = await fetch(url, opts);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buf = '';
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      let idx;
      while ((idx = buf.indexOf('\n')) >= 0) {
        const line = buf.slice(0, idx).trim();
        buf = buf.slice(idx + 1);
        if (!line) continue;
        try { onEvent(JSON.parse(line)); } catch (e) { console.error('bad ndjson', line, e); }
      }
    }
    if (buf.trim()) try { onEvent(JSON.parse(buf)); } catch (e) {}
  },
};

window.Utils = Utils;
