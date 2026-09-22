/**
 * Daily Briefs - Google Calendar Color Sync
 * 
 * Automatically reads your true Google Calendar event colors and provides them
 * to your Daily Brief.
 * 
 * SETUP INSTRUCTIONS:
 * 1. Go to https://script.google.com and click "New project".
 * 2. Delete any code in the editor, paste this entire file, and click Save (Ctrl+S).
 * 3. In the toolbar, ensure "syncCalendarColors" is selected, and click "Run".
 * 4. Google will ask for permission to read your Calendar. Click "Review permissions" -> select your Google account -> "Allow".
 * 5. Check the "Execution log" at the bottom: it will display the JSON containing all your exact event colors!
 * 
 * AUTOMATIC DAILY SYNC (Zero maintenance):
 * 1. In Apps Script, click the blue "Deploy" button (top right) -> "New deployment".
 * 2. Click the gear icon next to "Select type" and choose "Web app".
 * 3. Configuration:
 *    - Description: Daily Briefs Calendar Color Sync
 *    - Execute as: Me (<your-email>)
 *    - Who has access: Anyone
 * 4. Click "Deploy" and copy the "Web app URL" (looks like https://script.google.com/macros/s/.../exec).
 * 5. In your GitHub repository (PostWorkCulture/daily-briefs):
 *    - Go to Settings -> Secrets and variables -> Actions.
 *    - Click "New repository secret".
 *    - Name: GOOGLE_CALENDAR_COLORS_URL
 *    - Value: <your Web app URL>
 *    - Click "Add secret".
 * 
 * From then on, every morning refresh will automatically pull your real event colors directly from Google!
 */

function doGet(e) {
  const payload = getCalendarColorsPayload();
  return ContentService.createTextOutput(JSON.stringify(payload, null, 2))
    .setMimeType(ContentService.MimeType.JSON);
}

function syncCalendarColors() {
  const payload = getCalendarColorsPayload();
  Logger.log("=== YOUR GOOGLE CALENDAR COLORS ===");
  Logger.log(JSON.stringify(payload, null, 2));
  return payload;
}

function getCalendarColorsPayload() {
  const calendar = CalendarApp.getDefaultCalendar();
  const now = new Date();
  now.setHours(0, 0, 0, 0);

  // Look ahead 60 days
  const future = new Date(now.getTime() + 60 * 24 * 60 * 60 * 1000);
  const events = calendar.getEvents(now, future);

  const eventMap = {};

  events.forEach(event => {
    let id = event.getId();
    if (id.indexOf("@") !== -1) {
      id = id.split("@")[0];
    }
    // Base series ID for recurring events
    const baseId = id.replace(/_R?\d+.*$/, "");

    const color = event.getColor(); // Returns "1" to "11", or "" if using default calendar color
    if (color) {
      eventMap[id] = color;
      if (baseId !== id) {
        eventMap[baseId] = color;
      }
    } else {
      eventMap[id] = null;
    }
  });

  return {
    eventPalette: {
      "1": "#a4bdfc",
      "2": "#7ae7bf",
      "3": "#dbadff",
      "4": "#ff887c",
      "5": "#fbd75b",
      "6": "#ffb878",
      "7": "#46d6db",
      "8": "#e1e1e1",
      "9": "#5484ed",
      "10": "#51b749",
      "11": "#dc2127"
    },
    defaultColor: calendar.getColor() || "#5484ed",
    events: eventMap
  };
}
