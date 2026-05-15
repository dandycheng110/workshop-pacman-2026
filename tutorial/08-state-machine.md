[< 上一章：幽靈繪製](07-ghost-rendering.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：繪圖系統 >](09-drawing-system.md)
---

## 第八章：遊戲狀態機

### 狀態定義

遊戲有四個狀態：

| 狀態 | 說明 |
|------|------|
| `"play"` | 正常遊玩中 |
| `"dead"` | 玩家剛死亡，等待重置 |
| `"win"` | 所有豆子吃完，顯示勝利畫面 |
| `"gameover"` | 生命歸零，顯示遊戲結束畫面 |

狀態轉移圖：

```
     reset_game()
         │
         ▼
      "play"  ──── 吃完所有豆子 ────► "win"
         │                               │ 90 幀後
    碰到幽靈                         reset_game()
         │
         ▼
      "dead"
         │
    60 幀後
    ┌────┴────┐
    │         │
lives > 0  lives = 0
    │         │
reset_pos()   ▼
    │       "gameover"
    ▼          │ 120 幀後
  "play"    reset_game()
```

### App.update 主邏輯

```python
def update(self):
    if pyxel.btnp(pyxel.KEY_Q):
        pyxel.quit()

    if self.state == "play":
        eaten = self.pac.update(self.dots)
        if eaten == "dot":
            self.score += 10
        elif eaten == "power":
            self.score += 50
            for g in self.ghosts:
                g.scared = True
                g.scared_timer = 150   # 150 幀 = 5 秒

        for g in self.ghosts:
            g.update(self.pac.tx, self.pac.ty)

        # 碰撞偵測：小精靈 vs 幽靈
        for g in self.ghosts:
            if abs(self.pac.tx - g.tx) < 0.8 and abs(self.pac.ty - g.ty) < 0.8:
                if g.scared:
                    g.reset()
                    self.score += 200
                else:
                    self.lives -= 1
                    self.state = "dead"
                    self.state_timer = 60
                    break

        if not self.dots:
            self.state = "win"
            self.state_timer = 90

    elif self.state == "dead":
        self.state_timer -= 1
        if self.state_timer <= 0:
            if self.lives <= 0:
                self.state = "gameover"
                self.state_timer = 120
            else:
                self.reset_positions()
                self.state = "play"

    elif self.state in ("win", "gameover"):
        self.state_timer -= 1
        if self.state_timer <= 0:
            self.reset_game()
```

### 碰撞偵測

```python
if abs(self.pac.tx - g.tx) < 0.8 and abs(self.pac.ty - g.ty) < 0.8:
```

這用的是「軸對齊邊界框（AABB）」碰撞偵測，只需比較兩個方向的座標差是否都小於門檻值。門檻 0.8 格讓碰撞判定有一定容錯，即使小精靈和幽靈沒有完全重疊也會觸發。

**碰撞結果：**
- 幽靈**受驚中**：幽靈被吃掉（`g.reset()` 回到出生點），玩家加 200 分
- 幽靈**正常狀態**：玩家死亡（`lives -= 1`，進入 `"dead"` 狀態）

### build_dots 與豆子字典

```python
def build_dots(self):
    self.dots = {}
    for ty in range(ROWS):
        for tx in range(COLS):
            c = MAZE[ty][tx]
            if c == TILE_DOT:
                self.dots[(tx, ty)] = "dot"
            elif c == TILE_POWER:
                self.dots[(tx, ty)] = "power"
```

> **💡 Python 技巧：用元組 (Tuple) 當作字典的 Key**
> 我們用 `(tx, ty)` 這個座標元組當作字典的 Key。這是一個非常聰明的做法，因為字典的查詢速度（O(1)）極快。不管地圖上有 10 顆還是 1000 顆豆子，判斷「小精靈現在這格有沒有豆子」的速度都是一樣的。

豆子用字典存放，以格子座標 `(tx, ty)` 為 key。字典查詢的時間複雜度是 O(1)，每幀的豆子碰撞檢查只需要一次字典查詢，不需要遍歷所有豆子。吃掉豆子用 `dict.pop(key)` 同時查詢並移除。當 `self.dots` 為空時代表全部吃完，觸發勝利。

---
[< 上一章：幽靈繪製](07-ghost-rendering.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：繪圖系統 >](09-drawing-system.md)
