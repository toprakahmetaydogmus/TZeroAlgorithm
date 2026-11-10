'use strict';

const vscode = require('vscode');
const { execFile } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const core = require('./core');

function getConfig() {
    return vscode.workspace.getConfiguration('tzero');
}

function getExecutablePath() {
    return core.resolveExecutable(getConfig().get('executablePath'));
}

function getWorkspaceRoot() {
    const folders = vscode.workspace.workspaceFolders;
    if (folders && folders.length > 0) {
        return folders[0].uri.fsPath;
    }
    return undefined;
}

function runTZeroCli(args, cwd, stdinText) {
    const exe = getExecutablePath();
    return new Promise((resolve, reject) => {
        const child = execFile(
            exe,
            args,
            { cwd: cwd || os.tmpdir(), maxBuffer: 8 * 1024 * 1024 },
            (error, stdout, stderr) => {
                if (error && !stdout) {
                    reject(new Error(stderr || error.message));
                    return;
                }
                resolve({ stdout: stdout || '', stderr: stderr || '', exitCode: error ? error.code : 0 });
            }
        );
        if (stdinText !== undefined && stdinText !== null && child.stdin) {
            child.stdin.write(stdinText);
            child.stdin.end();
        }
    });
}

function runInTerminal(args) {
    const exe = getExecutablePath();
    const cmdLine = [core.quoteTerminalArg(exe), ...args.map((a) => core.quoteTerminalArg(a))].join(' ');
    const term = vscode.window.createTerminal('T-Zero Architect');
    term.show();
    term.sendText(cmdLine);
}

