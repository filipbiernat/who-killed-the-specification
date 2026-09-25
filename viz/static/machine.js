/* Draw whatever the server says the machine is doing.
   There is no coffee-machine logic in this file, and there is no number
   here that the Python did not send. */

const mount = document.getElementById('machine-mount');
const conn = document.getElementById('conn');

let svg = null;
let shownSource = null;

fetch('/machine.svg')
  .then((response) => response.text())
  .then((markup) => {
    mount.innerHTML = markup;
    svg = document.getElementById('machine');
    connect();
  });

function connect() {
  const source = new EventSource('/api/stream');

  source.onmessage = (event) => render(JSON.parse(event.data));

  source.onopen = () => setConnected(true);
  source.onerror = () => {
    /* A frozen picture is indistinguishable from a working one, so say so. */
    setConnected(false);
  };
}

function setConnected(up) {
  conn.dataset.up = String(up);
  conn.textContent = up ? 'LIVE' : 'DISCONNECTED';
}

function render(snapshot) {
  setConnected(true);
  if (!svg) return;

  svg.dataset.state = snapshot.state;
  svg.style.setProperty('--water-level', snapshot.tank_ml / snapshot.tank_capacity_ml);
  svg.style.setProperty('--cup-fill', snapshot.cup_ml / snapshot.cup_capacity_ml);

  const banner = svg.querySelector('#banner');
  if (banner) {
    banner.textContent = snapshot.warning_banner;
  }

  document.getElementById('spec-uid').textContent = snapshot.spec_uid;
  document.getElementById('spec-text').textContent = snapshot.spec_text;
  document.getElementById('sha').textContent = 'sha ' + snapshot.src_sha;
  showSource(snapshot.source, snapshot.spec_uid);

  const tests = snapshot.tests || {};
  document.getElementById('passed').textContent = tests.passed ?? 0;
  document.getElementById('failed').textContent = tests.failed ?? 0;
  document.getElementById('first-failure').textContent = tests.first_failure || '';
  document.getElementById('results').classList.toggle('failing', (tests.failed ?? 0) > 0);
}

/* Mark the code that carries the displayed requirement's UID: from its
   comment to the next blank line. Redrawn only when the file changes, so the
   heartbeat does not keep yanking the scroll position. */
function showSource(source, uid) {
  const key = uid + '\n' + source;
  if (key === shownSource) return;
  shownSource = key;

  const pre = document.getElementById('source');
  pre.textContent = '';
  let first = null;
  let inBlock = false;
  for (const line of source.split('\n')) {
    if (!first && line.trim().startsWith('#') && line.includes(uid)) inBlock = true;
    else if (!line.trim()) inBlock = false;
    const row = document.createElement('span');
    row.textContent = line || ' ';
    if (inBlock) {
      row.className = 'governed';
      first = first || row;
    }
    pre.appendChild(row);
  }
  if (first) pre.scrollTop = first.offsetTop - pre.clientHeight / 4;
}

document.querySelector('.controls').addEventListener('click', (event) => {
  const action = event.target.dataset.action;
  if (!action) return;
  if (action === 'espresso') post('/api/select', { drink: 'espresso' });
  if (action === 'empty') post('/api/tank', { level_ml: 0 });
  if (action === 'refill') post('/api/refill', {});
});

function post(url, body) {
  return fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}
