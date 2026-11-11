const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');

const extRoot = path.resolve(__dirname, '..');
const pkg = JSON.parse(fs.readFileSync(path.join(extRoot, 'package.json'), 'utf8'));

test('package.json defines 11.0.0 metadata, sidebar viewContainer, and commands with zero runtime deps', () => {
    assert.equal(pkg.version, '11.0.0');
    assert.equal(pkg.dependencies === undefined || Object.keys(pkg.dependencies).length === 0, true);
    assert.ok(pkg.contributes.viewsContainers && Array.isArray(pkg.contributes.viewsContainers.activitybar));
    assert.ok(pkg.contributes.views && Array.isArray(pkg.contributes.views.tzeroSidebar));

    const commandIds = new Set(pkg.contributes.commands.map((c) => c.command));
    for (const required of [
        'tzero.init',
        'tzero.compressFile',
        'tzero.showTree',
        'tzero.audit',
        'tzero.openDashboard',
        'tzero.explain',
        'tzero.review',
        'tzero.watch',
        'tzero.golden',
        'tzero.budget',
        'tzero.contracts',
        'tzero.debt',
        'tzero.mutate',
        'tzero.bridge',
        'tzero.mergeHeal',
        'tzero.refreshMetrics',
        'tzero.lspCheck',
        'tzero.hookInstall',
        'tzero.federationImpact'
    ]) {
        assert.ok(commandIds.has(required), `Missing command: ${required}`);
    }

    const props = pkg.contributes.configuration.properties;
    assert.ok(props['tzero.executablePath']);
    assert.ok(props['tzero.autoInitOnOpen']);
});

test('core.js resolves executable paths and parses scan JSON cleanly', () => {
    const core = require('../src/core');
    assert.equal(core.resolveExecutable(''), 'tzero');
    assert.equal(core.resolveExecutable('   '), 'tzero');
    assert.equal(core.resolveExecutable('/opt/venv/bin/tzero'), '/opt/venv/bin/tzero');

    const parsed = core.parseScanJson('Log line\n{"workspace_dir": "/tmp/ws", "total_files": 4, "raw_tokens": 1200, "pruned_tokens": 240, "savings_pct": 80.0, "files": []}');
    assert.ok(parsed);
    assert.equal(parsed.total_files, 4);
    assert.equal(parsed.savings_pct, 80.0);
    assert.equal(core.parseScanJson('not-json'), null);
});

test('core.js formats dynamic status bar from real scan metrics', () => {
    const core = require('../src/core');
    const emptyBar = core.formatStatusBar(null, null);
    assert.match(emptyBar.text, /T-Zero:/);
    assert.doesNotMatch(emptyBar.text, /94\.9%/);

    const liveBar = core.formatStatusBar({
        total_files: 12,
        raw_tokens: 10000,
        pruned_tokens: 1500,
        savings_pct: 85.0
    }, { symbolCount: 4, fileName: 'app.py' });
    assert.match(liveBar.text, /85\.0%/);
    assert.match(liveBar.tooltip, /12 files/);
    assert.match(liveBar.tooltip, /app\.py/);
});

test('core.js computes real block-span CodeLens metrics without *6 approximation', () => {
    const core = require('../src/core');
    const pySource = [
        'class Processor:',
        '    def run(self, data: list) -> int:',
        '        acc = 0',
        '        for item in data:',
        '            acc += item * 2',
        '            if acc > 100:',
        '                break',
        '        return acc',
        '',
        'def helper(x: int) -> int:',
        '    y = x + 1',
        '    return y'
    ].join('\n');

    const metrics = core.computeCodeLensMetrics(pySource, 'python');
    assert.equal(metrics.length, 3);
    assert.equal(metrics[0].name, 'Processor');
    assert.equal(metrics[1].name, 'run');
    assert.equal(metrics[2].name, 'helper');
    assert.ok(metrics[0].endLine >= 7);
    assert.ok(metrics[0].rawTokens > metrics[0].signatureTokens);
    assert.ok(metrics[0].savingsPct > 0);
});

