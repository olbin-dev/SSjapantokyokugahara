# 🪿 Goose → Ollama 接続完全ガイド

Open WebUI経由ではなく、OllamaにGooseを直接接続する際のトラブルシューティング記録。

- **Goose**: v1.26.1
- **Open WebUI**: 🐳 (Docker等)
- **Ollama**: 🦙 (ローカル推論エンジン)
- **日付**: 2026-03-03

---

## 1. 環境構成

### ネットワーク構成

| ホスト | IP | 役割 | 備考 |
|---|---|---|---|
| CLIENT | 192.168.1.x | **Goose実行マシン** | Apple Silicon Mac |
| SERVER | 192.168.1.y | **Ollama / Open WebUI** | 大容量RAM Mac |
| PROXY | 192.168.1.z | liteLLM proxy / n8n | Apple Silicon Mac |

### サービスとポート

| サービス | ポート | 用途 |
|---|---|---|
| Open WebUI | 18789 | Web UI + OpenAI互換API |
| Ollama | 11434 | LLM推論エンジン（直接接続） |

---

## 2. 根本原因

### 🚨 主要原因 (PRIMARY CAUSE)
**Goose v1.26.1 がデフォルトで OpenAI Responses API を使用する**

Goose 1.26以降、OpenAIの新しい `/v1/responses` エンドポイントをデフォルトで使用します。Open WebUI はこのエンドポイントを実装していないため、**405 Method Not Allowed** が返り続けます。

### ⚠️ 二次的要因 (SECONDARY CAUSE)
**Ollamaがデフォルトでlocalhostのみにバインド**

Ollamaはデフォルトで `127.0.0.1:11434` しか待ち受けないため、他マシンから直接アクセスできません。`OLLAMA_HOST=0.0.0.0:11434` の設定が必要です。

### エラーの変遷

| エラー | 原因 | 状態 |
|---|---|---|
| 401 Unauthorized | JWTトークン期限切れ / キー未設定 | 解決 |
| JSON parse error | OPENAI_BASE_PATHが `api/chat/completions`（重複） | 解決 |
| 405 Method Not Allowed | Responses API非対応 + OllamaへのURL誤り | 解決 |
| Connection refused | Ollamaがlocalhostのみバインド | 解決 |

---

## 3. 解決ステップ詳細

### Step 1: Open WebUI APIキーの取得
Open WebUIのアカウント画面にAPIキーセクションが表示されない場合、Admin設定で有効化が必要。

```bash
# Admin Panel → Settings → General → Enable API Keys をON

# APIキー発行UIが動作しない場合、サインインAPIで直接JWTを取得
curl -X POST http://192.168.1.y:18789/api/v1/auths/signin \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"yourpassword"}'

# レスポンスの "token" フィールドを取得
# "expires_at": null → 無期限トークン
# "api_keys": false → ここが原因でAPIキー作成UIが機能しない
```

### Step 2: Gooseの設定 — `OPENAI_BASE_PATH` の修正
Gooseは `OPENAI_HOST + OPENAI_BASE_PATH + /chat/completions` でURLを組み立てます。

```yaml
# ❌ 誤り — URLが二重になる
OPENAI_BASE_PATH: api/chat/completions
# → http://host/api/chat/completions/chat/completions

# ✅ 正しい
OPENAI_BASE_PATH: /api/v1
# → http://host/api/v1/chat/completions
```

### Step 3: curl で接続確認
Gooseに任せる前に、必ずcurlでエンドポイントが正常か確認する。

```bash
# モデル一覧確認
curl http://192.168.1.y:18789/api/v1/models \
  -H "Authorization: Bearer YOUR_TOKEN"

# Chat completions 確認
curl -X POST http://192.168.1.y:18789/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"model":"qwen2.5:7b-instruct","messages":[{"role":"user","content":"hi"}]}'

# ✅ curlは成功 → Goose側の問題と確定
```

### Step 4: Goose v1.26.1 の Responses API 問題を迂回
**Goose v1.26以降はOpenAI Responses APIをデフォルト使用**。Open WebUIは未対応のため405エラーが出続ける。  
解決策：GooseプロバイダーをOpenAIからOllamaに切り替える。

