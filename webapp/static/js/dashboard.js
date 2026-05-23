// Dashboard panel: load CSV summary + charts.

const Dashboard = {
  async init() {
    const fileSelect = document.getElementById('dash-file');
    const files = await Utils.fetchJson('/api/benchmark/files');
    fileSelect.innerHTML = '';
    if (files.length === 0) {
      fileSelect.innerHTML = '<option>(không có file CSV)</option>';
    } else {
      const defaultName = 'benchmark_results_timeout5.csv';
      files.forEach((f) => {
        const opt = document.createElement('option');
        opt.value = f.name;
        opt.textContent = `${f.name} (${f.rows} rows)`;
        if (f.name === defaultName) opt.selected = true;
        fileSelect.appendChild(opt);
      });
    }
    document.getElementById('dash-refresh').onclick = () => Dashboard.load();
    fileSelect.onchange = () => Dashboard.load();
    Dashboard.load();
  },

  async load() {
    const file = document.getElementById('dash-file').value;
    if (!file || file.startsWith('(')) return;
    const data = await Utils.fetchJson(`/api/benchmark/summary?file=${encodeURIComponent(file)}`);
    Dashboard.renderCards(data);
    Dashboard.renderCharts(data);
    Dashboard.renderTable(data);
  },

  renderCards(data) {
    const total = data.totals?.rows || 0;
    const instances = data.totals?.instances || 0;
    const algos = data.algorithms?.length || 0;
    const bestSuccess = Object.entries(data.by_algorithm).sort((a, b) => b[1].success_rate - a[1].success_rate)[0];

    const root = document.getElementById('dash-cards');
    root.innerHTML = '';
    [
      { title: 'Tổng số runs', big: total, sub: 'rows trong CSV' },
      { title: 'Số instances', big: instances, sub: 'JSON tests duy nhất' },
      { title: 'Số thuật toán', big: algos, sub: 'algorithms evaluated' },
      { title: 'Top success rate', big: bestSuccess ? bestSuccess[0] : '—', sub: bestSuccess ? Utils.pct(bestSuccess[1].success_rate) : '' },
    ].forEach((c) => {
      root.appendChild(Utils.el('div', { class: 'card' }, [
        Utils.el('h3', {}, c.title),
        Utils.el('div', { class: 'big' }, c.big),
        Utils.el('div', { class: 'sub' }, c.sub),
      ]));
    });
  },

  renderCharts(data) {
    const algos = Object.keys(data.by_algorithm);
    const colors = algos.map((a) => Utils.algorithmColor(a));

    Utils.chart('dash-success', {
      type: 'bar',
      data: {
        labels: algos,
        datasets: [
          { label: 'Success', data: algos.map((a) => data.by_algorithm[a].success), backgroundColor: '#3fb950' },
          { label: 'Timeout', data: algos.map((a) => data.by_algorithm[a].timeout), backgroundColor: '#d29922' },
          { label: 'Error', data: algos.map((a) => data.by_algorithm[a].error), backgroundColor: '#f85149' },
        ],
      },
      options: { responsive: true, scales: { x: { stacked: true }, y: { stacked: true } } },
    });

    Utils.chart('dash-time', {
      type: 'bar',
      data: {
        labels: algos,
        datasets: [{ label: 'Avg time (s)', data: algos.map((a) => data.by_algorithm[a].avg_time || 0), backgroundColor: colors }],
      },
      options: { responsive: true, scales: { y: { type: 'logarithmic' } } },
    });

    Utils.chart('dash-memory', {
      type: 'bar',
      data: {
        labels: algos,
        datasets: [{ label: 'Avg memory (MB)', data: algos.map((a) => data.by_algorithm[a].avg_memory_mb || 0), backgroundColor: colors }],
      },
      options: { responsive: true },
    });

    const ns = Object.keys(data.by_n).map(Number).sort((a, b) => a - b);
    Utils.chart('dash-time-by-n', {
      type: 'line',
      data: {
        labels: ns,
        datasets: algos.map((a) => ({
          label: a,
          data: ns.map((n) => data.by_n[String(n)]?.[a]?.avg_time || null),
          borderColor: Utils.algorithmColor(a),
          backgroundColor: Utils.algorithmColor(a) + '33',
          spanGaps: true,
          tension: 0.25,
        })),
      },
      options: { responsive: true, scales: { y: { type: 'logarithmic', title: { display: true, text: 'time (s, log)' } }, x: { title: { display: true, text: 'N items' } } } },
    });
  },

  renderTable(data) {
    const algos = Object.keys(data.by_algorithm).sort();
    const root = document.getElementById('dash-table');
    const table = Utils.el('table', {}, [
      Utils.el('thead', {}, Utils.el('tr', {}, [
        'Algorithm', 'Total', 'Success', 'Timeout', 'Error', 'Success %', 'Avg time (s)', 'Median', 'Max', 'Avg mem MB', 'Max mem MB',
      ].map((h) => Utils.el('th', {}, h)))),
      Utils.el('tbody', {}, algos.map((a) => {
        const d = data.by_algorithm[a];
        return Utils.el('tr', {}, [
          Utils.el('td', {}, a),
          Utils.el('td', { class: 'num' }, d.total),
          Utils.el('td', { class: 'num' }, d.success),
          Utils.el('td', { class: 'num' }, d.timeout),
          Utils.el('td', { class: 'num' }, d.error),
          Utils.el('td', { class: 'num' }, Utils.pct(d.success_rate)),
          Utils.el('td', { class: 'num' }, Utils.fmt(d.avg_time, 5)),
          Utils.el('td', { class: 'num' }, Utils.fmt(d.median_time, 5)),
          Utils.el('td', { class: 'num' }, Utils.fmt(d.max_time, 5)),
          Utils.el('td', { class: 'num' }, Utils.fmt(d.avg_memory_mb, 4)),
          Utils.el('td', { class: 'num' }, Utils.fmt(d.max_memory_mb, 4)),
        ]);
      })),
    ]);
    root.innerHTML = '';
    root.appendChild(table);
  },
};

window.Dashboard = Dashboard;
