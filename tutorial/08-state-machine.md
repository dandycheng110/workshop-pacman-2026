[< 上一章：幽靈繪製](07-ghost-rendering.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：延伸挑戰 >](09-challenges.md)
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

每幀在 `"play"` 狀態下依序執行：

1. 呼叫 `self.pac.update(self.dots)` 取得本幀吃到的豆子類型（`"dot"`、`"power"` 或 `None`）
2. **計分與觸發受驚**：
   - 吃到普通豆子 → 加分
   - 吃到能量豆 → 加分，並讓所有幽靈進入受驚狀態（設定 `scared=True` 與計時器）
3. 更新所有幽靈位置
4. 碰撞偵測：小精靈與受驚幽靈相撞 → 吃掉幽靈並加分；與正常幽靈相撞 → 死亡
5. 豆子清空 → 切換到 `"win"` 狀態

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

## 🖊️ 練習一：計分與觸發受驚

在 `App.update()` 第一個 `pass`（計分區）填入以下框架：

```python
            if eaten == "dot":
                self.score += ___
            elif eaten == "power":
                self.score += ___
                self.ghost_combo = 0   # 重置連鎖計數器（第九章挑戰會用到）
                for g in self.ghosts:
                    g.scared = ___
                    g.scared_timer = ___   # 150 幀 ≈ 5 秒
```

完成後執行遊戲，確認吃豆子時分數正確跳動，吃到能量豆後幽靈變藍。

---

## 🖊️ 練習二：碰撞偵測與狀態轉移

對照本章的狀態轉移圖，填入其餘三個 `pass`：

```python
                    else:
                        # 碰到正常幽靈：扣血並進入 dead 狀態
                        self.lives -= ___
                        self.state = ___        # "dead"
                        self.state_timer = ___  # 60 幀緩衝
                        break

            # 豆子清空：進入 win 狀態
            if not self.dots:
                self.state = ___               # "win"
                self.state_timer = ___         # 90 幀緩衝

        elif self.state == "dead":
            self.state_timer -= ___
            if self.state_timer <= ___:
                if self.lives <= 0:
                    self.state = ___           # "gameover"
                    self.state_timer = ___     # 120 幀後重置
                else:
                    self.reset_positions()
                    self.state = ___           # 回到 "play"

        elif self.state in (___, ___):         # "win" 和 "gameover"
            self.state_timer -= ___
            if self.state_timer <= ___:
                self.reset_game()
```

完成後執行遊戲，確認碰到幽靈會死亡、全豆吃完會顯示 YOU WIN、生命歸零會顯示 GAME OVER。

---

### [M] 修改

做完填寫後，嘗試以下兩個小改動，觀察遊戲行為有何不同：

1. 把 `g.scared_timer = 150` 改成 `90`——受驚時間縮短為幾秒？
2. 把碰撞判定裡的 `self.score += 200` 改成 `300`——吃鬼分數有正確變化嗎？

---
[< 上一章：幽靈繪製](07-ghost-rendering.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：延伸挑戰 >](09-challenges.md)
