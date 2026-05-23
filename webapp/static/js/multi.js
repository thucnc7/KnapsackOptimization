// Multi-algorithm streaming runner panel.

const MultiSolver = {
  async init() {
    document.getElementById('multi-search').oninput = (e) => MultiSolver.filter(e.target.value);
    document.getElementById('multi-run').onclick = () => MultiSolver.run();
    document.getElementById('multi-stop').onclick = () => MultiSolver.abort();

    const algos = await Utils.fetchJson('/api/data/algorithms');
    const root = document.getElementById('multi-algos');
    root.innerHTML = '';
    algos.forEach((a) => {
      const id = `multi-algo-${a.name}`;
      root.appendChild(Utils.el('label', { for: id }, [
        Utils.el('input', { type: 'checkbox', id, value: a.name, checked: '' }),
        ` ${a.name}`,
      ]));
    });

    const list = await Utils.fetchJson('/api/data/instances?limit=2000');
    MultiSolver.allInstances = list.items;
    MultiSolver.filter('');
  },

  filter(q) {
    const sel = document.getElementById('multi-instance');
    sel.innerHTML = '';
    const filtered = MultiSolver.allInstances.filter((it) => !q || it.id.toLowerCase().includes(q.toLowerCase()));
    filtered.slice(0, 500).forEach((it) => {
      const opt = document.createElement('option');
      opt.value = it.id; opt.textContent = it.id;
      sel.appendChild(opt);
    });
  },

  async run() {
    const id = document.getElementById('multi-instance').value;
    if (!id) return;
    const algorithms = Array.from(document.querySelectorAll('#multi-algos input:checked')).map((c) => c.value);
    if (algorithms.length === 0) return;
    const timeout = parseFloat(document.getElementById('multi-timeout').value) || 10;

    document.getElementById('multi-run').disabled = true;
    document.getElementById('multi-stop').style.display = '';
    document.getElementById('multi-table').innerHTML = '';

    MultiSolver._abort = new AbortController();
    MultiSolver._results = [];
    MultiSolver.renderStreamHeader(algorithms);

    Utils.startTimer('multi-live', '⏱ tổng');

    try {
      await Utils.streamNdjson('/api/solver/run-stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ instance_id: id, algorithms, timeout }),
        signal: MultiSolver._abort.signal,
      }, (ev) => MultiSolver.onEvent(ev));
    } catch (e) {
      if (e.name !== 'AbortError') console.error(e);
    } finally {
      Utils.stopTimer('multi-live');
      document.getElementById('multi-run').disabled = false;
      document.getElementById('multi-stop').style.display = 'none';
      MultiSolver.renderCharts();
      MultiSolver.renderTable();
    }
  },

  abort() {
    if (MultiSolver._abort) MultiSolver._abort.abort();
  },

  renderStreamHeader(algorithms) {
    const root = document.getElementById('multi-stream');
    root.innerHTML = '';
    root.appendChild(Utils.el('div', { class: 'stream-row', style: 'font-weight:600;color:var(--text-dim);' }, [
      'Algorithm', 'Status', 'Progress', 'Time (s)', 'Optimal value',
    ].map((h) => Utils.el('span', {}, h))));
    algorithms.forEach((name) => {
      const row = Utils.el('div', { class: 'stream-row pending', id: `multi-row-${name}` }, [
        Utils.el('span', { class: 'algo' }, name),
        Utils.el('span', { class: 'badge' }, 'pending'),
        Utils.el('span', { class: 'progress-cell' }, '—'),
        Utils.el('span', { class: 'num' }, '—'),
        Utils.el('span', { class: 'num' }, '—'),
      ]);
      root.appendChild(row);
    });
  },

  onEvent(ev) {
    if (ev.event === 'start') {
      MultiSolver._total = ev.total;
      MultiSolver._capacity = ev.capacity;
      MultiSolver._n = ev.n;
    } else if (ev.event === 'algo-start') {
      const row = document.getElementById(`multi-row-${ev.algorithm}`);
      if (!row) return;
      row.classList.remove('pending');
      row.children[1].innerHTML = '<span class="badge b-running">running</span>';
      row.children[2].textContent = '0.0s';
    } else if (ev.event === 'tick') {
      const row = document.getElementById(`multi-row-${ev.algorithm}`);
      if (!row) return;
      row.children[2].textContent = `${ev.elapsed}s`;
    } else if (ev.event === 'algo-done') {
      const row = document.getElementById(`multi-row-${ev.algorithm}`);
      const r = ev.result;
      if (!row) return;
      const cls = r.status === 'SUCCESS' ? 'b-success' : (r.status === 'TIMEOUT' ? 'b-warn' : 'b-error');
      row.children[1].innerHTML = `<span class="badge ${cls}">${r.status}</span>`;
      row.children[2].textContent = `done`;
      row.children[3].textContent = Utils.fmt(r.time_sec, 5);
      row.children[4].textContent = Utils.fmt(r.optimal_value, 2);
      MultiSolver._results.push(r);
    } else if (ev.event === 'end') {
      // results are already collected via algo-done; capture full list for safety
      MultiSolver._results = ev.results;
    }
  },

  renderCharts() {
    const results = MultiSolver._results;
    if (!results || results.length === 0) return;
    Utils.chart('multi-time', {
      type: 'bar',
      data: {
        labels: results.map((r) => r.algorithm),
        datasets: [{ label: 'time (s)', data: results.map((r) => r.time_sec || 0), backgroundColor: results.map((r) => Utils.algorithmColor(r.algorithm)) }],
      },
      options: { responsive: true, scales: { y: { type: 'logarithmic' } } },
    });
    Utils.chart('multi-memory', {
      type: 'bar',
      data: {
        labels: results.map((r) => r.algorithm),
        datasets: [{ label: 'memory (MB)', data: results.map((r) => r.peak_memory_mb || 0), backgroundColor: results.map((r) => Utils.algorithmColor(r.algorithm)) }],
      },
      options: { responsive: true },
    });
    Utils.chart('multi-value', {
      type: 'bar',
      data: {
        labels: results.map((r) => r.algorithm),
        datasets: [{ label: 'optimal value', data: results.map((r) => r.optimal_value || 0), backgroundColor: results.map((r) => Utils.algorithmColor(r.algorithm)) }],
      },
      options: { responsive: true },
    });
  },

  renderTable() {
    const results = MultiSolver._results;
    if (!results || results.length === 0) return;
    const tableRoot = document.getElementById('multi-table');
    tableRoot.innerHTML = '';
    tableRoot.appendChild(Utils.el('table', {}, [
      Utils.el('thead', {}, Utils.el('tr', {}, ['Algorithm', 'Status', 'Time (s)', 'Memory (MB)', 'Optimal value', 'Items chọn', 'Total weight', 'Error'].map((h) => Utils.el('th', {}, h)))),
      Utils.el('tbody', {}, results.map((r) => Utils.el('tr', {}, [
        Utils.el('td', {}, r.algorithm),
        Utils.el('td', { class: `status-${r.status}` }, r.status),
        Utils.el('td', { class: 'num' }, Utils.fmt(r.time_sec, 6)),
        Utils.el('td', { class: 'num' }, Utils.fmt(r.peak_memory_mb, 4)),
        Utils.el('td', { class: 'num' }, Utils.fmt(r.optimal_value, 2)),
        Utils.el('td', { class: 'num' }, r.selected ? r.selected.length : 0),
        Utils.el('td', { class: 'num' }, Utils.fmt((r.selected || []).reduce((acc, s) => acc + (s.weight || 0) * (s.fraction ?? s.quantity ?? 1), 0), 2)),
        Utils.el('td', {}, r.error || ''),
      ]))),
    ]));
  },
};

window.MultiSolver = MultiSolver;
