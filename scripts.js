/* alphabet-first browsing and instance-based filters. */
const normalize = value => String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
export function selectInstances(rows, f) {
  const q = normalize(f.search).trim();
  const numeric = /^#?\d+$/.test(q) ? Number(q.replace('#', '')) : null;
  return rows.filter(o => {
    if (numeric !== null ? o.id !== numeric : q && !normalize(`${o.lemma} ${o.sense}`).includes(q)) return false;
    if (f.letter && normalize(o.lemma)[0] !== normalize(f.letter)) return false;
    if (f.status !== 'all' && o.status !== f.status) return false;
    if (f.valency !== 'all' && o.valency !== Number(f.valency)) return false;
    if (f.role !== 'all' || f.realization !== 'all') {
      if (!o.roles.some(r => (f.role === 'all' || r.slot === f.role) && (f.realization === 'all' || r.status === f.realization))) return false;
    }
    return true;
  });
}

if (typeof document !== 'undefined') {
  const controls = ['search', 'status', 'valency', 'role', 'realization'];
  const params = new URLSearchParams(location.search);
  let letter = params.get('letter') ?? '', page = 1;
  const allButton = document.createElement('button');
  const alphabet = document.querySelector('#alphabet-buttons');
  for (const value of ['', ...'ABCDEFGHIJKLMNOPQRSTUVWXYZ']) {
    const button = value ? document.createElement('button') : allButton;
    button.className = 'letter-button'; button.type = 'button'; button.textContent = value || 'Todos';
    button.dataset.letter = value; button.setAttribute('aria-pressed', String(letter === value));
    button.addEventListener('click', () => { letter = value; page = 1; render(); });
    alphabet.append(button);
  }
  for (const id of controls) {
    const node = document.getElementById(id);
    if (params.has(id)) node.value = params.get(id);
    node.addEventListener(id === 'search' ? 'input' : 'change', () => { page = 1; render(); });
  }
  let rows = [];
  function render() {
    const f = Object.fromEntries(controls.map(id => [id, document.getElementById(id).value])); f.letter = letter;
    const selected = selectInstances(rows, f), grouped = new Map();
    for (const o of selected) {
      if (!grouped.has(o.lemma)) grouped.set(o.lemma, []); grouped.get(o.lemma).push(o);
    }
    const lemmas = [...grouped.entries()]; const totalPages = Math.max(1, Math.ceil(lemmas.length / 50));
    page = Math.min(page, totalPages);
    const container = document.getElementById('content-box'); container.replaceChildren();
    const exact = /^#?\d+$/.test(f.search.trim());
    for (const [lemma, matches] of lemmas.slice((page - 1) * 50, page * 50)) {
      const link = document.createElement('a'); link.className = 'lemma-card';
      link.href = `site_pages/${matches[0].slug}.html` + (exact ? `#instance-${matches[0].id}` : '');
      const name = document.createElement('strong'); name.textContent = lemma;
      const info = document.createElement('small'); info.textContent = `${matches.length} instâncias · ${matches.filter(o => o.status === 'annotated').length} com ARG`;
      link.append(name, info); container.append(link);
    }
    if (!lemmas.length) { const p = document.createElement('p'); p.textContent = 'Nenhum nome encontrado com esses filtros.'; container.append(p); }
    const count = document.getElementById('result-count');
    count.textContent = `${lemmas.length.toLocaleString('pt-BR')} lemas · ${selected.length.toLocaleString('pt-BR')} instâncias`;
    count.dataset.lemmas = lemmas.length; count.dataset.instances = selected.length;
    document.getElementById('page-label').textContent = `Página ${page} de ${totalPages}`;
    document.getElementById('previous').disabled = page <= 1; document.getElementById('next').disabled = page >= totalPages;
    for (const b of alphabet.children) { const active = b.dataset.letter === letter; b.classList.toggle('selected', active); b.setAttribute('aria-pressed', String(active)); }
    const state = new URLSearchParams();
    for (const [key,value] of Object.entries(f)) if (value && value !== 'all') state.set(key,value);
    history.replaceState(null,'',location.pathname + (state.size ? '?' + state : ''));
  }
  document.getElementById('previous').addEventListener('click', () => { page--; render(); });
  document.getElementById('next').addEventListener('click', () => { page++; render(); });
  fetch('data/lemma_index.json', {cache:'no-store'}).then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); }).then(data => { rows = data.instances; render(); }).catch(() => { document.getElementById('result-count').textContent = 'Não foi possível carregar o índice. Abra a lista completa de nomes.'; const a = document.createElement('a'); a.href = 'all-lemmas.html'; a.textContent = 'Lista completa'; document.getElementById('content-box').append(a); });
}
