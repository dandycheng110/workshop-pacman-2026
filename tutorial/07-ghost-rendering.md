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

繪製程式碼：

```python
def draw(self):
    px = MAZE_X + int(self.tx * TS)
    py = MAZE_Y + int(self.ty * TS)
    if self.scared:
        pyxel.blt(px, py, 0, 0, 80, 16, 16, 0)
    else:
        sx = ((pyxel.frame_count // 4) % 2) * 16   # 每 4 幀切換一次動畫幀
        pyxel.blt(px, py, 0, sx, _GHOST_SPRITE_Y[self.idx], 16, 16, 0)
```

- 每 4 幀（`frame_count // 4`）切換一次動畫幀（0 或 1），乘以 16 得到 Sprite 的 x 座標（0 或 16）
- 受驚時固定使用受驚 Sprite，不受幽靈索引影響
- 顏色 0（黑色）作為透明色（`colkey=0`），不繪製 Sprite 背景

---
[< 上一章：四隻幽靈的 AI](06-ghost-ai.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：遊戲狀態機 >](08-state-machine.md)
