[< 上一章：四隻幽靈的 AI](06-ghost-ai.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：遊戲狀態機 >](08-state-machine.md)
---

## 第七章：幽靈繪製

幽靈的形狀是用像素逐格手繪的：

```python
def draw(self):
    px = MAZE_X + int(self.tx * TS)
    py = MAZE_Y + int(self.ty * TS)
    col = COL_SCARED if self.scared else COL_GHOST[self.idx]
    for dy in range(1, 7):
        for dx in range(1, 7):
            if dy <= 3:
                # 上半部：半圓形
                if (dx - 3.5) ** 2 + (dy - 3.5) ** 2 <= 3.5**2:
                    pyxel.pset(px + dx, py + dy, col)
            else:
                # 下半部：整排（波浪裙擺）
                pyxel.pset(px + dx, py + dy, col)
    if not self.scared:
        pyxel.pset(px + 2, py + 3, 7)   # 左眼
        pyxel.pset(px + 5, py + 3, 7)   # 右眼
```

繪製邏輯：

- 上半部（`dy <= 3`）：判斷像素是否在以 (3.5, 3.5) 為圓心、半徑 3.5 的圓內，形成半圓頭頂
- 下半部（`dy > 3`）：全部填滿，形成方形裙擺（原版幽靈的波浪裙擺在這個解析度下簡化為直邊）
- 受驚時：全部換成 `COL_SCARED`（藍色），並且不繪製眼睛

---
[< 上一章：四隻幽靈的 AI](06-ghost-ai.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：遊戲狀態機 >](08-state-machine.md)
