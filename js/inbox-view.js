/* Inbox integration is temporarily paused at Pete's request. */
(function () {
  const view = document.getElementById('view-inbox');
  const button = document.querySelector('[data-view-target="inbox"]');
  const mobileButton = document.querySelector('[data-open-inbox]');

  window.syncBriefInbox = function () {
    button.hidden = true;
    mobileButton.hidden = true;
    view.replaceChildren();
    view.classList.remove('active');
  };
  window.openBriefInbox = function () { return false; };
  window.syncBriefInbox();
})();
