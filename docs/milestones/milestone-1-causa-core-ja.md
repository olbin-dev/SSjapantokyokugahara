# マイルストーン 1: Causa Core 設計と仕様

本マニュアルは、因果関係データベース「Causa（Anchor DB）」における、最初の安全な実装境界（マイルストーン1）を定義します。

## 1. SQLite スキーマ設計 (Schema Design)

因果の連鎖を正確にトラッキングするため、以下の7つのテーブル構造をSQLite上に定義します：

```sql
CREATE TABLE AnchorCase (
    id TEXT PRIMARY KEY,
    user_intent TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE UISnapshot (
    id TEXT PRIMARY KEY,
    anchor_case_id TEXT NOT NULL,
    ax_tree_json TEXT NOT NULL,
    image_hash TEXT NOT NULL,
    FOREIGN KEY(anchor_case_id) REFERENCES AnchorCase(id)
);

CREATE TABLE LLMProposal (
    id TEXT PRIMARY KEY,
    anchor_case_id TEXT NOT NULL,
    action_sequence TEXT NOT NULL,
    risk_level INTEGER NOT NULL,
    FOREIGN KEY(anchor_case_id) REFERENCES AnchorCase(id)
);

CREATE TABLE HumanApproval (
    id TEXT PRIMARY KEY,
    llm_proposal_id TEXT NOT NULL,
    approved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(llm_proposal_id) REFERENCES LLMProposal(id)
);

CREATE TABLE ExecutionEvent (
    id TEXT PRIMARY KEY,
    human_approval_id TEXT NOT NULL,
    executed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(human_approval_id) REFERENCES HumanApproval(id)
);

CREATE TABLE OutcomeEvidence (
    id TEXT PRIMARY KEY,
    execution_event_id TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    post_execution_state TEXT,
    FOREIGN KEY(execution_event_id) REFERENCES ExecutionEvent(id)
);

CREATE TABLE ReplayPolicy (
    id TEXT PRIMARY KEY,
    anchor_case_id TEXT NOT NULL,
    expires_at DATETIME NOT NULL,
    FOREIGN KEY(anchor_case_id) REFERENCES AnchorCase(id)
);
```

## 2. Python データモデル (Python Data Models)

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class AnchorCase:
    id: str
    user_intent: str
    created_at: datetime

@dataclass
class UISnapshot:
    id: str
    anchor_case_id: str
    ax_tree_json: str
    image_hash: str

@dataclass
class LLMProposal:
    id: str
    anchor_case_id: str
    action_sequence: str
    risk_level: int

@dataclass
class HumanApproval:
    id: str
    llm_proposal_id: str
    approved_at: datetime

@dataclass
class ExecutionEvent:
    id: str
    human_approval_id: str
    executed_at: datetime

@dataclass
class OutcomeEvidence:
    id: str
    execution_event_id: str
    success: bool
    post_execution_state: Optional[str]

@dataclass
class ReplayPolicy:
    id: str
    anchor_case_id: str
    expires_at: datetime
```

## 3. 決定論的リプレイ判定機能 (Deterministic Replay Decision Function)

```python
@dataclass
class ReplayDecision:
    status: str
    reason_code: str
    message: str
    anchor_case_id: Optional[str]

def determine_replay_decision(
    current_ui_snapshot: UISnapshot,
    historical_cases: list[dict],
    current_risk_level: int
) -> ReplayDecision:
    """
    ステータス、理由コード、メッセージ、および anchor_case_id を含む ReplayDecision オブジェクトを返します。
    """
    # ドキュメント作成用の擬似実装
    pass
