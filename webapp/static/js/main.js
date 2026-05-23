// Mode switcher + initial bootstrapping.

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
})();