test('core.js builds multi-line AST contract from explain JSON or signature fallback', () => {
    const core = require('../src/core');
    const tsSource = [
        'export function packContext(',
        '    workspace: string,',
        '    budget: number',
        '): Promise<string> {',
        '    return Promise.resolve(workspace);',
        '}'
    ].join('\n');

    const fromExplain = core.buildSymbolContract(tsSource, 0, [
        { lineno: 1, name: 'packContext', signatures: ['export function packContext(workspace: string, budget: number): Promise<string>'], docstring: 'Packs workspace context.' }
    ]);
    assert.match(fromExplain, /packContext\(workspace: string, budget: number\)/);
    assert.match(fromExplain, /Packs workspace context/);

    const fallback = core.buildSymbolContract(tsSource, 0, null);
    assert.match(fallback, /budget: number/);
    assert.doesNotMatch(fallback, /Promise\.resolve/);
});

test('core.js renders offline sidebar HTML with live metrics and command dispatch buttons', () => {
    const core = require('../src/core');
    const html = core.buildSidebarHtml({
        metrics: { total_files: 8, raw_tokens: 4000, pruned_tokens: 600, savings_pct: 85.0 },
        lastCommand: 'tzero --debt',
        lastOutput: 'Debt Score: 92/100'
    });
    assert.match(html, /85\.0%/);
    assert.match(html, /tzero\.debt/);
    assert.match(html, /tzero\.golden/);
    assert.match(html, /tzero\.lspCheck/);
    assert.match(html, /tzero\.hookInstall/);
    assert.match(html, /tzero\.federationImpact/);
    assert.match(html, /Debt Score: 92\/100/);
    assert.match(html, /Content-Security-Policy/);
    assert.doesNotMatch(html, /https?:\/\/cdn\./i);
});

test('core.js quotes terminal args safely and ignores braces inside strings/comments', () => {
    const core = require('../src/core');
    assert.equal(core.quoteTerminalArg("C:\\Users\\a$b\\it's", 'win32'), "'C:\\Users\\a$b\\it''s'");
    assert.equal(core.quoteTerminalArg("/tmp/a$b/it's", 'linux'), "'/tmp/a$b/it'\\''s'");

    const jsWithBraces = [
        'export function parseTemplate(name: string): string {',
        '    const fakeClose = "}"; // ignore } here',
        '    const tail = `}` + name;',
        '    return fakeClose + tail;',
        '}',
        'export function afterFn(): number {',
        '    return 1;',
        '}'
    ].join('\n');
    const metrics = core.computeCodeLensMetrics(jsWithBraces, 'typescript');
    assert.equal(metrics.length, 2);
    assert.equal(metrics[0].endLine, 4);
    assert.equal(metrics[1].endLine, 7);
});

test('extension.js invokes compatible tzero_v3 CLI flags for init and pipe compression', () => {
    const extSrc = fs.readFileSync(path.join(extRoot, 'src', 'extension.js'), 'utf8');
    assert.doesNotMatch(extSrc, /'--ultra'/);
    assert.doesNotMatch(extSrc, /\['--init',\s*wsRoot\]/);
    assert.match(extSrc, /'--pipe'/);
    assert.match(extSrc, /\['--init',\s*'all'\]/);
});

test('extension.js registers v11 commands (lspCheck, hookInstall, federationImpact)', () => {
    const extSrc = fs.readFileSync(path.join(extRoot, 'src', 'extension.js'), 'utf8');
    assert.match(extSrc, /registerCommand\('tzero\.lspCheck'/);
    assert.match(extSrc, /'--check-arch'/);
    assert.match(extSrc, /registerCommand\('tzero\.hookInstall'/);
    assert.match(extSrc, /'--hook-install',\s*'all'/);
    assert.match(extSrc, /registerCommand\('tzero\.federationImpact'/);
    assert.match(extSrc, /showInputBox/);
    assert.match(extSrc, /'--federation',\s*'impact',\s*'--federation-symbol'/);
});