```

## 4. 決定論的リプレイ判定ルール (Replay Eligibility Rules)

過去の判例データ（Precedent）が、再び自動実行可能（`replay_candidate`）と判定されるには、以下の条件を**すべて**満たす必要があります：

- 現在のUIスナップショットが、過去のUI指紋と完全に一致すること。
- ビジネスオブジェクトの同一性が検証されていること。
- アクションのペイロードハッシュが完全に一致すること。
- 過去に人間の承認（HumanApproval）が存在すること。
- 過去の実行結果（OutcomeEvidence）が存在し、それが「成功」を示していること。
- リプレイポリシー（ReplayPolicy）が有効であり、期限切れでないこと。
- 現在の操作のリスクレベルが「リスク3（手動再承認しきい値）」未満であること。
- 安全上の制約が満たされていること。

もし一つでも条件から外れる場合は、以下のように安全に判定が分岐します：

- リスクレベルが3以上 ➡️ `requires_human_anchor` (手動承認要求)
- 過去の実行が失敗 ➡️ `do_not_replay` (リプレイ禁止)
- UIの完全一致ではなく部分一致 ➡️ `requires_llm_reasoning` (LLMによる推論要求)
- ポリシーが期限切れ ➡️ `requires_human_anchor` (再承認要求)

## 5. 単体テストケース (Unit Test Cases)

- **完全なUI一致 + リスク1 + 成功した実行結果**: `replay_candidate` を返すべき。
- **完全なUI一致 + リスク3**: `requires_human_anchor` を返すべき。
- **過去の実行結果が失敗**: `do_not_replay` を返すべき。
- **部分的なUI一致**: `requires_llm_reasoning` を返すべき。
- **期限切れのリプレイポリシー**: `requires_human_anchor` を返すべき。

## 6. スキーマに関する補足 (Schema Notes)

初期スキーマは概念的なものです。実装バージョンでは以下を追加することを検討してください：
- ui_fingerprint_hash (UI指紋ハッシュ)
- business_object_id (ビジネスオブジェクトID)
- action_payload_hash (アクションペイロードハッシュ)
- app_bundle_id (アプリバンドルID)
- app_version (アプリバージョン)
- outcome_status (実行結果ステータス)
- replay_allowed (リプレイ許可フラグ)
- risk_threshold (リスクしきい値)
- required_match_score (必要な一致スコア)

## 7. ストレージの抽象化 (Storage Abstraction)

- Causa Coreはストレージに依存しません。
- `decision.py` はストレージの実装から完全に独立している必要があります。
- インメモリリポジトリは、テストおよびローカルシミュレーション専用です。
- SQLiteが最初のローカル永続化ターゲットです。
- PostgreSQL / Supabaseは、後ほどストレージアダプターを介して追加可能です。
- リプレイ判定は特定のデータベースバックエンドに依存してはなりません。

## 8. AnchorRecord の集約 (AnchorRecord Aggregation)

- `AnchorRecord` は1つの論理的な判例（Precedent Case）を表します。
- AnchorCase, UISnapshot, LLMProposal, HumanApproval, ExecutionEvent, OutcomeEvidence, ReplayPolicy をグループ化します。
- 証拠が欠落している場合でも表現可能とするため、一部のデータはオプション（Partial）となります。
- リプレイ判定には、依然として `decision.py` による明示的な検証が必要です。
- AnchorRecord はデータ集約の便宜を提供するものであり、自動的にリプレイ権限を与えるものではありません。

## 9. AnchorRecord 決定アダプター (AnchorRecord Decision Adapter)

- このアダプターにより、完全な AnchorRecord からリプレイ判定を行うことができます。
- リポジトリが一致するレコードを見つけられない場合があるため、`AnchorRecord` または `None` を受け入れます。
- これは `determine_replay_decision` の単なる便利なラッパーです。
- 永続化処理は行いません。
- リポジトリのクエリは実行しません。
- これ単体でリプレイ権限を付与することはありません。
- 依然として `ReplayDecision` が権限のある出力です。

## 10. 監査ログ生成 (Audit Summary)

- `ReplayDecision` は機械可読な正式な判定結果です。
- `AuditSummary` は人間可読な説明レイヤーです。
- AuditSummary はリプレイ権限を付与しません。
- AuditSummary は実行処理を行いません。
- AuditSummary はストレージのクエリを実行しません。
- 意思決定を監査・レビュー可能に保つために存在します。

## 11. 実行を伴わないエンドツーエンドシミュレーション (Non-executing End-to-End Simulation)

- Causa Coreは、一切の実行アクションを伴わずに決定パス全体をシミュレートできます。
- シミュレーションパス：
  `AnchorRecord` -> `Repository` -> `ReplayDecision` -> `AuditSummary`
- これらのテストは、コアとなる各レイヤーの統合を保証します。
- OS操作は実行しません。
- 自律的なリプレイは行いません。
- 外部ストレージは使用しません。

## 12. マイルストーン完了条件 (Milestone Completion)

以下が満たされたため、Causa Core v1.0-alphaとしてのマイルストーン1は「完了」とみなされます：
- AnchorRecord が定義されていること
- ReplayDecision が定義されていること
- AuditSummary が定義されていること
- InMemoryRepository が実装されていること
- 実行を伴わないエンドツーエンドのシミュレーションテストがパスしていること

## 13. 安全境界と制約 (Safety Constraints)

- 現時点ではOSの実行ロジックは存在しません。
- sudoなどの特権昇格ロジックはありません。
- 破壊的操作は行いません。
- Dify連携は未実装です。
- Accessibility APIの直接呼び出しは未実装です。
- 自律的なリプレイは未実装です。
- LLMの提案が自分自身の危険な操作を自動承認することは決してありません。
- HumanApproval（人間の承認）とOutcomeEvidence（実行結果）は厳密に分離して保存します。
- 過去の HumanApproval は「ユーザーが承認したこと」のみを証明し、「実行が成功したこと」は証明しません。
- 自動リプレイの適格性判定には、有効な HumanApproval レコードと成功した OutcomeEvidence レコードの両方しきい値が必要です。
