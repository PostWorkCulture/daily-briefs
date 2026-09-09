/* Pete-only entry to the owner-authenticated Inbox Command Centre. */
(function () {
  const privateOrigin = 'https://inbox-command-centre.pyro-pete.chatgpt.site';
  const isPrivateBrief = location.origin === privateOrigin && location.pathname.startsWith('/brief');
  const view = document.getElementById('view-inbox');
  const button = document.querySelector('[data-view-target="inbox"]');

  window.syncBriefInbox = function (profile) {
    button.hidden = profile !== 'pete';
    if (profile !== 'pete') {
      view.replaceChildren();
      view.classList.remove('active');
    }
  };

  window.openBriefInbox = function () {
    if (state.profile !== 'pete') return false;
    if (!isPrivateBrief) {
      location.assign(privateOrigin + '/brief/?profile=pete&locked=1&view=inbox');
      return false;
    }
    if (!view.querySelector('iframe')) {
      const header = document.createElement('div');
      header.className = 'inbox-view-heading';
      const title = document.createElement('h2');
      title.textContent = 'Inbox';
      const link = document.createElement('a');
      link.href = '/';
      link.textContent = 'Open full inbox';
      header.append(title, link);
      const frame = document.createElement('iframe');
      frame.src = '/?from=brief';
      frame.title = 'Your private Inbox Command Centre';
      frame.className = 'inbox-frame';
      view.append(header, frame);
    }
    return true;
  };

  window.syncBriefInbox(state.profile);
  // Defer until the existing view controller has installed its listeners.
  document.addEventListener('DOMContentLoaded', function () {
    if (isPrivateBrief && new URLSearchParams(location.search).get('view') === 'inbox') {
      window.showBriefView('inbox');
    }
  });
})();
