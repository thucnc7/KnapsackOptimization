// Sensitivity analysis panel: warm-start Dual Simplex vs solve-from-scratch.

const Sensitivity = {
  async init() {
    document.getElementById('sens-refresh').onclick = () => Sensitivity.load();
    Sensitivity.load();
  },

  async load() {
    const data = await Utils.fetchJson('/api/benchmark/sensitivity');
    if (!data.available) {
      const root = document.getElementById('sens-cards');
      root.innerHTML = '';
      root.appendChild(Utils.el('div', { class: 'card', style: 'grid-column:1/-1;text-align:center;padding:30px;' }, [
        Utils.el('p', { style: 'font-size:14px;color:var(--text-dim);' }, data.hint || 'Chưa có dữ liệu sensitivity. Hãy chạy benchmark/sensitivity_runner.py.'),
      ]));
      return;
    }
    Sensitivity.data = data;
    Sensitivity.renderCards(data);
    Sensitivity.renderCharts(data);
    Sensitivity.renderTable(data);
    Sensitivity.renderStaticImages();
  },

  renderCards(data) {
    const root = document.getElementById('sens-cards');
    root.innerHTML = '';
    const t = data.totals;
    [
      { title: 'Tổng số runs', big: t.count, sub: '600 = 200 instances × 3 scenarios' },
      { title: 'Warm-start thắng', big: Utils.pct(t.warm_win_rate), sub: `${t.warm_wins}/${t.count} runs nhanh hơn solve from scratch` },
      { title: 'Speedup trung bình', big: t.speedup.mean.toFixed(1) + 'x', sub: `median ${t.speedup.median.toFixed(1)}x` },
      { title: 'Speedup tối đa', big: t.speedup.max.toFixed(0) + 'x', sub: 'best-case warm-start' },
    ].forEach((c) => {
      root.appendChild(Utils.el('div', { class: 'card' }, [
        Utils.el('h3', {}, c.title),
        Utils.el('div', { class: 'big' }, c.big),
        Utils.el('div', { class: 'sub' }, c.sub),
      ]));
    });
  },

  renderCharts(data) {
    const scenarios = Object.keys(data.by_scenario);
    const scenarioColor = (sc) => ({ capacity: '#4f9eff', value: '#a371f7', volume: '#3fb950' }[sc] || '#d29922');

    // 1) Speedup histogram by scenario (log scale)
    const buckets = [0.1, 0.3, 1, 3, 10, 30, 100, 300, 1000, 3000, 10000, 30000];
    const labels = buckets.slice(0, -1).map((lo, i) => `${lo}-${buckets[i+1]}`);
    const datasets = scenarios.map((sc) => {
      const speedups = data.rows.filter((r) => r.scenario === sc).map((r) => r.speedup).filter((x) => x != null);
      const counts = labels.map((_, i) => speedups.filter((s) => s >= buckets[i] && s < buckets[i+1]).length);
      return { label: sc, data: counts, backgroundColor: scenarioColor(sc) + 'cc' };
    });
    Utils.chart('sens-speedup-hist', {
      type: 'bar',
      data: { labels, datasets },
      options: {
        responsive: true,
        scales: { x: { title: { display: true, text: 'speedup bucket (log)' } }, y: { title: { display: true, text: 'số runs' } } },
      },
    });

    // 2) Time scratch vs warm scatter (log-log)
    Utils.chart('sens-time-scatter', {
      type: 'scatter',
      data: {
        datasets: scenarios.map((sc) => ({
          label: sc,
          data: data.rows.filter((r) => r.scenario === sc).map((r) => ({
            x: r.time_scratch_sec, y: r.time_warm_sec, n: r.n, speedup: r.speedup,
          })),
          backgroundColor: scenarioColor(sc) + '88',
        })),
      },
      options: {
        responsive: true,
        scales: {
          x: { type: 'logarithmic', title: { display: true, text: 'time scratch (s, log)' } },
          y: { type: 'logarithmic', title: { display: true, text: 'time warm-start (s, log)' } },
        },
        plugins: {
          tooltip: {
            callbacks: { label: (ctx) => `n=${ctx.raw.n}, speedup=${(ctx.raw.speedup||0).toFixed(1)}x` },
          },
        },
      },
    });

    // 3) Iterations comparison (grouped bars by scenario)
    Utils.chart('sens-iter', {
      type: 'bar',
      data: {
        labels: scenarios,
        datasets: [
          { label: 'iter scratch (mean)', data: scenarios.map((s) => data.by_scenario[s].iter_scratch.mean), backgroundColor: '#d29922' },
          { label: 'iter warm (mean)', data: scenarios.map((s) => data.by_scenario[s].iter_warm.mean), backgroundColor: '#3fb950' },
        ],
      },
      options: { responsive: true, scales: { y: { title: { display: true, text: 'pivots trung bình' } } } },
    });

    // 4) Win rate by scenario
    Utils.chart('sens-win-rate', {
      type: 'bar',
      data: {
        labels: scenarios,
        datasets: [{ label: 'win rate', data: scenarios.map((s) => data.by_scenario[s].warm_win_rate * 100), backgroundColor: scenarios.map(scenarioColor) }],
      },
      options: { responsive: true, scales: { y: { min: 0, max: 100, title: { display: true, text: '% runs warm-start nhanh hơn' } } } },
    });
  },

  renderTable(data) {
    const scenarios = Object.keys(data.by_scenario);
    const root = document.getElementById('sens-table');
    root.innerHTML = '';
    root.appendChild(Utils.el('table', {}, [
      Utils.el('thead', {}, Utils.el('tr', {}, [
        'Scenario', 'Runs', 'Win rate', 'Speedup mean', 'Speedup median', 'Speedup max',
        'Time scratch (mean s)', 'Time warm (mean s)', 'Iter scratch (mean)', 'Iter warm (mean)',
      ].map((h) => Utils.el('th', {}, h)))),
      Utils.el('tbody', {}, scenarios.map((sc) => {
        const s = data.by_scenario[sc];
        return Utils.el('tr', {}, [
          Utils.el('td', {}, sc),
          Utils.el('td', { class: 'num' }, s.count),
          Utils.el('td', { class: 'num' }, Utils.pct(s.warm_win_rate)),
          Utils.el('td', { class: 'num' }, Utils.fmt(s.speedup.mean, 2)),
          Utils.el('td', { class: 'num' }, Utils.fmt(s.speedup.median, 2)),
          Utils.el('td', { class: 'num' }, Utils.fmt(s.speedup.max, 1)),
          Utils.el('td', { class: 'num' }, Utils.fmt(s.time_scratch.mean, 5)),
          Utils.el('td', { class: 'num' }, Utils.fmt(s.time_warm.mean, 5)),
          Utils.el('td', { class: 'num' }, Utils.fmt(s.iter_scratch.mean, 1)),
          Utils.el('td', { class: 'num' }, Utils.fmt(s.iter_warm.mean, 1)),
        ]);
      })),
    ]));
  },

  renderStaticImages() {
    const root = document.getElementById('sens-static-imgs');
    root.innerHTML = '';
    [
      'runtime_comparison.png',
      'iterations_comparison.png',
      'speedup_distribution.png',
    ].forEach((name) => {
      const fig = Utils.el('figure', {}, [
        Utils.el('img', { src: `/api/data/static-image/sensitivity/${name}`, alt: name, loading: 'lazy', onError: function() { this.style.display = 'none'; } }),
        Utils.el('figcaption', {}, name),
      ]);
      root.appendChild(fig);
    });
  },
};

window.Sensitivity = Sensitivity;