```yaml
# goose configure → Ollama を選択
# または config.yaml を直接編集

# ❌ 削除する設定
GOOSE_PROVIDER: openai
OPENAI_HOST: http://192.168.1.y:18789
OPENAI_BASE_PATH: /api/v1
OPENAI_API_KEY: sk-...

# ✅ 追加する設定
GOOSE_PROVIDER: ollama
GOOSE_MODEL: qwen2.5:7b-instruct
OLLAMA_HOST: http://192.168.1.y:11434
```

### Step 5: NRT Ollama のネットワーク公開
Ollamaはデフォルトでlocalhostのみバインド。外部マシンからアクセスするには `0.0.0.0` へのバインドが必要。

```bash
# SERVER側で実行

# launchctlへの環境変数設定（再起動後も有効）
launchctl setenv OLLAMA_HOST 0.0.0.0:11434
brew services restart ollama

# すぐに動作確認したい場合はフォアグラウンド起動
brew services stop ollama
OLLAMA_HOST=0.0.0.0:11434 ollama serve &

# CLIENTから確認
curl http://192.168.1.y:11434/api/tags
# → モデル一覧JSONが返れば成功
```

### Step 6: 環境変数の残留に注意
以前に `export OPENAI_API_KEY="unused"` などを実行していた場合、`config.yaml` の設定を上書きしてしまう。

```bash
# 確認コマンド
echo $OPENAI_API_KEY
grep -i "openai\|goose" ~/.zshrc ~/.zprofile

# 解決策：ターミナルを完全に閉じて新しいセッションで起動
# または unset で明示的に削除
unset OPENAI_API_KEY
unset OPENAI_BASE_URL
```

---

## 4. 最終設定

### 動作確認済み `config.yaml`
CLIENT（192.168.1.x）の `~/.config/goose/config.yaml`

```yaml
# Provider
GOOSE_PROVIDER: ollama
GOOSE_MODEL: qwen2.5:7b-instruct

# Ollama on NRT
OLLAMA_HOST: http://192.168.1.y:11434
OLLAMA_TIMEOUT: '600'

# Telemetry
GOOSE_TELEMETRY_ENABLED: false

# Extensions (省略)
extensions:
  ...
```

---

## 5. 恒久化設定

### SERVER再起動後も Ollama を外部公開し続ける

> [!WARNING]
> `~/.zshrc` への `export OLLAMA_HOST` 追記は **launchd サービスには効きません**。launchctlで設定するか、plistを編集する必要があります。

#### 方法1: launchctl（推奨）
```bash
# SERVER側で実行
launchctl setenv OLLAMA_HOST 0.0.0.0:11434
brew services restart ollama
```

#### 方法2: plist 編集
```bash
# homebrew.mxcl.ollama.plist を編集
nano ~/Library/LaunchAgents/homebrew.mxcl.ollama.plist

# EnvironmentVariables を追加
<key>EnvironmentVariables</key>
<dict>
  <key>OLLAMA_HOST</key>
  <string>0.0.0.0:11434</string>
</dict>
```

---

## 6. 教訓・まとめ

### Key Takeaways
- **根本原因**: Goose v1.26+ の Responses API 非互換
- **解決策**: OpenAI → Ollama プロバイダーへ切り替え
- **Ollama設定**: `OLLAMA_HOST=0.0.0.0:11434` で外部公開
- **診断ツール**: `curl -v` で接続確認してからGooseを設定

### モデル使い分けの指針

| 用途 | 推奨 | 理由 |
|---|---|---|
| 技術トラブルシュート | **Claude** | 論理的推論・正確な情報 |
| 大量文書処理・OCR整理 | **Gemini** | 100万トークンの文脈窓 |
| プライベートデータ処理 | **ローカルLLM (qwen2.5等)** | コスト0・オフライン |
| コスト重視の単純タスク | **ローカルLLM** | 無制限に叩ける |

> [!TIP]
> GooseやAIクライアントの設定で詰まったら、まず **curl で直接エンドポイントを叩いて接続確認**する。curlが通るかどうかで「ネットワーク・認証の問題」と「クライアント設定の問題」を切り分けられる。
