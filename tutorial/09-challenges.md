[< 上一章：遊戲狀態機](08-state-machine.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：發布與打包遊戲 >](10-distribution.md)
---

## 第九章：延伸挑戰

以下挑戰可以讓你更深入了解遊戲各個系統：

### 入門

- [ ] 調整小精靈速度（`Pacman.speed`）和幽靈速度（`Ghost.speed`），觀察遊戲難度變化
- [ ] 修改能量豆讓幽靈受驚的持續時間（`g.scared_timer = 150`），改成 300 或 60
- [ ] 加入「吃驚嚇幽靈連殺加成」：第一隻 200 分、第二隻 400 分、第三隻 800 分、第四隻 1600 分

  <details>
  <summary>提示：連鎖計分框架</summary>

  `student_scaffold.py` 裡已有 `self.ghost_combo` 計數器，吃到能量豆時歸零，每吃一隻幽靈加一。把碰撞判定裡的 `self.score += 200` 換成：

  ```python
  self.score += 200 * (2 ** (self.ghost_combo - 1))
  # ghost_combo=1 → 200×1=200，ghost_combo=2 → 200×2=400 …
  ```

  選做：在 `App.draw()` 裡顯示連殺提示：

  ```python
  if self.ghost_combo >= 2:
      msg = f"COMBO x{2 ** (self.ghost_combo - 1)}!"
      pyxel.text(WIDTH // 2 - 20, HEIGHT // 2 - 20, msg, COL_PAC)
  ```

  </details>

### 中階

- [ ] 增加**生命顯示圖示**：在畫面底部用小精靈 Sprite 代替數字顯示剩餘生命（參考 `pyxel.blt`）
- [ ] 實作**幽靈眼睛**：被吃掉後幽靈只剩眼睛，以高速回到出生點後復活
- [ ] 讓**幽靈穿越隧道**：修改幽靈的 `update` 使用 `allow_tunnel=True`，並讓座標取餘數如同小精靈

### 進階

- [ ] 加入**關卡系統**：每過一關速度加快、受驚時間縮短
- [ ] 實作**散步模式（Scatter Mode）**：幽靈每隔一段時間切換到各自負責的角落徘徊，再切回追逐模式（原版 Pac-Man 的完整 AI 行為）
- [ ] 加入**音效**：用 `pyxel.sounds` 加入吃豆聲、死亡音效、能量豆音效

---
[< 上一章：遊戲狀態機](08-state-machine.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：發布與打包遊戲 >](10-distribution.md)
