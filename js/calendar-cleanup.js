// Keep the visible calendar focused on explicit ranges only.
if (typeof state !== 'undefined') {
  state.calendarRange = 'today';
}

// If profile data has already loaded before this script runs, redraw immediately.
if (typeof state !== 'undefined' && state.data?.calendar && typeof renderCalendar === 'function') {
  renderCalendar(state.data.calendar);
}

// Load the family birthday tab as a self-contained feature so daily data refreshes cannot overwrite it.
import('./birthdays.js?v=20260820a').catch(err=>console.error('Birthdays feature failed to load',err));
