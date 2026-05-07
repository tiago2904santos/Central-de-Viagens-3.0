import { initRoteirosEditor } from './pages/roteiros/editor/index.js';

function ensureJsonAlias(primaryId, fallbackId) {
  const primary = document.getElementById(primaryId);
  const fallback = document.getElementById(fallbackId);
  if (primary || !fallback) return;
  const clone = document.createElement('script');
  clone.type = 'application/json';
  clone.id = primaryId;
  clone.textContent = fallback.textContent || '';
  fallback.insertAdjacentElement('afterend', clone);
}

function bootRoteirosEditor() {
  const form = document.getElementById('oficio-roteiro-form') || document.getElementById('oficio-step3-form');
  if (!form) return;
  ensureJsonAlias('roteiro-state-data', 'step3-state-data');
  ensureJsonAlias('roteiro-routes-data', 'step3-routes-data');
  ensureJsonAlias('roteiro-diarias-data', 'step3-diarias-data');
  initRoteirosEditor();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', bootRoteirosEditor);
} else {
  bootRoteirosEditor();
}
