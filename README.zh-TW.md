# Codex Surgical Engineering

這是一個適用於 Codex CLI、IDE extension 與 ChatGPT desktop Codex 的 Agent Skill，目標是讓程式代理：

- 不盲目修改未讀取的檔案；
- 依風險調整流程嚴謹度，而不是每個小修改都反覆詢問；
- 只做最小且一致的修改；
- 對外部輸入保留必要錯誤處理，但不濫用 catch-all；
- 使用專案既有工具驗證；
- 完成前逐段審查 Git diff；
- 清楚區分「已通過、失敗、未執行」的檢查。

## 目錄

```text
codex-surgical-engineering/
├─ SKILL.md
├─ agents/openai.yaml
├─ assets/AGENTS.template.md
└─ scripts/verify_change_scope.py
```

## 安裝到單一 Repository

把整個資料夾放到：

```text
<repository>/.agents/skills/codex-surgical-engineering/
```

Repository 可以提交這個資料夾，讓團隊成員共同使用。

## 安裝到個人 Codex

把整個資料夾放到：

```text
~/.agents/skills/codex-surgical-engineering/
```

Codex 通常會自動偵測技能變更；沒有出現時重新啟動 Codex。

## 使用

在 Codex CLI 或 IDE 中明確指定：

```text
$codex-surgical-engineering 修正登入失敗問題，保留現有 API，並執行相關測試。
```

也可以使用 `/skills` 或輸入 `$` 後選擇技能。因為 `agents/openai.yaml` 允許隱式叫用，符合描述的程式修改任務也可能自動啟用。

## 建議搭配 AGENTS.md

將 `assets/AGENTS.template.md` 複製到 Repository 根目錄並改名為 `AGENTS.md`，填入專案實際命令：

```bash
cp .agents/skills/codex-surgical-engineering/assets/AGENTS.template.md AGENTS.md
```

Skill 提供通用工作流程；`AGENTS.md` 負責專案特定的測試、架構、依賴與禁止修改範圍。

## 確定性範圍檢查

腳本不會修改檔案。它會檢查 staged、unstaged、刪除、重新命名、複製與未追蹤檔案的路徑，並對 tracked diff 執行 `git diff --check`：

```bash
python .agents/skills/codex-surgical-engineering/scripts/verify_change_scope.py \
  --allow 'src/**' \
  --allow 'tests/**' \
  --deny 'migrations/**'
```

指定比較基準：

```bash
python .agents/skills/codex-surgical-engineering/scripts/verify_change_scope.py \
  --base origin/main \
  --allow 'game/**'
```

沒有提供 `--allow` 時，不限制允許路徑；`--deny` 仍會生效。

## 設計取向

這個版本刻意改善單純「謹慎、簡單、少修改」規則的不足：

1. 用 Tier 0–2 避免簡單任務也陷入繁瑣問答。
2. 將必要的相鄰修改定義為「一致性修改」，避免把 surgical change 誤解成只能改一個檔案。
3. 將錯誤處理限制在真實邊界，不把內部確定性邏輯全面包進 `try/except`。
4. 驗證不限於單元測試，也包含型別、編譯、解析、migration、UI／遊戲場景與人工 smoke test。
5. 強制 diff 自審與真實結果報告，避免只靠提示詞宣稱成功。
6. 以獨立腳本處理可確定執行的範圍檢查，保持 Skill 本身清楚且可攜。
