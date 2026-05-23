// Job Runner panel: trigger benchmark/generator/quality subprocesses.

const Runner = {
  init() {
    document.getElementById('runner-refresh').onclick = () => Runner.refresh();
    document.getElementById('runner-bench-start').onclick = () => Runner.startBenchmark();
    document.getElementById('runner-gen-start').onclick = () => Runner.startGenerator();
    document.getElementById('runner-quality-start').onclick = () => Runner.startQuality();
    Runner.refresh();
    Runner._timer = setInterval(() => Runner.refresh(), 4000);
  },

  async refresh() {
    try {
      const jobs = await Utils.fetchJson('/api/runner/jobs');
      Runner.renderJobs(jobs);
    } catch (e) {
      console.error(e);
    }
  },

  renderJobs(jobs) {
    const root = document.getElementById('runner-jobs');
    root.innerHTML = '';
    if (jobs.length === 0) {
      root.innerHTML = '<p style="color:var(--text-dim)">Chưa có job nào.</p>';
      return;
    }
    const table = Utils.el('table', {}, [
      Utils.el('thead', {}, Utils.el('tr', {}, ['ID', 'Kind', 'PID', 'Status', 'Started', 'Actions'].map((h) => Utils.el('th', {}, h)))),
      Utils.el('tbody', {}, jobs.map((j) => {
        const status = j.running ? '<span class="badge b-running">running</span>'
          : (j.exit_code === 0 ? '<span class="badge b-success">done</span>' : `<span class="badge b-error">exit ${j.exit_code}</span>`);
        return Utils.el('tr', {}, [
          Utils.el('td', {}, j.id),
          Utils.el('td', {}, j.kind),
          Utils.el('td', { class: 'num' }, j.pid),
          Utils.el('td', { html: status }, ''),
          Utils.el('td', {}, j.started_at.substring(11, 19)),
          Utils.el('td', {}, [
            Utils.el('button', { onClick: () => Runner.viewLog(j.id) }, 'Xem log'),
            ' ',
            j.running ? Utils.el('button', { onClick: () => Runner.stopJob(j.id), style: 'background:var(--danger);' }, 'Stop') : '',
          ]),
        ]);
      })),
    ]);
    root.appendChild(table);
  },

  async startBenchmark() {
    const timeout = parseInt(document.getElementById('runner-bench-timeout').value, 10) || 5;
    const limit = parseInt(document.getElementById('runner-bench-limit').value, 10) || 0;
    const output = document.getElementById('runner-bench-output').value || undefined;
    const res = await Utils.postJson('/api/runner/benchmark', { timeout, limit, output });
    Runner.viewLog(res.job_id);
    Runner.refresh();
  },

  async startGenerator() {
    const seed = parseInt(document.getElementById('runner-gen-seed').value, 10) || 42;
    const res = await Utils.postJson('/api/runner/generator', { seed });
    Runner.viewLog(res.job_id);
    Runner.refresh();
  },

  async startQuality() {
    const res = await Utils.postJson('/api/runner/quality', {});
    Runner.viewLog(res.job_id);
    Runner.refresh();
  },

  async stopJob(id) {
    await fetch(`/api/runner/jobs/${id}`, { method: 'DELETE' });
    Runner.refresh();
  },

  async viewLog(id) {
    Runner._currentJob = id;
    if (Runner._logTimer) clearInterval(Runner._logTimer);
    const pump = async () => {
      try {
        const res = await Utils.fetchJson(`/api/runner/jobs/${id}/log?tail=1`);
        const pre = document.getElementById('runner-log');
        pre.textContent = res.content || '(log trống)';
        pre.scrollTop = pre.scrollHeight;
        Runner.renderProgress(id, res);
        if (!res.running) clearInterval(Runner._logTimer);
      } catch (e) {
        console.error(e);
      }
    };
    pump();
    Runner._logTimer = setInterval(pump, 2000);
  },

  renderProgress(id, res) {
    const box = document.getElementById('runner-progress-box');
    box.innerHTML = '';
    const header = Utils.el('div', { style: 'margin-bottom:8px;' }, [
      Utils.el('strong', {}, `Job ${id}`),
      ' — ',
      res.running ? Utils.el('span', { class: 'badge b-running' }, 'running')
        : Utils.el('span', { class: `badge ${res.exit_code === 0 ? 'b-success' : 'b-error'}` }, `exited ${res.exit_code}`),
    ]);
    box.appendChild(header);
    const p = res.progress;
    if (p && p.total) {
      const klass = res.running ? '' : (res.exit_code === 0 ? 'success' : 'danger');
      box.appendChild(Utils.progressBar(p.percent, klass, `${p.current}/${p.total} (${p.percent}%)`));
      box.appendChild(Utils.el('div', { style: 'display:flex;gap:18px;color:var(--text-dim);font-size:12px;' }, [
        Utils.el('span', {}, `elapsed: ${p.elapsed}`),
        Utils.el('span', {}, `ETA: ${p.eta}`),
      ]));
    } else {
      box.appendChild(Utils.el('p', { style: 'color:var(--text-dim);font-size:12px;' }, 'Chưa có tqdm progress nào.'));
    }
  },
};

window.Runner = Runner;
