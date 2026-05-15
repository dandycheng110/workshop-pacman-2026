# 第一章：事前準備與專案架構

## 事前準備

安裝 [uv](https://docs.astral.sh/uv/getting-started/installation/) 後，在專案目錄執行：

```bash
uv run python main.py
```

即可啟動遊戲。方向鍵或 WASD 控制小精靈移動，Q 鍵離開。

---

## Pyxel 是什麼？

[Pyxel](https://github.com/kitao/pyxel) 是一個專為復古像素風格遊戲設計的 Python 遊戲引擎。它的設計哲學刻意限制資源：

| 限制 | 數值 |
|------|------|
| 調色盤 | 16 色 |
| 音效聲道 | 4 |
| 背景音樂軌道 | 8 |

這些限制和 1980 年代的遊戲硬體相近，讓製作者能專注在遊戲設計本身，而不是無窮無盡的視覺調整。

## 專案結構

遊戲由兩個檔案組成：

- `main.py`：所有遊戲邏輯
- `main.pyxres`：Pyxel 資源檔，儲存小精靈和幽靈的像素圖（Sprite）

`main.py` 由上到下大致分為：

```
常數定義（顏色、格子、地圖）
  ↓
工具函式（位置計算、碰撞偵測、方向選擇）
  ↓
AI 函式（四隻幽靈的目標計算策略）
  ↓
Pacman 類別（玩家）
  ↓
Ghost 類別（幽靈）
  ↓
App 類別（遊戲主迴圈）
```

## Pyxel 的遊戲迴圈

Pyxel 採用固定頻率的遊戲迴圈。呼叫 `pyxel.run(update, draw)` 後，每一幀會依序執行：

1. **update**：處理輸入、更新遊戲邏輯
2. **draw**：根據目前狀態渲染畫面

```python
pyxel.init(WIDTH, HEIGHT, title="Pac-Man", fps=30)
pyxel.load("main.pyxres")   # 載入圖片資源（Sprite 圖）
pyxel.run(self.update, self.draw)
```

`fps=30` 代表每秒執行 30 次 update 和 draw，這也是本專案中所有「計時器」和「速度」的時間基準。

## Pyxel 編輯器

Pyxel 內建一個像素圖編輯器，讓你直接在 Python 環境中繪製 Sprite 和音效素材。啟動方式：

```bash
uv run pyxel edit main.pyxres
```

編輯器主要包含三個工具：

| 工具 | 說明 |
|------|------|
| Image Bank | 繪製 Sprite（小精靈、幽靈的 16×16 像素圖） |
| Tilemap | 用 Sprite 組合成地圖背景 |
| Sound / Music | 設計音效與背景音樂 |

除了本地端的編輯器，Pyxel 也提供了 **[Web 版編輯器 (Code Maker)](https://kitao.github.io/pyxel/web/code-maker/)**，讓你不需要安裝 Python 就能直接在瀏覽器裡寫程式與繪圖。

詳細操作說明見官方手冊：[Pyxel Editor Manual](https://kitao.github.io/pyxel/web/editor-manual/)

> **工作坊說明**：課程進行到這裡時，請依照講師說明在 Pyxel 編輯器中繪製 Sprite 並儲存為 `main.pyxres`。完成後進行下方的練習。

---

## 🖊️ 練習：載入 Sprite 資源

在 Pyxel 編輯器中繪製好 Sprite 並儲存後，打開 `student_scaffold.py`，找到 `App.__init__` 裡的提示，加入一行：

```python
pyxel.load("main.pyxres")
```

執行遊戲，確認小精靈以 Sprite 形式出現並在畫面中移動。

---
[🏠 回目錄](../TUTORIAL.md) | [下一章：顏色、格子與地圖 >](02-grid-and-maze.md)
