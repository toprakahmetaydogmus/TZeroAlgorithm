# ⚡ T-Zero コンテキストアーキテクト & MCP サーバー (Token 削減エンジン)

<p align="center">
  <img src="https://raw.githubusercontent.com/toprakahmetaydogmus/TZeroAlgorithm/main/benchmark-site/favicon.svg" width="128" height="128" alt="T-Zero Logo" /><br>
  <b>Cursor、Claude Desktop、Windsurf、VS Code Copilot 対応の決定的 AST コード圧縮エンジン</b><br>
  <i>型定義とインターフェース契約を 100% 保持しながら、LLM コンテキストのトークン消費量を最大 95% 削減！</i>
</p>

<p align="center">
  <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm"><img src="https://img.shields.io/github/stars/toprakahmetaydogmus/TZeroAlgorithm?style=for-the-badge&logo=github&color=22c55e&label=GitHub%20Stars" alt="GitHub Stars" /></a>
  <a href="https://www.npmjs.com/package/tzero-mcp"><img src="https://img.shields.io/npm/dt/tzero-mcp?style=for-the-badge&logo=npm&color=cb3837&label=npm%20Downloads" alt="npm Downloads" /></a>
  <a href="https://pypi.org/project/tzero-mcp/"><img src="https://img.shields.io/pepy/dt/tzero-mcp?style=for-the-badge&logo=pypi&color=38bdf8&label=PyPI%20Downloads" alt="PyPI Downloads" /></a>
  <a href="https://open-vsx.org/extension/siber-akademi/tzero-vscode"><img src="https://img.shields.io/open-vsx/dt/siber-akademi/tzero-vscode?style=for-the-badge&logo=openvsx&color=8b5cf6&label=Open-VSX" alt="Open VSX Downloads" /></a>
  <a href="../LICENSE"><img src="https://img.shields.io/badge/License-AGPL--3.0--only-blue?style=for-the-badge" alt="License AGPL-3.0-only" /></a>
</p>

[English](../README.md) | [Türkçe](README.tr.md) | **日本語** | [简体中文](README.zh.md)

---

## 🌟 主な機能と特長

1. **決定的 AST 構文木プルーニング (DAG-AC):**
   - 従来のプロンプトでは関数の実装やループなどの余分なコードでトークン枠を浪費します。
   - T-Zero はローカルで構文木を解析し、クラス構造、関数シグネチャ、型契約のみ（例: `def compute(...) -> bool: ...`）を抽出。**85%〜95% のトークン削減**を実現します。
2. **100% ゼロリーク (Zero-Leak) セキュリティ監査:**
   - シャノンエントロピー ($H \ge 4.75$) 解析により、ハードコードされた API キーや機密情報をローカルで即座に検出。
   - 1 コマンドで安全に `.env` へ移行し、自動で `.gitignore` に追加します。
3. **AI ハルシネーション撲滅 (Reality-Lock):**
   - AI が提案したコードを適用する前に、実在しない架空のライブラリや関数の呼び出しを静的 AST で事前検証・排除します。
4. **15+ 言語ネイティブ対応 (Polyglot):**
   - Python、TypeScript、JavaScript、Rust、Go、C/C++、Java、C#、Swift、Kotlin、Dart、Solidity、Ruby、PHP、Scala、Elixir。
5. **完全ローカル & 永久無料 ($0 コスト):**
   - 有料 API や外部クラウド通信は一切不要。オフラインのミリ秒単位で高速動作します。

---

## ⚡ 30 秒クイックスタート

### 選択肢 A: npx による即時起動（インストール不要・推奨）
```bash
# MCP サーバーを直接起動 (stdio)
npx -y tzero-mcp@latest

# グローバル CLI インストール:
npm install -g tzero-mcp
```

### 選択肢 B: Python / PyPI からのインストール
```bash
pip install --upgrade tzero-mcp
```

### 選択肢 C: ワンライナー高速インストーラー
```bash
# Linux / macOS:
curl -fsSL https://raw.githubusercontent.com/toprakahmetaydogmus/TZeroAlgorithm/main/install.sh | bash

# Windows (PowerShell):
irm https://raw.githubusercontent.com/toprakahmetaydogmus/TZeroAlgorithm/main/install.ps1 | iex
```

### 選択肢 D: 全 IDE (Cursor / Claude / Windsurf / VS Code) の一括自動設定
```bash
tzero init
```

---

## 🔌 Cursor & Claude Desktop 設定方法

設定ファイルに以下を追記するだけで即座に連携可能です：

### 1. Cursor (`.cursor/mcp.json`)
```json
{
  "mcpServers": {
    "tzero": {
      "command": "npx",
      "args": ["-y", "tzero-mcp@latest"]
    }
  }
}
```

### 2. Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "tzero": {
      "command": "npx",
      "args": ["-y", "tzero-mcp@latest"]
    }
  }
}
```

---

## 📊 ベンチマーク検証 (Claude 3.5 Sonnet / GPT-4o / DeepSeek)

| 検証項目 (10,000 行コードベース) | 生のコード | T-Zero 圧縮後 | 削減率 | 1リクエストあたりの節約コスト |
| :--- | :---: | :---: | :---: | :---: |
| **AST 型シグネチャ抽出** | 128,450 Tokens | **7,820 Tokens** | **-93.9%** | **$0.36 / 回** |
| **大規模モジュール解析** | 542,100 Tokens | **28,140 Tokens** | **-94.8%** | **$1.54 / 回** |
| **Git Incremental PR Diff** | 45,200 Tokens | **1,850 Tokens** | **-95.9%** | **$0.13 / 回** |
| **レスポンス応答速度** | 12,400 ms | **1,150 ms** | **10.7倍 高速** | — |

---

## 🛠️ よく使う CLI コマンド

| コマンド | 説明 |
| :--- | :--- |
| `tzero --scan` | プロジェクト全体を走査し、AST コンテキストの概要を表示 |
| `tzero --watch` | ファイル保存時に自動で Cursor/Claude 向けコンテキストを再生成 |
| `tzero --audit` | 静的 AST コードスメルおよび機密情報漏洩を監査 |
| `tzero --vault --migrate` | ハードコードされた API キーを自動で `.env` へ移行 |
| `tzero review` | コミット前 / PR マージ前の自律的 Reality-Lock 検査 |
| `tzero demo` | 0.5 秒で AST 圧縮と Reality-Lock の動作を体験 |
| `tzero --web` | `http://localhost:8421` でダークモード開発者ダッシュボードを起動 |

---

## 🤝 開発者 & ライセンス

- **作者:** Toprak Ahmet Aydoğmuş ([Siber Akademi](https://github.com/toprakahmetaydogmus))
- **ライセンス:** AGPL-3.0-only
- T-Zero がお役に立ちましたら、ぜひ GitHub リポジトリへの **⭐ Star** をお願いいたします！

---

## 📈 スター推移 (Star History)

<div align="center">
  <a href="https://star-history.com/#toprakahmetaydogmus/TZeroAlgorithm&Date">
    <img src="https://api.star-history.com/svg?repos=toprakahmetaydogmus/TZeroAlgorithm&type=Date" alt="T-Zero Star History" width="100%" style="max-width: 800px; border-radius: 10px;">
  </a>
</div>

