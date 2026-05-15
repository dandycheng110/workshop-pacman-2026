[< 上一章：小精靈——輸入處理與動畫](04-pacman.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：四隻幽靈的 AI >](06-ghost-ai.md)
---

## 第五章：方向選擇演算法

### pick_direction 函式

這是四隻幽靈共用的移動核心，根據目標位置選擇最佳前進方向：

```python
_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]  # 右、左、下、上

def pick_direction(
    itx: int, ity: int,        # 幽靈目前所在格子（整數）
    dx: int, dy: int,          # 幽靈目前移動方向
    target_x: float, target_y: float,  # 目標位置
    flee: bool = False,        # True = 逃離目標
    allow_tunnel: bool = True, # False = 不允許選擇隧道方向
) -> tuple[int, int] | None:
    best: tuple[int, int] | None = None
    best_score: float | None = None
    for ddx, ddy in _DIRS:
        if ddx == -dx and ddy == -dy:
            continue            # 不允許 180° 迴轉
        ntx, nty = itx + ddx, ity + ddy
        if not allow_tunnel and not (0 <= ntx < COLS and 0 <= nty < ROWS):
            continue            # 幽靈不走隧道
        if is_wall(ntx, nty):
            continue            # 不走進牆壁
        dist2 = (ntx - target_x) ** 2 + (nty - target_y) ** 2
        score = -dist2 if flee else dist2
        if best_score is None or score < best_score:
            best_score = score
            best = (ddx, ddy)
    return best
```

關鍵設計決策：

1. **不允許 180° 迴轉**：`if ddx == -dx and ddy == -dy: continue`。這是原版 Pac-Man 的規則——幽靈除非進入「受驚」狀態的切換時刻，否則不能原地掉頭。
2. **不走隧道**（`allow_tunnel=False`）：幽靈呼叫時傳入 `allow_tunnel=False`，排除會讓座標超出地圖邊界的方向，讓幽靈不會主動選擇穿越隧道。
3. **追逐模式**（`flee=False`）：選擇讓下一格**距離目標最近**的方向（`score = dist2`，選最小的 score 即選最小的距離）。
4. **逃跑模式**（`flee=True`，受驚狀態）：選擇讓下一格**距離目標最遠**的方向（`score = -dist2`，最小的 `-dist2` 就是最大的 `dist2`）。

> **為什麼用距離平方（dist²）而不是距離？**
> 比較大小不需要開根號。`dist² = dx² + dy²` 計算量只有乘法和加法，比 `sqrt(dx² + dy²)` 快很多，而且不影響排序結果。在遊戲中，能省下的計算成本都值得省。

---
[< 上一章：小精靈——輸入處理與動畫](04-pacman.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：四隻幽靈的 AI >](06-ghost-ai.md)
