// Keep the visible calendar focused on explicit ranges only.
if (typeof state !== 'undefined') {
  state.calendarRange = 'today';
}

// If profile data has already loaded before this script runs, redraw immediately.
if (typeof state !== 'undefined' && state.data?.calendar && typeof renderCalendar === 'function') {
  renderCalendar(state.data.calendar);
}

// Preview-only enhancement for milestone birthdays and anniversaries.
if (!document.querySelector('script[data-occasion-milestones]')) {
  const milestoneScript = document.createElement('script');
  milestoneScript.src = 'js/occasion-milestones.js?v=20260820a';
  milestoneScript.defer = true;
  milestoneScript.dataset.occasionMilestones = '1';
  document.head.appendChild(milestoneScript);
}
