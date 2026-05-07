import { initRoteirosEditor } from './pages/roteiros/editor/index.js';

function bootRoteirosEditor() {
  const form = document.getElementById('oficio-roteiro-form');
  if (!form) return;
  initRoteirosEditor();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', bootRoteirosEditor);
} else {
  bootRoteirosEditor();
}