function activate(context) {
    const outputChannel = vscode.window.createOutputChannel('T-Zero Architect');
    const codeLensEmitter = new vscode.EventEmitter();
    const explainCache = new Map();

    const state = {
        metrics: null,
        activeFileStats: null,
        lastCommand: 'None',
        lastOutput: 'Initializing T-Zero workspace telemetry...',
        sidebarView: null
    };

    const statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBar.command = 'tzero.openMenu';
    statusBar.show();

    function updateUiTelemetry() {
        const bar = core.formatStatusBar(state.metrics, state.activeFileStats);
        statusBar.text = bar.text;
        statusBar.tooltip = bar.tooltip;
        if (state.sidebarView) {
            state.sidebarView.webview.html = core.buildSidebarHtml(state);
        }
    }

    function updateActiveEditorMetrics(editor) {
        if (!editor || !editor.document || editor.document.isUntitled) {
            state.activeFileStats = null;
            updateUiTelemetry();
            return;
        }
        const doc = editor.document;
        const symbols = core.computeCodeLensMetrics(doc.getText(), doc.languageId);
        state.activeFileStats = {
            fileName: path.basename(doc.fileName),
            symbolCount: symbols.length
        };
        updateUiTelemetry();
    }

    async function refreshWorkspaceMetrics() {
        const wsRoot = getWorkspaceRoot();
        if (!wsRoot) {
            updateUiTelemetry();
            return;
        }
        try {
            const res = await runTZeroCli(['--scan', wsRoot, '--format', 'json'], wsRoot);
            const parsed = core.parseScanJson(res.stdout);
            if (parsed) {
                state.metrics = parsed;
                state.lastCommand = 'tzero --scan --format json';
                state.lastOutput = `Scanned ${parsed.total_files} files | ~${parsed.pruned_tokens} vs ${parsed.raw_tokens} tokens (${parsed.savings_pct}% saved)`;
            }
        } catch (err) {
            state.lastOutput = `Scan telemetry unavailable: ${err.message}`;
        }
        updateUiTelemetry();
    }

    async function executeOutputCommand(label, args, cwd, showDocLanguage) {
        try {
            const res = await runTZeroCli(args, cwd || getWorkspaceRoot());
            const combined = (res.stdout || res.stderr || '').trim();
            state.lastCommand = `tzero ${args.join(' ')}`;
            state.lastOutput = combined.slice(0, 4000) || '(no output)';
            outputChannel.clear();
            outputChannel.appendLine(`$ ${getExecutablePath()} ${args.join(' ')}`);
            outputChannel.appendLine(combined);
            outputChannel.show(true);
            updateUiTelemetry();
            if (showDocLanguage && combined) {
                const doc = await vscode.workspace.openTextDocument({ content: combined, language: showDocLanguage });
                await vscode.window.showTextDocument(doc);
            } else {
                vscode.window.showInformationMessage(`T-Zero: ${label} complete.`);
            }
        } catch (err) {
            state.lastCommand = `tzero ${args.join(' ')}`;
            state.lastOutput = `Error: ${err.message}`;
            updateUiTelemetry();
            vscode.window.showErrorMessage(`T-Zero ${label} failed: ${err.message}`);
        }
    }

    const sidebarProvider = {
        resolveWebviewView(webviewView) {
            state.sidebarView = webviewView;
            webviewView.webview.options = { enableScripts: true };
            webviewView.webview.html = core.buildSidebarHtml(state);
            webviewView.webview.onDidReceiveMessage((msg) => {
                if (msg && msg.type === 'runCommand' && msg.command) {
                    vscode.commands.executeCommand(msg.command);
                }
            });
        }
    };

    const refreshMetricsCmd = vscode.commands.registerCommand('tzero.refreshMetrics', async () => {
        await refreshWorkspaceMetrics();
    });

    const openMenuCmd = vscode.commands.registerCommand('tzero.openMenu', async () => {
        const items = [
            { label: '$(sync) Refresh Live AST Telemetry', command: 'tzero.refreshMetrics' },
            { label: '$(rocket) Initialize Workspace (tzero --init)', command: 'tzero.init' },
            { label: '$(list-tree) View Workspace Context Tree', command: 'tzero.showTree' },
            { label: '$(shield) Zero-Leak Secret Audit', command: 'tzero.audit' },
            { label: '$(file-code) Explain Active File (--explain)', command: 'tzero.explain' },
            { label: '$(file-zip) Compress Active File AST to Clipboard', command: 'tzero.compressFile' },
            { label: '$(pulse) Tech Debt & Code Health (--debt)', command: 'tzero.debt' },
            { label: '$(package) Token Budget & Certificate (--budget)', command: 'tzero.budget' },
            { label: '$(verified) Public API Contracts Audit (--contracts)', command: 'tzero.contracts' },
            { label: '$(checklist) Golden AST Signature Baseline (--golden)', command: 'tzero.golden' },
            { label: '$(beaker) AST Mutation Test Suite (--mutate)', command: 'tzero.mutate' },
            { label: '$(arrow-swap) Polyglot Type Bridge (--bridge)', command: 'tzero.bridge' },
            { label: '$(git-merge) Semantic 3-Way Merge Healer (--merge-heal)', command: 'tzero.mergeHeal' },
            { label: '$(eye) Autonomous PR Review (--review)', command: 'tzero.review' },
            { label: '$(watch) Live AST Context Watcher (--watch)', command: 'tzero.watch' },
            { label: '$(tools) System Diagnostics (--doctor)', command: 'tzero.doctor' },
            { label: '$(globe) Launch Local Web Dashboard', command: 'tzero.openDashboard' }
        ];
        const picked = await vscode.window.showQuickPick(items, { placeHolder: 'T-Zero Context Architect Command Center (v10.9.0)' });
        if (picked) {
            vscode.commands.executeCommand(picked.command);
        }
    });

    const initCmd = vscode.commands.registerCommand('tzero.init', async () => {
        const wsRoot = getWorkspaceRoot();
        if (!wsRoot) {
            vscode.window.showErrorMessage('Please open a workspace folder before running T-Zero init.');
            return;
        }
        await executeOutputCommand('Workspace Init', ['--init', 'all'], wsRoot);
        await refreshWorkspaceMetrics();
    });

    const compressFileCmd = vscode.commands.registerCommand('tzero.compressFile', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showWarningMessage('No active editor found to compress.');
            return;
        }
        const filePath = editor.document.fileName;
        const rawText = editor.document.getText();
        const res = await runTZeroCli(['--pipe', path.basename(filePath)], path.dirname(filePath), rawText).catch((err) => {
            vscode.window.showErrorMessage(`T-Zero compress failed: ${err.message}`);
            return null;
        });
        if (res && res.stdout) {
            await vscode.env.clipboard.writeText(res.stdout);
            vscode.window.showInformationMessage(`T-Zero compressed AST of ${path.basename(filePath)} copied to clipboard.`);
        }
    });

    const compressSelCmd = vscode.commands.registerCommand('tzero.compressSelection', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.selection.isEmpty) {
            vscode.window.showWarningMessage('Please select a code block to compress.');
            return;
        }
        const selectedText = editor.document.getText(editor.selection);
        const ext = path.extname(editor.document.fileName) || '.py';
        try {
            const res = await runTZeroCli(['--pipe', `selection${ext}`], os.tmpdir(), selectedText);
            await vscode.env.clipboard.writeText(res.stdout);
            vscode.window.showInformationMessage('T-Zero compressed AST selection copied to clipboard.');
        } catch (err) {
            vscode.window.showErrorMessage(`T-Zero selection compress failed: ${err.message}`);
        }
    });

    const showTreeCmd = vscode.commands.registerCommand('tzero.showTree', async () => {
        const wsRoot = getWorkspaceRoot();
        if (!wsRoot) {
            vscode.window.showErrorMessage('Please open a workspace folder.');
            return;
        }
        await executeOutputCommand('Context RepoMap', ['--export-repomap', '-', '--dir', wsRoot], wsRoot, 'markdown');
    });

    const auditCmd = vscode.commands.registerCommand('tzero.audit', async () => {
        const wsRoot = getWorkspaceRoot() || '.';
        await executeOutputCommand('Zero-Leak Security Audit', ['--audit', wsRoot], wsRoot);
    });

    const openDashCmd = vscode.commands.registerCommand('tzero.openDashboard', () => {
        runInTerminal(['--web']);
    });

    const reviewCmd = vscode.commands.registerCommand('tzero.review', () => {
        const wsRoot = getWorkspaceRoot() || '.';
        runInTerminal(['--review', '--dir', wsRoot]);
    });

    const watchCmd = vscode.commands.registerCommand('tzero.watch', () => {
        const wsRoot = getWorkspaceRoot() || '.';
        runInTerminal(['--watch', wsRoot]);
    });

    const doctorCmd = vscode.commands.registerCommand('tzero.doctor', async () => {
        const wsRoot = getWorkspaceRoot() || '.';
        await executeOutputCommand('Doctor Diagnostics', ['--doctor'], wsRoot);
    });

    const explainCmd = vscode.commands.registerCommand('tzero.explain', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showWarningMessage('No active editor found for T-Zero Explain.');
            return;
        }
        const filePath = editor.document.fileName;
        await executeOutputCommand('Architectural Passport', ['--explain', filePath, '--format', 'json'], path.dirname(filePath), 'json');
    });

    const debtCmd = vscode.commands.registerCommand('tzero.debt', async () => {
        const wsRoot = getWorkspaceRoot() || '.';
        await executeOutputCommand('Technical Debt Analysis', ['--debt', wsRoot], wsRoot);
    });

    const budgetCmd = vscode.commands.registerCommand('tzero.budget', async () => {
        const wsRoot = getWorkspaceRoot() || '.';
        await executeOutputCommand('Token Budget Optimizer', ['--budget', wsRoot], wsRoot);
    });

    const contractsCmd = vscode.commands.registerCommand('tzero.contracts', async () => {
        const wsRoot = getWorkspaceRoot() || '.';
        await executeOutputCommand('Public API Contract Audit', ['--contracts', 'HEAD~1', '--dir', wsRoot], wsRoot);
    });

    const goldenCmd = vscode.commands.registerCommand('tzero.golden', async () => {
        const wsRoot = getWorkspaceRoot() || '.';
        const action = await vscode.window.showQuickPick(['verify', 'generate', 'update'], {
            placeHolder: 'Select Golden AST Baseline Action'
        });
        if (!action) {
            return;
        }
        await executeOutputCommand(`Golden ${action}`, ['--golden', action, '--dir', wsRoot], wsRoot);
    });

    const mutateCmd = vscode.commands.registerCommand('tzero.mutate', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showWarningMessage('Open a file to run AST mutation testing.');
            return;
        }
        const filePath = editor.document.fileName;
        await executeOutputCommand('AST Mutation Suite', ['--mutate', filePath], path.dirname(filePath));
    });

    const bridgeCmd = vscode.commands.registerCommand('tzero.bridge', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showWarningMessage('Open a file to run Polyglot Type Bridge.');
            return;
        }
        const lang = await vscode.window.showQuickPick(['ts', 'rust', 'go', 'kt', 'swift', 'all'], {
            placeHolder: 'Select Target Polyglot Schema Language'
        });
        if (!lang) {
            return;
        }
        const filePath = editor.document.fileName;
        await executeOutputCommand(`Polyglot Bridge (${lang})`, ['--bridge', filePath, '--bridge-lang', lang], path.dirname(filePath), lang === 'ts' ? 'typescript' : 'markdown');
    });

    const mergeHealCmd = vscode.commands.registerCommand('tzero.mergeHeal', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showWarningMessage('Open a conflicted file to run T-Zero Semantic Merge Healer.');
            return;
        }
        const filePath = editor.document.fileName;
        await executeOutputCommand('Semantic Merge Healer', ['--merge-heal', filePath], path.dirname(filePath));
    });

    const copyContractCmd = vscode.commands.registerCommand('tzero.copySymbolContract', async (filePath, lineNum) => {
        const doc = vscode.workspace.textDocuments.find((d) => d.fileName === filePath)
            || (vscode.window.activeTextEditor && vscode.window.activeTextEditor.document);
        const text = doc ? doc.getText() : '';
        let explainSymbols = explainCache.get(filePath) || null;
        if (!explainSymbols && filePath) {
            try {
                const res = await runTZeroCli(['--explain', filePath, '--format', 'json'], path.dirname(filePath));
                const parsed = JSON.parse(res.stdout);
                if (parsed && Array.isArray(parsed.symbols)) {
                    explainSymbols = parsed.symbols;
                    explainCache.set(filePath, explainSymbols);
                }
            } catch (_) {
                explainSymbols = null;
            }
        }
        const contract = core.buildSymbolContract(text, lineNum, explainSymbols);
        await vscode.env.clipboard.writeText(contract);
        vscode.window.showInformationMessage('Copied symbol AST contract to clipboard.');
    });

    const codeLensProvider = {
        onDidChangeCodeLenses: codeLensEmitter.event,
        provideCodeLenses(document) {
            const symbols = core.computeCodeLensMetrics(document.getText(), document.languageId);
            const lenses = [];
            for (const sym of symbols) {
                const range = new vscode.Range(sym.line, 0, sym.line, 0);
                lenses.push(new vscode.CodeLens(range, {
                    title: `⚡ ~${sym.rawTokens} tok → ${sym.signatureTokens} sig (${sym.savingsPct}% saved)`,
                    tooltip: `Block spans ${sym.linesCount} lines (L${sym.line + 1}-L${sym.endLine + 1}).`,
                    command: ''
                }));
                lenses.push(new vscode.CodeLens(range, {
                    title: '📋 Copy AST Contract',
                    tooltip: `Copy pruned AST contract for ${sym.name}`,
                    command: 'tzero.copySymbolContract',
                    arguments: [document.fileName, sym.line]
                }));
            }
            return lenses;
        }
    };

    const selector = [
        { language: 'python', scheme: 'file' },
        { language: 'typescript', scheme: 'file' },
        { language: 'javascript', scheme: 'file' },
        { language: 'typescriptreact', scheme: 'file' },
        { language: 'javascriptreact', scheme: 'file' },
        { language: 'rust', scheme: 'file' },
        { language: 'go', scheme: 'file' },
        { language: 'java', scheme: 'file' },
        { language: 'csharp', scheme: 'file' },
        { language: 'cpp', scheme: 'file' },
        { language: 'c', scheme: 'file' }
    ];

    context.subscriptions.push(
        outputChannel,
        codeLensEmitter,
        statusBar,
        vscode.window.registerWebviewViewProvider('tzero.cockpitView', sidebarProvider),
        vscode.languages.registerCodeLensProvider(selector, codeLensProvider),
        vscode.window.onDidChangeActiveTextEditor((editor) => updateActiveEditorMetrics(editor)),
        vscode.workspace.onDidSaveTextDocument((doc) => {
            explainCache.delete(doc.fileName);
            codeLensEmitter.fire();
            refreshWorkspaceMetrics();
        }),
        refreshMetricsCmd,
        openMenuCmd,
        initCmd,
        compressFileCmd,
        compressSelCmd,
        showTreeCmd,
        auditCmd,
        openDashCmd,
        reviewCmd,
        watchCmd,
        doctorCmd,
        explainCmd,
        debtCmd,
        budgetCmd,
        contractsCmd,
        goldenCmd,
        mutateCmd,
        bridgeCmd,
        mergeHealCmd,
        copyContractCmd
    );

    updateActiveEditorMetrics(vscode.window.activeTextEditor);
    refreshWorkspaceMetrics();

    if (getConfig().get('autoInitOnOpen')) {
        const wsRoot = getWorkspaceRoot();
        if (wsRoot && !fs.existsSync(path.join(wsRoot, '.tzero')) && !fs.existsSync(path.join(wsRoot, '.mcp.json'))) {
            runTZeroCli(['--init', 'all'], wsRoot).then(() => refreshWorkspaceMetrics()).catch(() => {});
        }
    }
}

function deactivate() {}

module.exports = {
    activate,
    deactivate
};
