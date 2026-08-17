# Daily Briefs repository instructions

You are working on Pete's Daily Briefs project.

The single source of truth is docs/MASTER-BRIEF-CURRENT.md in PostWorkCulture/daily-briefs. Read it and docs/CHANGELOG.md before planning or modifying the build. Use only PostWorkCulture/daily-briefs; the old Claude/API repository is obsolete.

Never remove, rename, hide, reorder, restyle, or change an existing section, route, control, data source, content field, link, colour treatment, or responsive behaviour unless Pete explicitly requests it. A request about one component must not alter unrelated components.

If a request conflicts with the master brief, state the conflict and wait for Pete's decision. If the build conflicts with the brief, the brief wins unless Pete changes it. Missing history is not permission to remove current behaviour.

Before editing:

1. Read the master brief and changelog.
2. Inspect the implementation and data.
3. State the bounded scope and requirements at risk.

After editing:

1. Test the requested feature.
2. Test mobile and Chromebook/desktop.
3. Run docs/QA-CHECKLIST.md.
4. Report missing, unexpected, new, conflicting, and passed requirements.
5. Update the changelog.
6. Update the master brief only for an approved specification change.

Hard rules:

- Weather uses the Met Office for the home area.
- Weather icons match written conditions. Rain probability alone does not produce a rain icon.
- No weather advice or best-time content.
- Calendar data is real, refreshed, non-duplicated, and higher priority than Arsenal.
- No Arsenal betting or gambling information.
- Arsenal uses the men's first team, all competitions, latest completed fixture, and nearest upcoming fixture.
- Do not restore the obsolete Us profile.
- Keep Pete and Sofia personalisation consistent.
- All promised destinations and sources use real, clickable links.
- Never invent data, sources, URLs, test results, or completion claims.
- Do not add Anthropic/OpenAI API dependencies or paid API requirements.

If work pauses or is blocked, explain why, what is complete, what remains, and the exact next step.
