[< 上一章：四隻幽靈的 AI](06-ghost-ai.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：遊戲狀態機 >](08-state-machine.md)
---

## 第七章：幽靈繪製

幽靈的外觀來自 `main.pyxres` 的 Sprite 圖，儲存在圖片銀行 0，每隻幽靈有兩幀動畫（各 16×16 像素）：

| y 座標 | 幽靈 | 對應索引 |
|--------|------|---------|
| 16     | Blinky（紅） | ghost[0] |
| 32     | Inky（青）   | ghost[2] |
| 48     | Clyde（橘）  | ghost[3] |
| 64     | Pinky（粉）  | ghost[1] |
| 80     | 受驚（深藍） | 所有幽靈 |

兩幀分別存在 x=0 和 x=16，交替播放形成「飄動」動畫。受驚狀態只有一幀（x=0, y=80）。

這個對應關係定義在模組層級的常數：

```python
_GHOST_SPRITE_Y = [16, 64, 32, 48]   # 索引 0~3 對應 Blinky/Pinky/Inky/Clyde
```

繪製邏輯有兩個分支：

- **受驚狀態**：固定使用受驚 Sprite（x=0, y=80），不受幽靈索引影響
- **正常狀態**：每 4 幀（`pyxel.frame_count // 4`）切換一次動畫幀（x=0 或 x=16），透過 `_GHOST_SPRITE_Y[self.idx]` 取得對應幽靈的 y 座標

顏色 0（黑色）作為透明色（`colkey=0`），不繪製 Sprite 背景。

---

## 🖊️ 練習：實作 Ghost.draw()

打開 `student_scaffold.py`，找到 `Ghost.draw()` 裡的靜態繪製，替換成完整版本：

```python
    def draw(self):
        px = MAZE_X + int(self.tx * TS)
        py = MAZE_Y + int(self.ty * TS)
        if self.scared:
            # 受驚：固定使用 x=0, y=80 的 Sprite
            pyxel.blt(px, py, 0, ___, ___, 16, 16, 0)
        else:
            # 正常：每 4 幀切換一次，x 座標為 0 或 16
            sx = ((pyxel.frame_count // ___) % 2) * ___
            pyxel.blt(px, py, 0, sx, _GHOST_SPRITE_Y[___], 16, 16, 0)
```

完成後執行遊戲，確認幽靈身體會輕微飄動，吃下能量豆後變成深藍色。

---
[< 上一章：四隻幽靈的 AI](06-ghost-ai.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：遊戲狀態機 >](08-state-machine.md)
