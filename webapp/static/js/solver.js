// Single instance solver panel with live timer + capacity bar.

const Solver = {
  async init() {
    Solver.allInstances = [];
    document.getElementById('solver-search').oninput = (e) => Solver.filter(e.target.value);
    document.getElementById('solver-instance').onchange = (e) => Solver.loadInstance(e.target.value);
    document.getElementById('solver-run').onclick = () => Solver.run();

    const algos = await Utils.fetchJson('/api/data/algorithms');
    const algoSel = document.getElementById('solver-algo');
    algoSel.innerHTML = '';
    algos.forEach((a) => {
      const opt = document.createElement('option');
      opt.value = a.name; opt.textContent = `${a.name} (${a.knapsack_type})`;
      algoSel.appendChild(opt);
    });

    const list = await Utils.fetchJson('/api/data/instances?limit=2000');
    Solver.allInstances = list.items;
    Solver.filter('');
  },

  filter(q) {
    const sel = document.getElementById('solver-instance');
    sel.innerHTML = '';
    const filtered = Solver.allInstances.filter((it) => !q || it.id.toLowerCase().includes(q.toLowerCase()));
    filtered.slice(0, 500).forEach((it) => {
      const opt = document.createElement('option');
      opt.value = it.id; opt.textContent = it.id;
      sel.appendChild(opt);
    });
    if (filtered.length) Solver.loadInstance(filtered[0].id);
  },

  async loadInstance(id) {
    if (!id) return;
    const info = document.getElementById('solver-instance-info');
    info.innerHTML = 'Loading…';
    const data = await Utils.fetchJson(`/api/data/instance/${encodeURIComponent(id)}`);
    Solver.currentInstance = data;
    const meta = data.metadata || {};
    info.innerHTML = '';
    [
      ['test_id', data.test_id],
      ['n items', data.items.length],
      ['capacity', Utils.fmt(data.capacity)],
      ['capacity_ratio', meta.capacity_ratio_input ?? meta.capacity_ratio ?? '—'],
      ['target_pearson_r', meta.target_pearson_r ?? '—'],
      ['actual_pearson_r', meta.pearson_actual ?? meta.pearson_r ?? '—'],
      ['max_weight', meta.max_weight ?? '—'],
    ].forEach(([k, v]) => info.appendChild(Utils.el('div', { class: 'kv' }, [Utils.el('span', { class: 'k' }, k), Utils.el('span', { class: 'v' }, String(v))])));

    // Pre-render scatter of all items, no selection yet
    Solver.renderItemsScatter([], data.items);
    document.getElementById('solver-cap-bar').innerHTML = '';
    document.getElementById('solver-result').innerHTML = 'Chưa chạy';
    document.getElementById('solver-items-table').innerHTML = '';
  },

  async run() {
    const id = document.getElementById('solver-instance').value;
    const algorithm = document.getElementById('solver-algo').value;
    const timeout = parseFloat(document.getElementById('solver-timeout').value) || 10;
    if (!id || !algorithm) return;
    const btn = document.getElementById('solver-run');
    btn.disabled = true;
    btn.textContent = 'Đang chạy…';
    document.getElementById('solver-cap-bar').innerHTML = '';
    document.getElementById('solver-items-table').innerHTML = '';
    Utils.showRunning('solver-result', algorithm, timeout, `Đang giải instance ${id} bằng ${algorithm}`);
    try {
      const res = await Utils.postJson('/api/solver/run', { algorithm, instance_id: id, timeout });
      Utils.hideRunning('solver-result');
      Solver.renderResult(res);
    } catch (e) {
      Utils.hideRunning('solver-result');
      document.getElementById('solver-result').innerHTML = `<span class="status-ERROR">${e.message}</span>`;
    } finally {
      btn.disabled = false;
      btn.textContent = 'Run';
    }
  },

  renderResult(res) {
    const out = document.getElementById('solver-result');
    out.innerHTML = '';
    const status = `<span class="status-${res.status}">${res.status}</span>`;
    [
      ['algorithm', res.algorithm],
      ['status', status],
      ['knapsack_type', res.knapsack_type || '—'],
      ['time (s)', Utils.fmt(res.time_sec, 6)],
      ['memory (MB)', Utils.fmt(res.peak_memory_mb, 4)],
      ['optimal_value', Utils.fmt(res.optimal_value, 2)],
      ['selected items', res.selected.length],
      ['total weight', Utils.fmt(res.total_selected_weight ?? Solver.totalWeight(res.selected), 2)],
      ['timeout budget', `${res.timeout_budget_sec}s`],
      ['error', res.error || '—'],
    ].forEach(([k, v]) => out.appendChild(Utils.el('div', { class: 'kv' }, [Utils.el('span', { class: 'k' }, k), Utils.el('span', { class: 'v', html: String(v) })])));

    // Capacity fill bar
    const used = Solver.totalWeight(res.selected);
    Utils.capacityBar('solver-cap-bar', used, res.capacity || Solver.currentInstance?.capacity || 0);

    Solver.renderItemsScatter(res.selected, Solver.currentInstance?.items || []);
    Solver.renderItemsTable(res.selected);
  },

  totalWeight(selected) {
    return selected.reduce((acc, s) => acc + (s.weight || 0) * (s.fraction ?? s.quantity ?? 1), 0);
  },

  renderItemsScatter(selected, all) {
    const selectedIds = new Set(selected.map((s) => s.id));
    Utils.chart('solver-items-chart', {
      type: 'scatter',
      data: {
        datasets: [
          {
            label: `Không chọn (${all.length - selectedIds.size})`,
            data: all.filter((it) => !selectedIds.has(it.id)).map((it) => ({ x: it.weight, y: it.value, id: it.id })),
            backgroundColor: '#3b4452',
          },
          {
            label: `Đã chọn (${selectedIds.size})`,
            data: all.filter((it) => selectedIds.has(it.id)).map((it) => ({ x: it.weight, y: it.value, id: it.id })),
            backgroundColor: '#3fb950',
            pointRadius: 5,
          },
        ],
      },
      options: {
        responsive: true,
        scales: { x: { title: { display: true, text: 'weight' } }, y: { title: { display: true, text: 'value' } } },
        plugins: { tooltip: { callbacks: { label: (ctx) => `id=${ctx.raw.id}: w=${ctx.raw.x}, v=${ctx.raw.y}` } } },
      },
    });
  },

  renderItemsTable(selected) {
    const root = document.getElementById('solver-items-table');
    root.innerHTML = '';
    if (selected.length === 0) {
      root.innerHTML = '<p style="color:var(--text-dim)">Không có items nào được chọn</p>';
      return;
    }
    const enriched = selected.map((s) => ({
      ...s,
      density: s.weight > 0 ? (s.value || 0) / s.weight : 0,
    })).sort((a, b) => b.density - a.density);

    const headers = ['id', 'weight', 'value', 'density'];
    if (enriched[0].fraction !== undefined) headers.push('fraction');
    if (enriched[0].quantity !== undefined) headers.push('quantity');
    root.appendChild(Utils.el('table', {}, [
      Utils.el('thead', {}, Utils.el('tr', {}, headers.map((h) => Utils.el('th', {}, h)))),
      Utils.el('tbody', {}, enriched.slice(0, 200).map((s) => Utils.el('tr', {}, headers.map((h) => Utils.el('td', { class: 'num' }, Utils.fmt(s[h], 4)))))),
    ]));
    if (enriched.length > 200) {
      root.appendChild(Utils.el('p', { style: 'color:var(--text-dim)' }, `Hiển thị 200/${enriched.length} items`));
    }
  },
};

window.Solver = Solver;
