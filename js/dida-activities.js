/* Simple, clean Dida family activities with colourful titles and 3 clear steps.
   No complex tracking, save favourites, or nested folds. */
(() => {
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  
  const TITLE_COLOURS = [
    '#ff9b50', // Autumn orange / amber
    '#4ecdc4', // Bright cyan / teal
    '#ff7597', // Coral rose
    '#ffd166', // Sunny yellow
    '#7cf46a', // Lime green
    '#5bc0be', // Sky blue
    '#d55cff', // Purple / violet
    '#ff6b6b', // Coral red
    '#20c997', // Mint green
    '#f06595', // Vivid pink
    '#e599f7', // Lilac
    '#51cf66'  // Leaf green
  ];

  function renderCard(activity, index) {
    const color = TITLE_COLOURS[index % TITLE_COLOURS.length];
    const steps = (activity.steps || []).slice(0, 3);
    const stepsHtml = steps.map((step, sIdx) => `<li><span class="dida-step-num" style="color: ${color};">${sIdx + 1}.</span> <span class="dida-step-text">${esc(step)}</span></li>`).join('');
    return `
      <article class="dida-card" data-activity-id="${esc(activity.id)}">
        <h3 class="dida-card-title" style="color: ${color};">${esc(activity.title)}</h3>
        <ol class="dida-steps">
          ${stepsHtml}
        </ol>
      </article>
    `;
  }

  function mount(profile) {
    const host = document.getElementById('didaContent');
    if (!host) return;
    const all = window.DIDA_ACTIVITIES || [];
    if (!all.length) return;

    // Prioritise autumn colour hunt and current autumn / all-season activities
    const ordered = [...all].sort((a, b) => {
      if (a.id === 'autumn-colour-hunt') return -1;
      if (b.id === 'autumn-colour-hunt') return 1;
      if (a.season === 'autumn' && b.season !== 'autumn') return -1;
      if (b.season === 'autumn' && a.season !== 'autumn') return 1;
      return 0;
    });

    const cardsHtml = ordered.map((act, idx) => renderCard(act, idx)).join('');
    host.innerHTML = `<div class="dida-grid">${cardsHtml}</div>`;
  }

  window.mountDidaActivities = mount;
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => mount(window.state?.profile || 'pete'));
  } else {
    mount(window.state?.profile || 'pete');
  }
})();
