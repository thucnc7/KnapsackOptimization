// Custom instance builder with random generator + capacity bar.

const Custom = {
  async init() {
    Custom.items = [];
    document.getElementById('custom-add-row').onclick = () => Custom.addRow();
    document.getElementById('custom-load-sample').onclick = () => Custom.loadSample();
    document.getElementById('custom-run').onclick = () => Custom.run();
    document.getElementById('rand-gen').onclick = () => Custom.generateRandom();

    const algos = await Utils.fetchJson('/api/data/algorithms');
    const sel = document.getElementById('custom-algo');
    sel.innerHTML = '';
    algos.forEach((a) => {
      const opt = document.createElement('option');
      opt.value = a.name; opt.textContent = `${a.name} (${a.knapsack_type})`;
      sel.appendChild(opt);
    });

    Custom.loadSample();
  },

  loadSample() {
    document.getElementById('custom-capacity').value = 50;
    Custom.items = [
      { weight: 12, value: 24 },
      { weight: 7, value: 13 },
      { weight: 11, value: 23 },
      { weight: 8, value: 15 },
      { weight: 9, value: 16 },
    ];
    Custom.renderTable();
    Custom.renderScatterPreview();
  },

  async generateRandom() {
    const payload = {
      n: parseInt(document.getElementById('rand-n').value, 10),
      max_weight: parseInt(document.getElementById('rand-mw').value, 10),
      capacity_ratio: parseFloat(document.getElementById('rand-cr').value),
      pearson_r: parseFloat(document.getElementById('rand-pr').value),
      seed: document.getElementById('rand-seed').value || null,
    };
    try {
      const data = await Utils.postJson('/api/data/random-instance', payload);
      Custom.items = data.items.map((it) => ({ weight: it.weight, value: it.value }));
      document.getElementById('custom-capacity').value = data.capacity;
      Custom.renderTable();
      Custom.renderScatterPreview();
      document.getElementById('custom-result').innerHTML = `<span style="color:var(--text-dim)">Đã sinh ${data.items.length} items. Bấm Run để chạy.</span>`;
    } catch (e) {
      alert('Sinh thất bại: ' + e.message);
    }
  },

  addRow() {
    Custom.items.push({ weight: 1, value: 1 });
    Custom.renderTable();
  },

  renderTable() {
    const tbody = document.querySelector('#custom-items tbody');
    tbody.innerHTML = '';
    Custom.items.forEach((it, idx) => {
      const tr = Utils.el('tr', {}, [
        Utils.el('td', {}, String(idx)),
        Utils.el('td', {}, [Utils.el('input', { type: 'number', step: 'any', value: it.weight, onInput: (e) => { it.weight = parseFloat(e.target.value) || 0; Custom.updateDensity(tr, it); Custom.renderScatterPreview(); } })]),
        Utils.el('td', {}, [Utils.el('input', { type: 'number', step: 'any', value: it.value, onInput: (e) => { it.value = parseFloat(e.target.value) || 0; Custom.updateDensity(tr, it); Custom.renderScatterPreview(); } })]),
        Utils.el('td', { class: 'num density' }, Utils.fmt(it.weight ? it.value / it.weight : 0, 3)),
        Utils.el('td', {}, [Utils.el('button', { class: 'del-btn', onClick: () => { Custom.items.splice(idx, 1); Custom.renderTable(); Custom.renderScatterPreview(); } }, '✕')]),
      ]);
      tbody.appendChild(tr);
    });
    document.getElementById('custom-items-summary').textContent = `Bảng items (${Custom.items.length} rows)`;
  },

  updateDensity(tr, it) {
    tr.querySelector('.density').textContent = Utils.fmt(it.weight ? it.value / it.weight : 0, 3);
  },

  renderScatterPreview(selectedSet = null) {
    const all = Custom.items.map((it, idx) => ({ x: it.weight, y: it.value, id: idx }));
    const sel = selectedSet || new Set();
    Utils.chart('custom-chart', {
      type: 'scatter',
      data: {
        datasets: [
          { label: 'Không chọn', data: all.filter((p) => !sel.has(p.id)), backgroundColor: '#3b4452' },
          { label: 'Đã chọn', data: all.filter((p) => sel.has(p.id)), backgroundColor: '#3fb950', pointRadius: 5 },
        ],
      },
      options: { responsive: true, scales: { x: { title: { display: true, text: 'weight' } }, y: { title: { display: true, text: 'value' } } } },
    });
  },

  async run() {
    const capacity = parseFloat(document.getElementById('custom-capacity').value) || 0;
    const algorithm = document.getElementById('custom-algo').value;
    const timeout = parseFloat(document.getElementById('custom-timeout').value) || 15;
    if (Custom.items.length === 0) { alert('Cần thêm ít nhất 1 item'); return; }
    const payload = {
      algorithm, timeout,
      instance: {
        capacity,
        items: Custom.items.map((it, idx) => ({ id: idx, weight: it.weight, value: it.value })),
      },
    };
    const btn = document.getElementById('custom-run');
    btn.disabled = true;
    btn.textContent = 'Đang chạy…';
    document.getElementById('custom-cap-bar').innerHTML = '';
    Utils.showRunning('custom-result', algorithm, timeout, `Đang giải custom instance (n=${Custom.items.length})`);

    try {
      const res = await Utils.postJson('/api/solver/run', payload);
      Utils.hideRunning('custom-result');
      Custom.renderResult(res, capacity);
    } catch (e) {
      Utils.hideRunning('custom-result');
      document.getElementById('custom-result').innerHTML = `<span class="status-ERROR">${e.message}</span>`;
    } finally {
      btn.disabled = false;
      btn.textContent = 'Run';
    }
  },

  renderResult(res, capacity) {
    const out = document.getElementById('custom-result');
    out.innerHTML = '';
    [
      ['status', `<span class="status-${res.status}">${res.status}</span>`],
      ['time (s)', Utils.fmt(res.time_sec, 6)],
      ['memory (MB)', Utils.fmt(res.peak_memory_mb, 4)],
      ['optimal_value', Utils.fmt(res.optimal_value, 2)],
      ['items', res.selected.length],
      ['error', res.error || '—'],
    ].forEach(([k, v]) => out.appendChild(Utils.el('div', { class: 'kv' }, [Utils.el('span', { class: 'k' }, k), Utils.el('span', { class: 'v', html: String(v) })])));

    const used = res.selected.reduce((acc, s) => acc + (s.weight || 0) * (s.fraction ?? s.quantity ?? 1), 0);
    Utils.capacityBar('custom-cap-bar', used, capacity);

    const sel = new Set(res.selected.map((s) => s.id));
    Custom.renderScatterPreview(sel);
  },
};

window.Custom = Custom;
