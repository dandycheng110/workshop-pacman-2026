# Pac-Man 2026 進階版

在原版工作坊 `workshop-pacman` 的基礎上，迭代出一版完整可玩的 Pac-Man。

## 新增功能

| # | 功能 | 說明 |
|---|------|------|
| 1 | 關卡系統 + 難度遞增 | 第 1 ~ 8 關，每關小精靈速度 +0.005、幽靈速度 +0.006、能量豆時間 -22 幀，超過第 8 關維持最高難度 |
| 2 | Scatter / Chase 模式切換 | 經典街機排程（7s 散開 → 20s 追逐 → 7s → 20s → 5s → 20s → 5s → 永遠追），切換時所有幽靈強制反向 |
| 3 | 水果道具 | 每關吃到第 70、170 顆豆子時固定點位出現對應關卡水果（櫻桃→草莓→橘子→蘋果→西瓜→Galaxian→鈴→鑰匙），分數 100 ~ 5000 |
| 4 | 連吃幽靈連擊 | 同一次能量豆內依序吃幽靈得 200 → 400 → 800 → 1600 分，幽靈變眼睛回到出生點復活 |
| 5 | 完整狀態機 | menu / ready / play / pause / dead / win / levelup / gameover 八種狀態 |
| 6 | 開始選單 + 暫停 | 主畫面顯示操作說明與最高分；遊戲中 P 鍵暫停 |
| 7 | 音效 | 吃豆、能量豆、吃幽靈、死亡、吃水果、過關、READY 提示音 |
| 8 | 動畫 | 死亡星爆動畫、能量豆閃爍、幽靈受驚倒數閃白、連擊浮分文字、READY!/LEVEL/GAME OVER 提示 |

## 玩法

```
方向鍵 / WASD → 移動
P              → 暫停 / 繼續
SPACE / ENTER → 開始遊戲、結束後回主選單
Q             → 離開
```

## 執行

```bash
uv sync                  # 安裝依賴
uv run python main.py    # 開始遊戲
```

或直接：
```bash
.venv/bin/python main.py
```

## 檔案結構

```
workshop-pacman-2026/
├── main.py            # 全部遊戲邏輯
├── main.pyxres        # Pyxel sprite bank（沿用原版）
├── pyproject.toml     # 依賴定義
├── tutorial/          # 原版教學章節（基礎概念參考）
├── README.md
└── TUTORIAL.md
```

## 設計重點

- **格子座標系**：`tile_x + dx * progress` 浮點格座標，轉彎只在抵達格子時發生，避免穿牆
- **幽靈 AI 解耦**：每隻幽靈有獨立的 `ai_fn`（chase 模式時呼叫），scatter 模式時改用各自的角落座標
- **強制反向**：經典機制 — Scatter ↔ Chase 切換時所有非受驚/非眼睛狀態的幽靈立刻 180°，避免玩家被同一路線追到死
- **狀態機**：`update()` 根據 `self.state` 分派子函式，UI 在 `draw()` 對應狀態繪製覆蓋層

從基礎版（[../workshop-pacman/main.py](../workshop-pacman/main.py)）升級到本版的主要差異：

1. 多了 `Fruit` 類別與 `level_cfg()` 難度表
2. `Ghost` 新增 `mode`、`eaten`（眼睛回家）、`force_reverse()`
3. `App` 拆出 `_update_*()` 八個狀態子函式 + `_draw_hud_*()` HUD 分區
4. `pyxel.sounds[0..6]` 註冊七種音效於 `_init_sounds()`
