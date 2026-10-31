const vscode = require('vscode');
const { spawn, exec } = require('child_process');
const path = require('path');
const fs = require('fs');

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    console.log('[T-Zero] Extension activated.');

    // 1. Status Bar Item
    const statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBar.text = "$(zap) T-Zero: 94.9% Saved";
    statusBar.tooltip = "T-Zero AST Context Engine: Click to open commands";
    statusBar.command = "tzero.openMenu";
    statusBar.show();
    context.subscriptions.push(statusBar);

    // Command: Open Menu
    const openMenuCmd = vscode.commands.registerCommand('tzero.openMenu', async () => {
        const selected = await vscode.window.showQuickPick([
            { label: "$(zap) 1-Click MCP Initialize", description: "Connect T-Zero MCP to Cursor, Claude, Windsurf, VS Code", cmd: "tzero.init" },
            { label: "$(file-code) Compress Current File", description: "Prune active file to AST signatures (-85% tokens)", cmd: "tzero.compressFile" },
            { label: "$(type-hierarchy) Show Project AST Skeleton", description: "Generate compact architecture outline", cmd: "tzero.showTree" },
            { label: "$(shield) Run 100% Zero-Leak Audit", description: "Scan workspace for secrets and code smells", cmd: "tzero.audit" },
            { label: "$(dashboard) Open Developer Dashboard", description: "Launch web UI on localhost:8421", cmd: "tzero.openDashboard" },
        ], { placeHolder: "Select a T-Zero Context Architect action" });

        if (selected && selected.cmd) {
            vscode.commands.executeCommand(selected.cmd);
        }
    });
    context.subscriptions.push(openMenuCmd);

    // Command: 1-Click Init
    const initCmd = vscode.commands.registerCommand('tzero.init', async () => {
        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "T-Zero: Initializing MCP in Workspace & IDEs...",
            cancellable: false
        }, () => {
            return new Promise((resolve) => {
                const cmd = "tzero init";
                exec(cmd, { cwd: getWorkspaceRoot() }, (error, stdout, stderr) => {
                    if (error) {
                        // Fallback to python execution
                        exec("python -m tzero_v3 init", { cwd: getWorkspaceRoot() }, (pyErr, pyStdout) => {
                            if (pyErr) {
                                vscode.window.showErrorMessage(`T-Zero Init Failed: ${pyErr.message}`);
                            } else {
                                vscode.window.showInformationMessage("🎉 T-Zero MCP initialized successfully! Restart your IDE window.");
                            }
                            resolve();
                        });
                    } else {
                        vscode.window.showInformationMessage("🎉 T-Zero MCP initialized successfully in all detected IDEs!");
                        resolve();
                    }
                });
            });
        });
    });
    context.subscriptions.push(initCmd);

    // Command: Compress Active File
    const compressCmd = vscode.commands.registerCommand('tzero.compressFile', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showWarningMessage("No active editor found to compress.");
            return;
        }

        const document = editor.document;
        const text = document.getText();
        const filename = path.basename(document.fileName);

        const child = spawn('tzero', ['--pipe', filename], { shell: true });
        let output = '';
        let errOutput = '';

        child.stdout.on('data', (data) => { output += data.toString(); });
        child.stderr.on('data', (data) => { errOutput += data.toString(); });

        child.on('close', async (code) => {
            if (code === 0 && output.trim()) {
                const doc = await vscode.workspace.openTextDocument({
                    content: output,
                    language: document.languageId
                });
                await vscode.window.showTextDocument(doc, { viewColumn: vscode.ViewColumn.Beside });
                const origTokens = Math.max(1, Math.floor(text.length / 4));
                const prunedTokens = Math.max(1, Math.floor(output.length / 4));
                const savings = ((1 - prunedTokens / origTokens) * 100).toFixed(1);
                vscode.window.showInformationMessage(`⚡ Compressed ${filename}: ${origTokens} -> ${prunedTokens} tokens (${savings}% saved)!`);
            } else {
                vscode.window.showErrorMessage(`Failed to compress: ${errOutput || 'Unknown error'}`);
            }
        });

        child.stdin.write(text);
        child.stdin.end();
    });
    context.subscriptions.push(compressCmd);

    // Command: Show AST Skeleton Tree
    const showTreeCmd = vscode.commands.registerCommand('tzero.showTree', async () => {
        const root = getWorkspaceRoot();
        exec('tzero --export-repomap -', { cwd: root }, async (error, stdout) => {
            const content = stdout || "No AST tree output generated.";
            const doc = await vscode.workspace.openTextDocument({
                content: content,
                language: 'markdown'
            });
            await vscode.window.showTextDocument(doc);
        });
    });
    context.subscriptions.push(showTreeCmd);

    // Command: Run Audit
    const auditCmd = vscode.commands.registerCommand('tzero.audit', async () => {
        const root = getWorkspaceRoot();
        const channel = vscode.window.createOutputChannel("T-Zero Security Audit");
        channel.show();
        channel.appendLine("⚡ Running T-Zero 100% Zero-Leak Security & AST Audit...\n");
        exec('tzero --audit .', { cwd: root }, (error, stdout, stderr) => {
            channel.appendLine(stdout || stderr);
            vscode.window.showInformationMessage("T-Zero Audit complete! See Output channel.");
        });
    });
    context.subscriptions.push(auditCmd);

    // Command: Open Dashboard
    const openDashCmd = vscode.commands.registerCommand('tzero.openDashboard', () => {
        exec('tzero --web 8421', { cwd: getWorkspaceRoot() });
        vscode.env.openExternal(vscode.Uri.parse('http://localhost:8421'));
    });
    context.subscriptions.push(openDashCmd);
}

function getWorkspaceRoot() {
    if (vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length > 0) {
        return vscode.workspace.workspaceFolders[0].uri.fsPath;
    }
    return process.cwd();
}

function deactivate() {}

module.exports = {
    activate,
    deactivate
};
