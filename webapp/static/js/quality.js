// Data Quality panel: scenarios + quality images.

const Quality = {
  async init() {
    document.getElementById('quality-refresh').onclick = () => Quality.load();
    Quality.load();
  },

  async load() {
    const [scenarios, images] = await Promise.all([
      Utils.fetchJson('/api/data/scenarios'),
      Utils.fetchJson('/api/data/quality-images'),
    ]);
    Quality.renderScenarios(scenarios);
    Quality.renderImages(images);
  },

  renderScenarios(scenarios) {
    const root = document.getElementById('quality-scenarios');
    root.innerHTML = '';
    scenarios.forEach((sc) => {
      const box = Utils.el('div', { class: 'card', style: 'margin-bottom:12px;' }, [
        Utils.el('h3', {}, sc.name),
        Utils.el('p', { style: 'color:var(--text-dim);font-size:12px;' }, sc.description || ''),
        Utils.el('table', {}, [
          Utils.el('thead', {}, Utils.el('tr', {}, ['Field', 'Value'].map((h) => Utils.el('th', {}, h)))),
          Utils.el('tbody', {}, Object.entries(sc).filter(([k]) => !['name', 'description'].includes(k)).map(([k, v]) => Utils.el('tr', {}, [
            Utils.el('td', {}, k),
            Utils.el('td', { class: 'num' }, JSON.stringify(v)),
          ]))),
        ]),
      ]);
      root.appendChild(box);
    });
  },

  renderImages(images) {
    const root = document.getElementById('quality-images');
    root.innerHTML = '';
    if (images.length === 0) {
      root.innerHTML = '<p style="color:var(--text-dim)">Chưa có biểu đồ chất lượng. Chạy <code>python data/quality.py</code> trong tab Job Runner.</p>';
      return;
    }
    images.forEach((img) => {
      const fig = Utils.el('figure', {}, [
        Utils.el('img', { src: img.url, alt: img.name, loading: 'lazy' }),
        Utils.el('figcaption', {}, `${img.category} / ${img.name}`),
      ]);
      root.appendChild(fig);
    });
  },
};

window.Quality = Quality;
