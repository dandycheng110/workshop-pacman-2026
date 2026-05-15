[< 上一章：移動與碰撞偵測](03-movement-and-collision.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：方向選擇演算法 >](05-direction-algorithm.md)
---

## 第四章：小精靈——吃豆子與動畫

### 吃豆子

吃豆子邏輯需要三步：

1. **四捨五入取最近格子**：`int(self.tx + 0.5)` 把浮點數格子座標轉成最近的整數
2. **查詢字典**：以座標元組 `(itx, ity)` 為 key，確認該格是否有豆子
3. **移除並回傳**：`dict.pop(key)` 同時移除豆子並回傳類型（`"dot"` 或 `"power"`）；若無豆子則回傳 `None`

回傳值在 `App.update` 中用來加分或觸發幽靈受驚狀態。

### Sprite 動畫

小精靈的外觀來自 `main.pyxres` 的 Sprite 圖，儲存在圖片銀行（image bank）0 的 y=0 列，共三格，每格 16×16 像素：

| x 座標 | 動畫幀 |
|--------|--------|
| 0      | 嘴巴全開 |
| 16     | 嘴巴半開 |
| 32     | 嘴巴閉合 |

所有 Sprite 都面向**左方**，向右移動時需水平翻轉。`_PAC_FRAMES` 定義了 12 幀的播放序列（開→半開→閉→半開→開循環）：

```python
_PAC_FRAMES = [0, 0, 0, 1, 1, 1, 2, 2, 2, 1, 1, 1]
```

`pyxel.blt(x, y, img, u, v, w, h, colkey)` 的參數：

- `x, y`：螢幕上的繪製起點（格子左上角）
- `img=0`：使用圖片銀行 0
- `u, v`：Sprite 在圖片銀行中的起始座標
- `w, h`：寬高；`w` 為負數時水平翻轉
- `colkey=0`：顏色 0（黑色）視為透明，不繪製

---

## 🖊️ 練習一：吃豆子

在 `Pacman.update()` 的步驟 4，把 `return None` 替換成吃豆子邏輯：

```python
    # 步驟 4：吃豆子
    itx = int(self.tx + ___)   # 四捨五入：加 0.5 再取整數
    ity = int(self.ty + ___)
    key = (___, ___)
    if key in dots:
        return dots.___(___)   # 同時移除並回傳 "dot" 或 "power"
    return None
```

完成後執行遊戲，確認 Pac-Man 走過豆子時豆子會消失。

---

## 🖊️ 練習二：動畫與方向翻轉

打開 `student_scaffold.py`，找到 `Pacman.draw()` 裡的靜態繪製，替換成完整的動畫版本：

```python
    def draw(self):
        # 步驟 1：每幀推進動畫計時器，用 % 12 讓它循環
        self.anim = (self.anim + ___) % ___
        # 步驟 2：用 _PAC_FRAMES 把計時器轉成 sprite 的 x 座標（每幀 16 像素）
        sx = _PAC_FRAMES[___] * ___
        px = MAZE_X + int(self.tx * TS)
        py = MAZE_Y + int(self.ty * TS)
        # 步驟 3：向右移動時 w 填負數（水平翻轉），否則填正數
        w = ___ if self.dx > 0 else ___
        pyxel.blt(px, py, 0, sx, 0, w, 16, 0)
```

完成後執行遊戲，確認小精靈移動時嘴巴會開合，且向右時 Sprite 會翻轉。

---
[< 上一章：移動與碰撞偵測](03-movement-and-collision.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：方向選擇演算法 >](05-direction-algorithm.md)
