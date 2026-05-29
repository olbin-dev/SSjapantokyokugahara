# Sovereign Systems (SS) Technical Log

Sovereign Systems (SS) 技術日誌・技術ノートの公開リポジトリです。ローカルAI環境の構築記録や、自律実行エンジン Causa / Anchor DB の設計ドキュメントを管理しています。

## 📖 技術日誌リスト (Technical Logs)

### 1. 🪿 Goose → Ollama 接続完全ガイド
Open WebUI経由ではなく、OllamaにGooseを直接接続する際のネットワーク設定および Responses API 互換性問題の解決手順。
- **日本語版 (Markdown)**: [goose-ollama-guide.md](docs/troubleshooting/goose-ollama-guide.md)

### 2. 🛠️ Local LLM Gateway Setup
Mac Studio M2 Max (32GB) において、Gemma 4、Qwen 2.5、Phi-4 の Q8_0 量子化モデルをブラウザごとに切り替え、VRAM溢れを回避してオンデマンドで切り替えるゲートウェイ型並行運用の構築ログ。
- **日本語版 (Markdown)**: [local-llm-setup-ja.md](docs/local-llm/local-llm-setup-ja.md)

### 3. 📜 Project Manifesto (Anchor LLM & Causa)
LLMの非決定的な実行プランを、人間が承認（Enter打鍵）した過去の「判例」に基づき決定論的に再現するコア思想およびアーキテクチャ定義。
- **英語版 (Markdown)**: [anchor-llm-causa-v1.md](docs/manifesto/anchor-llm-causa-v1.md)
- **日本語版 (Markdown)**: [anchor-llm-causa-v1-ja.md](docs/manifesto/anchor-llm-causa-v1-ja.md)

### 4. 🎯 Milestone 1: Causa Core Specification
因果関係データベースの SQLite スキーマ設計、判定ロジック関数、および実行を伴わないシミュレーションテストの実装仕様。
- **英語版 (Markdown)**: [milestone-1-causa-core.md](docs/milestones/milestone-1-causa-core.md)
- **日本語版 (Markdown)**: [milestone-1-causa-core-ja.md](docs/milestones/milestone-1-causa-core-ja.md)

### 5. 🏷️ Release Notes v1.0-alpha
Causa Core ライブラリのアルファバージョンリリース内容と、安全境界（OS実行や特権昇格の非実装）に関する制約。
- **英語版 (Markdown)**: [v1.0-alpha.md](docs/releases/v1.0-alpha.md)
- **日本語版 (Markdown)**: [v1.0-alpha-ja.md](docs/releases/v1.0-alpha-ja.md)

---

## 🪿 Goose → Ollama Troubleshooting Guide Interactive UI
<iframe src="https://claude.site/public/artifacts/05a5fe94-33e5-4706-a822-b0421fcb3bf2/embed" title="Claude Artifact" width="100%" height="600" frameborder="0" allow="clipboard-write"></iframe>
