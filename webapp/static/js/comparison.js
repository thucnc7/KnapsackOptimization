// Pairwise comparison between two algorithms.

const Comparison = {
  async init() {
    const data = await Utils.fetchJson('/api/data/algorithms');
    const a = document.getElementById('cmp-a');
    const b = document.getElementById('cmp-b');
    [a, b].forEach((sel) => {
      sel.innerHTML = '';
      data.forEach((algo) => {
        const opt = document.createElement('option');
        opt.value = algo.name; opt.textContent = algo.name;
        sel.appendChild(opt);
      });
    });
    a.value = 'BranchAndBound';
    b.value = 'Greedy01';
    document.getElementById('cmp-run').onclick = () => Comparison.run();
    Comparison.run();
  },

  async run() {
    const a = document.getElementById('cmp-a').value;
    const b = document.getElementById('cmp-b').value;
    const file = document.getElementById('dash-file').value || '';
    const data = await Utils.fetchJson(`/api/benchmark/compare?a=${a}&b=${b}&file=${encodeURIComponent(file)}`);
    Comparison.render(data);
  },

  render(data) {
    const pairs = data.pairs;
    const okBoth = pairs.filter((p) => p.a.status === 'SUCCESS' && p.b.status === 'SUCCESS');

    // Cards
    const root = document.getElementById('cmp-cards');
    root.innerHTML = '';
    const aWinsTime = okBoth.filter((p) => p.a.time < p.b.time).length;
    const aWinsValue = okBoth.filter((p) => p.a.value > p.b.value).length;
    const sameValue = okBoth.filter((p) => p.a.value === p.b.value).length;
    [
      { title: 'Pairs compared', big: pairs.length, sub: 'instances cùng test_id' },
      { title: 'Both succeeded', big: okBoth.length, sub: '' },
      { title: `${data.a} nhanh hơn`, big: aWinsTime, sub: `/ ${okBoth.length}` },
      { title: 'Optimal value khớp', big: sameValue, sub: `/ ${okBoth.length}` },
    ].forEach((c) => {
      root.appendChild(Utils.el('div', { class: 'card' }, [
        Utils.el('h3', {}, c.title),
        Utils.el('div', { class: 'big' }, c.big),
        Utils.el('div', { class: 'sub' }, c.sub),
      ]));
    });

    // Paired scatter (time)
    const points = okBoth.map((p) => ({ x: p.a.time, y: p.b.time, n: p.n, id: p.test_id }));
    Utils.chart('cmp-time', {
      type: 'scatter',
      data: {
        datasets: [{
          label: `${data.a} (x) vs ${data.b} (y)`,
          data: points,
          backgroundColor: '#4f9eff',
        }],
      },
      options: {
        responsive: true,
        scales: {
          x: { type: 'logarithmic', title: { display: true, text: `${data.a} time (s)` } },
          y: { type: 'logarithmic', title: { display: true, text: `${data.b} time (s)` } },
        },
        plugins: { tooltip: { callbacks: { label: (ctx) => `${ctx.raw.id} (n=${ctx.raw.n}): A=${ctx.raw.x}s, B=${ctx.raw.y}s` } } },
      },
    });

    // Value comparison
    const sorted = [...okBoth].sort((p, q) => (p.n || 0) - (q.n || 0));
    Utils.chart('cmp-value', {
      type: 'line',
      data: {
        labels: sorted.map((p, i) => `${p.test_id.substring(0, 25)} (n=${p.n})`),
        datasets: [
          { label: data.a, data: sorted.map((p) => p.a.value), borderColor: '#4f9eff', backgroundColor: '#4f9eff33', tension: 0.2 },
          { label: data.b, data: sorted.map((p) => p.b.value), borderColor: '#a371f7', backgroundColor: '#a371f733', tension: 0.2 },
        ],
      },
      options: { responsive: true, scales: { x: { ticks: { display: false } } } },
    });

    // Speedup chart: time_b / time_a per N (median)
    const byN = {};
    okBoth.forEach((p) => {
      if (!byN[p.n]) byN[p.n] = [];
      if (p.a.time > 0) byN[p.n].push(p.b.time / p.a.time);
    });
    const Ns = Object.keys(byN).map(Number).sort((x, y) => x - y);
    const speedupMedians = Ns.map((n) => {
      const arr = byN[n].sort((x, y) => x - y);
      return arr[Math.floor(arr.length / 2)] || 0;
    });
    Utils.chart('cmp-speedup', {
      type: 'bar',
      data: { labels: Ns, datasets: [{ label: `Median ratio ${data.b}/${data.a}`, data: speedupMedians, backgroundColor: '#3fb950' }] },
      options: { responsive: true, scales: { y: { type: 'logarithmic', title: { display: true, text: 'ratio (>1 ⇒ A nhanh hơn)' } } } },
    });
  },
};

window.Comparison = Comparison;
