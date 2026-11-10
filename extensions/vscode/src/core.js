'use strict';

/**
 * Pure, VS Code-independent helper core for T-Zero VS Code / Cursor Extension.
 */

function resolveExecutable(configuredPath) {
    if (typeof configuredPath === 'string' && configuredPath.trim().length > 0) {
        return configuredPath.trim();
    }
    return 'tzero';
}

function quoteTerminalArg(arg, platform) {
    const plat = platform || process.platform;
    const raw = String(arg === undefined || arg === null ? '' : arg);
    if (plat === 'win32') {
        return `'${raw.replace(/'/g, "''")}'`;
    }
    return `'${raw.replace(/'/g, "'\\''")}'`;
}

function estimateTokenCount(text) {
    if (!text || typeof text !== 'string') {
        return 0;
    }
    return Math.max(1, Math.ceil(text.length / 4));
}

function parseScanJson(stdout) {
    if (!stdout || typeof stdout !== 'string') {
        return null;
    }
    const startIdx = stdout.indexOf('{');
    const endIdx = stdout.lastIndexOf('}');
    if (startIdx === -1 || endIdx <= startIdx) {
        return null;
    }
    try {
        const parsed = JSON.parse(stdout.slice(startIdx, endIdx + 1));
        if (!parsed || typeof parsed.total_files !== 'number') {
            return null;
        }
        return parsed;
    } catch (_) {
        return null;
    }
}

function formatCompactTokens(tokens) {
    const n = Number(tokens) || 0;
    if (n >= 1000000) {
        return `${(n / 1000000).toFixed(1)}M`;
    }
    if (n >= 1000) {
        return `${(n / 1000).toFixed(1)}k`;
    }
    return `${n}`;
}

function formatStatusBar(scanMetrics, activeFileStats) {
    if (!scanMetrics || typeof scanMetrics.savings_pct !== 'number') {
        const fileNote = activeFileStats && activeFileStats.fileName
            ? ` | ${activeFileStats.fileName} (${activeFileStats.symbolCount || 0} symbols)`
            : '';
        return {
            text: '$(zap) T-Zero: Scan Workspace',
            tooltip: `Click to open T-Zero Command Center or refresh live AST telemetry${fileNote}`
        };
    }

    const pct = Number(scanMetrics.savings_pct).toFixed(1);
    const pruned = formatCompactTokens(scanMetrics.pruned_tokens);
    const raw = formatCompactTokens(scanMetrics.raw_tokens);
    const fileDetail = activeFileStats && activeFileStats.fileName
        ? `\nActive File: ${activeFileStats.fileName} (${activeFileStats.symbolCount || 0} symbols)`
        : '';

    return {
        text: `$(zap) T-Zero: ${pct}% Saved`,
        tooltip: [
            `Workspace: ${scanMetrics.total_files || 0} files`,
            `AST Budget: ~${pruned} vs ${raw} raw tokens (${pct}% saved)${fileDetail}`,
            'Click for Command Center'
        ].join('\n')
    };
}

const DECL_PATTERN = /^\s*(?:export\s+(?:default\s+|async\s+)?)?(?:public\s+|private\s+|protected\s+|static\s+|abstract\s+|async\s+|pub(?:\([^)]*\))?\s+)*(?:class|interface|struct|enum|trait|impl|fn|func|function|def|contract|type)\s+([A-Za-z_][A-Za-z0-9_]*)/;

function isIndentLanguage(languageId) {
    return ['python', 'ruby', 'coffeescript'].includes(String(languageId || '').toLowerCase());
}

