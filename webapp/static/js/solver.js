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
    filtered.slice(0, 500).forEach((it, i) => {
      const opt = document.createElement('option');
      opt.value = it.id; opt.textContent = it.id;
      if (i === 0) opt.selected = true;
      sel.appendChild(opt);
    });
    if (filtered.length) {
      sel.value = filtered[0].id;
      Solver.loadInstance(filtered[0].id);
    }
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
    document.getElementById('solver-trace-section').style.display = 'none';
    const isSimplex = Solver.SIMPLEX.has(algorithm);
    Utils.showRunning('solver-result', algorithm, timeout, `Đang giải instance ${id} bằng ${algorithm}`);
    try {
      const res = await Utils.postJson('/api/solver/run', {
        algorithm, instance_id: id, timeout, trace: isSimplex,
      });
      Utils.hideRunning('solver-result');
      Solver.renderResult(res);
      if (isSimplex && res.trace) Solver.renderTrace(res);
    } catch (e) {
      Utils.hideRunning('solver-result');
      document.getElementById('solver-result').innerHTML = `<span class="status-ERROR">${e.message}</span>`;
    } finally {
      btn.disabled = false;
      btn.textContent = 'Run';
    }
  },

  SIMPLEX: new Set(['PrimalSimplex', 'DualSimplex', 'SimplexBnB', 'GomoryCut']),

  renderTrace(res) {
    const section = document.getElementById('solver-trace-section');
    section.style.display = 'block';
    const trace = res.trace || [];
    const lp = res.lp_shape || {};

    // Stats cards
    const pivotCount = trace.filter((t) => t.phase !== 'transition').length;
    const phaseTransitionIter = trace.findIndex((t) => t.phase === 'transition');
    const phase1Count = trace.filter((t) => t.phase === 'phase1').length;
    const phase2Count = trace.filter((t) => t.phase === 'phase2').length;
    const cards = document.getElementById('solver-trace-cards');
    cards.innerHTML = '';
    [
      { title: 'Số pivots', big: pivotCount, sub: phase1Count > 0 ? `Phase I: ${phase1Count}, Phase II: ${phase2Count}` : `tất cả ${pivotCount}` },
      { title: 'LP tableau', big: `${lp.rows}×${lp.cols}`, sub: `${lp.n_decision} decision vars, ${lp.n_constraints} constraints, ${lp.n_artificial} artificials` },
      { title: 'Final objective', big: Utils.fmt(lp.final_objective, 4), sub: phaseTransitionIter >= 0 ? `Phase transition tại iter ${phaseTransitionIter}` : 'Không cần Phase I' },
      { title: 'Decision vars trong basis cuối', big: trace.length > 0 ? (trace[trace.length - 1].n_basis_decision || 0) : 0, sub: `trên tổng ${lp.n_decision} vars` },
    ].forEach((c) => {
      cards.appendChild(Utils.el('div', { class: 'card' }, [
        Utils.el('h3', {}, c.title),
        Utils.el('div', { class: 'big' }, c.big),
        Utils.el('div', { class: 'sub' }, c.sub),
      ]));
    });

    // Objective evolution
    const pivots = trace.filter((t) => t.phase !== 'transition');
    const objSeries = pivots.map((t, i) => ({ x: i, y: t.objective }));
    const colors = pivots.map((t) => t.phase === 'phase1' ? '#d29922' : (t.phase === 'phase2' ? '#3fb950' : '#4f9eff'));
    const transitionX = phaseTransitionIter >= 0 ? pivots.findIndex((_, i) => trace.slice(0, phaseTransitionIter + 1).filter((tr) => tr.phase !== 'transition').length === i) : -1;
    Utils.chart('solver-trace-obj', {
      type: 'line',
      data: {
        labels: objSeries.map((p) => p.x),
        datasets: [{
          label: 'objective',
          data: objSeries.map((p) => p.y),
          borderColor: '#4f9eff', backgroundColor: '#4f9eff22',
          pointBackgroundColor: colors, pointRadius: 4, tension: 0.1,
          fill: true,
        }],
      },
      options: {
        responsive: true,
        scales: { x: { title: { display: true, text: 'pivot iteration' } }, y: { title: { display: true, text: 'objective value' } } },
        plugins: {
          tooltip: { callbacks: { afterLabel: (ctx) => `phase=${pivots[ctx.dataIndex]?.phase}, pre=${Utils.fmt(pivots[ctx.dataIndex]?.pre_objective, 2)}` } },
        },
      },
    });

    // Basis size over time
    Utils.chart('solver-trace-basis-count', {
      type: 'line',
      data: {
        labels: pivots.map((_, i) => i),
        datasets: [{
          label: 'decision vars in basis',
          data: pivots.map((t) => t.n_basis_decision || 0),
          borderColor: '#a371f7', backgroundColor: '#a371f733', tension: 0.2, fill: true,
        }],
      },
      options: { responsive: true, scales: { y: { beginAtZero: true } } },
    });

    // Pivot columns (entering + leaving variable indices)
    Utils.chart('solver-trace-pivot-cols', {
      type: 'scatter',
      data: {
        datasets: [
          { label: 'entering col', data: pivots.map((t, i) => ({ x: i, y: t.entering_col })), backgroundColor: '#3fb950' },
          { label: 'leaving var', data: pivots.map((t, i) => ({ x: i, y: t.leaving_var })), backgroundColor: '#f85149' },
        ],
      },
      options: {
        responsive: true,
        scales: { x: { title: { display: true, text: 'iteration' } }, y: { title: { display: true, text: 'variable index' } } },
      },
    });

    // History table
    const histRoot = document.getElementById('solver-trace-history');
    histRoot.innerHTML = '';
    const headers = ['iter', 'phase', 'entering_col', 'leaving_var', 'pre_obj', 'post_obj', 'Δ', 'basis size'];
    histRoot.appendChild(Utils.el('table', {}, [
      Utils.el('thead', {}, Utils.el('tr', {}, headers.map((h) => Utils.el('th', {}, h)))),
      Utils.el('tbody', {}, trace.map((t) => {
        if (t.phase === 'transition') {
          return Utils.el('tr', { style: 'background:rgba(79,158,255,0.1);' }, [
            Utils.el('td', { colspan: 8, style: 'text-align:center;color:var(--primary);font-style:italic;' }, `⇣ ${t.marker} ⇣`),
          ]);
        }
        const delta = (t.objective || 0) - (t.pre_objective || 0);
        return Utils.el('tr', {}, [
          Utils.el('td', { class: 'num' }, t.iter),
          Utils.el('td', {}, t.phase),
          Utils.el('td', { class: 'num' }, t.entering_col),
          Utils.el('td', { class: 'num' }, t.leaving_var),
          Utils.el('td', { class: 'num' }, Utils.fmt(t.pre_objective, 4)),
          Utils.el('td', { class: 'num' }, Utils.fmt(t.objective, 4)),
          Utils.el('td', { class: 'num', style: delta > 0 ? 'color:var(--success)' : '' }, Utils.fmt(delta, 4)),
          Utils.el('td', { class: 'num' }, t.n_basis_decision),
        ]);
      })),
    ]));
    document.getElementById('solver-trace-history-summary').textContent = `Hiện chi tiết (${trace.length} entries)`;
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
