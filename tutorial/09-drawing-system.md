## 第九章：繪圖系統

### App.draw 主邏輯

```python
def draw(self):
    pyxel.cls(COL_BG)   # 清空畫面

    # UI：分數與生命
    pyxel.text(4, 4, f"SCORE:{self.score}", COL_TEXT)
    pyxel.text(110, 4, f"LIVES:{self.lives}", COL_TEXT)

    # 地圖牆壁
    for ty in range(ROWS):
        for tx in range(COLS):
            px = MAZE_X + tx * TS
            py = MAZE_Y + ty * TS
            if MAZE[ty][tx] == TILE_WALL:
                pyxel.rect(px, py, TS, TS, COL_WALL)

    # 豆子
    for (tx, ty), kind in self.dots.items():
        px = MAZE_X + tx * TS + 3
        py = MAZE_Y + ty * TS + 3
        if kind == "dot":
            pyxel.pset(px, py, COL_DOT)
        else:
            if (pyxel.frame_count // 8) % 2 == 0:
                pyxel.circ(px, py, 2, COL_PAC)

    # 幽靈和小精靈
    for g in self.ghosts:
        g.draw()

    if self.state != "dead" or self.state_timer > 30:
        self.pac.draw()

    # 覆蓋文字
    if self.state == "win":
        pyxel.text(55, 88, "YOU WIN!", COL_PAC)
    elif self.state == "gameover":
        pyxel.text(48, 88, "GAME OVER", 8)
```

幾個值得注意的細節：

**能量豆閃爍效果**

```python
if (pyxel.frame_count // 8) % 2 == 0:
    pyxel.circ(px, py, 2, COL_PAC)
```

`pyxel.frame_count` 是從遊戲開始的累積幀數。整除 8 後取餘數為 0 或 1，讓能量豆每 8 幀切換一次顯示狀態，達到閃爍效果。

**死亡動畫**

```python
if self.state != "dead" or self.state_timer > 30:
    self.pac.draw()
```

在死亡狀態的前 30 幀仍然顯示小精靈，後 30 幀隱藏，形成閃爍消失的效果。
