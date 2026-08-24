(() => {
  const birthdayMilestones = new Set([10,13,16,18,21,30,40,50,60,70,80,90,100]);
  const anniversaryMilestones = new Set([1,5,10,15,20,25,30,40,50,60,70]);

  function milestoneInfo(card) {
    const text = card.textContent || '';
    const birthday = text.match(/turning\s+(\d+)/i);
    if (birthday) {
      const number = Number(birthday[1]);
      if (birthdayMilestones.has(number)) return { number, label: `${number}th birthday` };
    }
    const anniversary = text.match(/anniversary[^\d]*(?:.*?)(\d+)\s+years/i) || text.match(/(\d+)\s+years/i);
    if (anniversary && /anniversary/i.test(text)) {
      const number = Number(anniversary[1]);
      if (anniversaryMilestones.has(number)) return { number, label: `${number} year milestone` };
    }
    return null;
  }

  function decorate() {
    document.querySelectorAll('.birthday-card,.home-reminder-card.birthday').forEach(card => {
      const info = milestoneInfo(card);
      card.classList.toggle('occasion-milestone', Boolean(info));
      let badge = card.querySelector('.occasion-milestone-badge');
      if (!info) {
        badge?.remove();
        return;
      }
      if (!badge) {
        badge = document.createElement('span');
        badge.className = 'occasion-milestone-badge';
        const target = card.querySelector('strong') || card.firstElementChild || card;
        target.insertAdjacentElement('afterend', badge);
      }
      badge.textContent = `★ ${info.label}`;
    });
  }

  const style = document.createElement('style');
  style.textContent = `
    .occasion-milestone{border-color:rgba(217,0,119,.58)!important;box-shadow:0 12px 28px rgba(73,79,111,.10)!important;background:linear-gradient(145deg,#fff,#ffb8d8 58%,#ff99c7)!important}
    .occasion-milestone-badge{display:inline-block;width:max-content;margin-top:6px;padding:5px 8px;border-radius:999px;background:#fff;border:1px solid rgba(217,0,119,.48);color:#8f004f;font-size:10px;font-weight:900;letter-spacing:.05em;text-transform:uppercase}
  `;
  document.head.appendChild(style);

  decorate();
  const observer = new MutationObserver(decorate);
  observer.observe(document.body, { childList: true, subtree: true });
  window.addEventListener('focus', decorate);
})();
