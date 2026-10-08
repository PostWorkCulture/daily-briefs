/* Simple, clean Dida family activities with colourful titles, 3 clear steps,
   and high-definition editorial still-life photography with zero visible people.
   Picks exactly 4 distinct activities each day. */
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

  const DIDA_POOL = [
    {
      id: 'autumn-colour-hunt',
      title: 'Autumn colour hunt',
      image: 'assets/dida/autumn-colour-hunt.webp',
      steps: [
        'Draw four autumn colour patches on your paper.',
        'Walk together and look for leaves that match your colours.',
        'Draw a tick beside each colour you spot and name your favourite leaf.'
      ]
    },
    {
      id: 'read-together',
      title: 'Read together',
      image: 'assets/dida/read-together.webp',
      steps: [
        'Choose a picture book and find a cosy reading spot together.',
        'Take turns pointing to illustrations and guessing what happens next.',
        'Show your favourite picture and say why you chose it.'
      ]
    },
    {
      id: 'shadow-story',
      title: 'Little shadow theatre',
      image: 'assets/dida/shadow-story.webp',
      steps: [
        'Turn on a bedside lamp to beam against a plain wall in a dim room.',
        'Use your hands or paper animal shapes to cast shadows on the wall.',
        'Make your shadow characters dance, talk, and go on a mini adventure.'
      ]
    },
    {
      id: 'paper-bridge',
      title: 'Paper bridge lab',
      image: 'assets/dida/paper-bridge.webp',
      steps: [
        'Place two hardcover books a small step apart on a table.',
        'Fold a sheet of thick paper accordion-style across the gap to form a bridge.',
        'Test how many small blocks or coins it can hold before it bends.'
      ]
    },
    {
      id: 'autumn-mini-museum',
      title: 'Our tiny autumn museum',
      image: 'assets/dida/autumn-mini-museum.webp',
      steps: [
        'Choose three interesting fallen leaves on your walk.',
        'Make a paper label for each with its colour and where you found it.',
        'Arrange your museum on a table and give your grown-up a tour.'
      ]
    },
    {
      id: 'nature-sound-map',
      title: 'Draw a sound map',
      image: 'assets/dida/nature-sound-map.webp',
      steps: [
        'Sit quietly outside together for one minute with eyes closed and listen.',
        'Draw a little dot in the centre of your paper for yourself.',
        'Draw playful marks around your dot for each sound you hear near and far.'
      ]
    },
    {
      id: 'swedish-colour-finder',
      title: 'Colour finder: English + svenska',
      image: 'assets/dida/swedish-colour-finder.webp',
      steps: [
        'Pick a Swedish colour word together: röd, blå, grön, or gul.',
        'Search around the room to find three objects that match that colour.',
        'Touch each one and say the colour out loud in Swedish and English.'
      ]
    },
    {
      id: 'musical-weather',
      title: 'The weather dance',
      image: 'assets/dida/musical-weather.webp',
      steps: [
        'Put on a cheerful favourite song in the living room.',
        'Dance together like gentle rain, swirling autumn wind, or beaming sunshine.',
        'Freeze like a statue every time the music pauses.'
      ]
    },
    {
      id: 'number-count',
      title: 'Count it three ways',
      image: 'assets/dida/number-count.webp',
      steps: [
        'Pick ten wooden building blocks and count them into a straight line.',
        'Rearrange the same blocks into a circle or rainbow and count again.',
        'Spread them across the mat and check if the total stays the same.'
      ]
    },
    {
      id: 'sock-bowling',
      title: 'Soft-sock bowling',
      image: 'assets/dida/sock-bowling.webp',
      steps: [
        'Roll two or three pairs of fluffy socks into soft round balls.',
        'Set up six paper cups in a bowling triangle at the end of the hallway.',
        'Take turns rolling your sock ball to see how many cups you can knock over.'
      ]
    },
    {
      id: 'pattern-parade',
      title: 'Pattern parade',
      image: 'assets/dida/pattern-parade.webp',
      steps: [
        'Pick two kinds of small toys or blocks in different colours or shapes.',
        'Line them up in an alternating pattern: block, toy, block, toy.',
        'Ask your grown-up to guess which piece comes next, then chant the pattern.'
      ]
    },
    {
      id: 'toy-rescue-route',
      title: 'Toy rescue route',
      image: 'assets/dida/toy-rescue-route.webp',
      steps: [
        'Place a favourite teddy bear on a low chair across the room.',
        'Lay down four soft floor cushions as stepping stones across the rug.',
        'Balance and hop carefully across each cushion to rescue the teddy bear.'
      ]
    }
  ];

  function getDailyActivities(pool, date = new Date()) {
    // Days since unix epoch in UTC
    const dayNumber = Math.floor(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()) / 86400000);
    // 20734 is 8 Oct 2026. (dayNumber - 20734) * 4 ensures 8 Oct starts at 0 with Autumn colour hunt.
    const baseOffset = ((dayNumber - 20734) * 4) % pool.length;
    const startIndex = (baseOffset + pool.length) % pool.length;
    
    const selected = [];
    for (let i = 0; i < 4; i++) {
      selected.push(pool[(startIndex + i) % pool.length]);
    }
    return selected;
  }

  function renderCard(activity, index) {
    const color = TITLE_COLOURS[index % TITLE_COLOURS.length];
    const steps = (activity.steps || []).slice(0, 3);
    const stepsHtml = steps.map((step, sIdx) => `<li><span class="dida-step-num" style="color: ${color};">${sIdx + 1}.</span> <span class="dida-step-text">${esc(step)}</span></li>`).join('');
    const imageSrc = activity.image || `assets/dida/${activity.id}.webp`;
    return `
      <article class="dida-card" data-activity-id="${esc(activity.id)}">
        <div class="dida-card-media">
          <img src="${esc(imageSrc)}" alt="${esc(activity.title)}" class="dida-card-img" loading="lazy" />
        </div>
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
    const pool = DIDA_POOL;
    const dailyActivities = getDailyActivities(pool, new Date());
    const cardsHtml = dailyActivities.map((act, idx) => renderCard(act, idx)).join('');
    host.innerHTML = `<div class="dida-grid">${cardsHtml}</div>`;
  }

  window.mountDidaActivities = mount;
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => mount(window.state?.profile || 'pete'));
  } else {
    mount(window.state?.profile || 'pete');
  }
})();
