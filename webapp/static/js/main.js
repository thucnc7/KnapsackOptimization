// Mode switcher + initial bootstrapping + first-time welcome modal.

(function () {
  const buttons = document.querySelectorAll('.mode-btn');
  const panels = document.querySelectorAll('.panel');
  const initialized = new Set();

  const initializers = {
    dashboard: () => Dashboard.init(),
    comparison: () => Comparison.init(),
    solver: () => Solver.init(),
    multi: () => MultiSolver.init(),
    custom: () => Custom.init(),
    sensitivity: () => Sensitivity.init(),
    quality: () => Quality.init(),
    runner: () => Runner.init(),
  };

  function activate(mode) {
    buttons.forEach((b) => b.classList.toggle('active', b.dataset.mode === mode));
    panels.forEach((p) => p.classList.toggle('active', p.dataset.panel === mode));
    if (!initialized.has(mode)) {
      initialized.add(mode);
      try { initializers[mode] && initializers[mode](); } catch (e) { console.error(e); }
    }
  }

  buttons.forEach((b) => b.addEventListener('click', () => activate(b.dataset.mode)));
  activate('dashboard');

  // --- Welcome modal (FTUE) ---
  const modal = document.getElementById('welcome-modal');
  const helpBtn = document.getElementById('help-btn');
  const dismissed = localStorage.getItem('knapsack-welcome-dismissed') === '1';

  function showModal() { if (modal) modal.style.display = 'flex'; }
  function hideModal() { if (modal) modal.style.display = 'none'; }

  if (!dismissed && modal) showModal();

  if (modal) {
    modal.querySelector('.modal-backdrop').addEventListener('click', hideModal);
    document.getElementById('welcome-close').addEventListener('click', () => {
      if (document.getElementById('welcome-dontshow').checked) {
        localStorage.setItem('knapsack-welcome-dismissed', '1');
      }
      hideModal();
    });
    modal.querySelectorAll('.tour-item').forEach((item) => {
      item.addEventListener('click', () => {
        const mode = item.dataset.jump;
        if (mode) {
          activate(mode);
          hideModal();
        }
      });
    });
  }

  if (helpBtn) helpBtn.addEventListener('click', showModal);
})();