function findSymbolEndLine(lines, startLine, useIndent) {
    const startText = lines[startLine] || '';
    if (useIndent) {
        const baseIndent = startText.length - startText.trimStart().length;
        let lastBodyLine = startLine;
        for (let j = startLine + 1; j < lines.length; j++) {
            const cur = lines[j];
            if (!cur.trim()) {
                continue;
            }
            const curIndent = cur.length - cur.trimStart().length;
            if (curIndent <= baseIndent) {
                return lastBodyLine;
            }
            lastBodyLine = j;
        }
        return Math.max(startLine, lastBodyLine);
    }

    let depth = 0;
    let opened = false;
    let inBlockComment = false;
    for (let j = startLine; j < lines.length; j++) {
        const line = lines[j];
        let quoteChar = null;
        for (let k = 0; k < line.length; k++) {
            const ch = line[k];
            const next = line[k + 1];
            if (inBlockComment) {
                if (ch === '*' && next === '/') {
                    inBlockComment = false;
                    k++;
                }
                continue;
            }
            if (quoteChar) {
                if (ch === '\\') {
                    k++;
                    continue;
                }
                if (ch === quoteChar) {
                    quoteChar = null;
                }
                continue;
            }
            if (ch === '/' && next === '/') {
                break;
            }
            if (ch === '/' && next === '*') {
                inBlockComment = true;
                k++;
                continue;
            }
            if (ch === '"' || ch === "'" || ch === '`') {
                quoteChar = ch;
                continue;
            }
            if (ch === '{') {
                depth++;
                opened = true;
            } else if (ch === '}') {
                depth--;
                if (opened && depth <= 0) {
                    return j;
                }
            }
        }
    }
    return Math.min(lines.length - 1, startLine + 10);
}

function computeCodeLensMetrics(text, languageId) {
    if (!text || typeof text !== 'string') {
        return [];
    }
    const lines = text.split(/\r?\n/);
    const useIndent = isIndentLanguage(languageId);
    const results = [];

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const m = line.match(DECL_PATTERN);
        if (!m) {
            continue;
        }
        const name = m[1];
        const endLine = findSymbolEndLine(lines, i, useIndent);
        const blockText = lines.slice(i, endLine + 1).join('\n');
        const sigText = line.trim();
        const rawTokens = estimateTokenCount(blockText);
        const signatureTokens = estimateTokenCount(sigText);
        const savingsPct = rawTokens > 0
            ? Math.max(0, Math.round((1 - signatureTokens / rawTokens) * 100))
            : 0;

        results.push({
            line: i,
            endLine,
            linesCount: Math.max(1, endLine - i + 1),
            name,
            rawTokens,
            signatureTokens,
            savingsPct,
            contract: sigText
        });
    }
    return results;
}

function buildSymbolContract(text, lineNum, explainSymbols) {
    const targetOneBased = Number(lineNum) + 1;
    if (Array.isArray(explainSymbols) && explainSymbols.length > 0) {
        const exact = explainSymbols.find((s) => Number(s.lineno) === targetOneBased)
            || explainSymbols.find((s) => Math.abs(Number(s.lineno) - targetOneBased) <= 2);
        if (exact && Array.isArray(exact.signatures) && exact.signatures.length > 0) {
            const docComment = exact.docstring ? `// ${exact.docstring}\n` : '';
            return `${docComment}${exact.signatures.join('\n')}`;
        }
    }

    if (!text || typeof text !== 'string') {
        return '';
    }
    const lines = text.split(/\r?\n/);
    const start = Math.max(0, Math.min(lines.length - 1, Number(lineNum) || 0));
    const collected = [];
    for (let i = start; i < Math.min(lines.length, start + 12); i++) {
        const trimmed = lines[i].trimEnd();
        collected.push(trimmed);
        if (trimmed.includes('{') || trimmed.endsWith(':') || trimmed.endsWith(';')) {
            break;
        }
    }
    return `// AST Contract\n${collected.join('\n')}`;
}

