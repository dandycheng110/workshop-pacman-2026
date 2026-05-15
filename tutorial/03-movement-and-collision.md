[< 上一章：顏色、格子與地圖](02-grid-and-maze.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：小精靈——輸入處理與動畫 >](04-pacman.md)
---

## 第三章：移動與碰撞偵測

本章是整個遊戲物理系統的核心，理解這部分才能讀懂小精靈和幽靈的移動邏輯。

### 格子進度模型（Tile-Progress Model）

小精靈和幽靈的位置用**格子進度模型**表示：

| 欄位 | 型別 | 說明 |
|------|------|------|
| `tile_x`, `tile_y` | `int` | 目前所在格子（已到達的整數格子） |
| `dx`, `dy` | `int` | 目前移動方向（-1、0 或 1） |
| `progress` | `float` | 朝下一格已走的比例（0.0 = 剛出發，1.0 = 抵達） |

這兩個值合成**浮點數格子座標**屬性，供繪圖使用：

```python
@property
def tx(self):
    return float(self.tile_x + self.dx * self.progress)
```

以小精靈為例，速度是 `0.08`（每幀進度增加 0.08）。以 30 fps 計算，每秒大約移動 2.4 格。

### 抵達格子時的邏輯

每幀角色的 `progress` 增加 `speed`。當 `progress >= 1.0` 時，代表角色抵達了下一格：

```python
self.progress += self.speed
if self.progress >= 1.0:
    self.tile_x = (self.tile_x + self.dx) % COLS   # 更新整數格子（含隧道穿越）
    self.tile_y = (self.tile_y + self.dy) % ROWS
    self.progress -= 1.0                             # 保留多餘進度，確保平滑
    # ── 此時嘗試轉彎或判斷下一格是否為牆壁 ──
```

方向的切換只發生在「剛到達格子」這個精確時間點，不需要用模糊的容錯區間（`near_grid`）。

### 穿越隧道

本地圖在第 6 列和第 9 列設有隧道開口——這兩列的首尾格子是 `TILE_DOT`（`"2"`）而非 `TILE_WALL`（`"1"`）：

```
row 6: "2222212112122222"   ← 兩端為 '2'，形成左右隧道口
row 9: "2222212112122222"
```

抵達下一格時用取餘數（`%`）實現穿越（小精靈適用）：

```python
self.tile_x = (self.tile_x + self.dx) % COLS
```

當格子座標超出地圖左右邊界，取餘數後會出現在對側，完成穿越。

幽靈的方向選擇傳入 `allow_tunnel=False`，讓幽靈不會主動選擇進入隧道：

```python
best = pick_direction(..., allow_tunnel=False)
```

`tile_at` 在超出水平邊界時會先確認該列是否有隧道開口，再決定要回傳 `TILE_WALL` 還是對側的格子，讓 `pick_direction` 能正確判斷哪些出口可通行。

---
[< 上一章：顏色、格子與地圖](02-grid-and-maze.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：小精靈——輸入處理與動畫 >](04-pacman.md)
