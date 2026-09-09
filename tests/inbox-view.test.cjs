const assert = require('node:assert/strict');
const test = require('node:test');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync('js/inbox-view.js', 'utf8');
function setup(profile, privatePage = false) {
  const node = () => ({ children: [], classList: {remove() {}}, append(...children) {this.children.push(...children)}, replaceChildren() {this.children=[]}, querySelector() {return this.children.find(c => c.tag==='iframe')} });
  const view = node(), button = node(); let destination;
  const state = {profile};
  const window = {};
  const document = {getElementById:()=>view, querySelector:()=>button, createElement: tag => ({...node(), tag}), addEventListener() {}};
  vm.runInNewContext(source, {window, document, state, location:{origin:privatePage?'https://inbox-command-centre.pyro-pete.chatgpt.site':'https://postworkculture.github.io', pathname:privatePage?'/brief/':'/daily-briefs/', assign(url){destination=url}}});
  return {window, view, button, state, destination:()=>destination};
}
test('public Pete enters the authenticated private brief without loading email publicly', () => {
  const env = setup('pete');
  assert.equal(env.button.hidden, false);
  assert.equal(env.window.openBriefInbox(), false);
  assert.equal(env.destination(), 'https://inbox-command-centre.pyro-pete.chatgpt.site/brief/?profile=pete&locked=1&view=inbox');
  assert.equal(env.view.children.length, 0);
});
test('Sofia has no Inbox entry and cannot open it directly', () => {
  const env = setup('sofia', true);
  assert.equal(env.button.hidden, true);
  assert.equal(env.window.openBriefInbox(), false);
  assert.equal(env.view.children.length, 0);
});
test('private Inbox is same-origin, reused between views and removed on profile change', () => {
  const env = setup('pete', true);
  assert.equal(env.window.openBriefInbox(), true);
  assert.equal(env.window.openBriefInbox(), true);
  assert.equal(env.view.children.length, 2);
  assert.equal(env.view.children[1].src, '/?from=brief');
  env.state.profile='sofia';
  env.window.syncBriefInbox('sofia');
  assert.equal(env.view.children.length, 0);
  assert.equal(env.button.hidden, true);
});