function escapeHtml(str) {
    return String(str || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function buildSidebarHtml(state) {
    const s = state || {};
    const m = s.metrics || {};
    const totalFiles = m.total_files !== undefined ? m.total_files : '-';
    const rawTok = m.raw_tokens !== undefined ? formatCompactTokens(m.raw_tokens) : '-';
    const prunedTok = m.pruned_tokens !== undefined ? formatCompactTokens(m.pruned_tokens) : '-';
    const savingsPct = m.savings_pct !== undefined ? `${Number(m.savings_pct).toFixed(1)}%` : 'Ready';
    const lastCmd = escapeHtml(s.lastCommand || 'None');
    const lastOut = escapeHtml(s.lastOutput || 'Click Refresh Telemetry to scan this workspace.');

    const actions = [
        { id: 'tzero.refreshMetrics', label: 'Refresh Telemetry' },
        { id: 'tzero.init', label: 'Initialize Workspace (--init)' },
        { id: 'tzero.showTree', label: 'Export RepoMap Tree' },
        { id: 'tzero.audit', label: 'Zero-Leak Secret Audit' },
        { id: 'tzero.explain', label: 'Explain Active File' },
        { id: 'tzero.debt', label: 'Tech Debt & Health (--debt)' },
        { id: 'tzero.budget', label: 'Budget Optimizer (--budget)' },
        { id: 'tzero.contracts', label: 'API Contracts (--contracts)' },
        { id: 'tzero.golden', label: 'Golden Verify (--golden)' },
        { id: 'tzero.mutate', label: 'AST Mutation Test (--mutate)' },
        { id: 'tzero.bridge', label: 'Polyglot Bridge (--bridge)' },
        { id: 'tzero.mergeHeal', label: 'Merge Healer (--merge-heal)' },
        { id: 'tzero.lspCheck', label: 'Arch & Zero-Leak Check (--check-arch)' },
        { id: 'tzero.hookInstall', label: 'Install AI Hooks (--hook-install all)' },
        { id: 'tzero.federationImpact', label: 'Federation Impact (--federation)' },
        { id: 'tzero.openDashboard', label: 'Launch Web Dashboard' }
    ];

    const buttonsHtml = actions
        .map((a) => `<button class="cmd-btn" data-cmd="${escapeHtml(a.id)}">${escapeHtml(a.label)}</button>`)
        .join('\n                ');

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline';" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <style>
        body {
            font-family: var(--vscode-font-family);
            color: var(--vscode-foreground);
            background: var(--vscode-sideBar-background, var(--vscode-editor-background));
            padding: 10px;
            font-size: 12px;
        }
        .card {
            border: 1px solid var(--vscode-panel-border, #333);
            border-radius: 6px;
            padding: 10px;
            margin-bottom: 10px;
            background: var(--vscode-editorWidget-background, rgba(128,128,128,0.08));
        }
        .kpi-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-top: 6px;
        }
        .kpi {
            padding: 6px;
            border-radius: 4px;
            background: var(--vscode-input-background, rgba(0,0,0,0.2));
        }
        .kpi-label { font-size: 10px; opacity: 0.75; }
        .kpi-val { font-size: 14px; font-weight: 700; margin-top: 2px; }
        .actions { display: flex; flex-direction: column; gap: 6px; }
        .cmd-btn {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 6px 10px;
            border-radius: 4px;
            cursor: pointer;
            text-align: left;
            font-size: 12px;
        }
        .cmd-btn:hover { background: var(--vscode-button-hoverBackground); }
        pre {
            white-space: pre-wrap;
            word-break: break-word;
            font-family: var(--vscode-editor-font-family, monospace);
            font-size: 11px;
            background: var(--vscode-input-background, rgba(0,0,0,0.2));
            padding: 8px;
            border-radius: 4px;
            max-height: 200px;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <div class="card">
        <strong>T-Zero AST Telemetry</strong>
        <div class="kpi-grid">
            <div class="kpi"><div class="kpi-label">AST Reduction</div><div class="kpi-val">${escapeHtml(savingsPct)}</div></div>
            <div class="kpi"><div class="kpi-label">Tracked Files</div><div class="kpi-val">${escapeHtml(String(totalFiles))}</div></div>
            <div class="kpi"><div class="kpi-label">Pruned Tokens</div><div class="kpi-val">${escapeHtml(prunedTok)}</div></div>
            <div class="kpi"><div class="kpi-label">Raw Tokens</div><div class="kpi-val">${escapeHtml(rawTok)}</div></div>
        </div>
    </div>
    <div class="card">
        <strong>Command Dispatch</strong>
        <div class="actions" style="margin-top:8px;">
                ${buttonsHtml}
        </div>
    </div>
    <div class="card">
        <div><strong>Last Run:</strong> <code>${lastCmd}</code></div>
        <pre>${lastOut}</pre>
    </div>
    <script>
        const vscode = acquireVsCodeApi();
        document.querySelectorAll('.cmd-btn').forEach((btn) => {
            btn.addEventListener('click', () => {
                vscode.postMessage({ type: 'runCommand', command: btn.getAttribute('data-cmd') });
            });
        });
    </script>
</body>
</html>`;
}

module.exports = {
    resolveExecutable,
    quoteTerminalArg,
    estimateTokenCount,
    parseScanJson,
    formatCompactTokens,
    formatStatusBar,
    computeCodeLensMetrics,
    buildSymbolContract,
    buildSidebarHtml
};

