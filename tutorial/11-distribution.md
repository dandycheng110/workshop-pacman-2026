[< 上一章：延伸挑戰](10-challenges.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：附錄：常用 Pyxel API 速查 >](99-appendix.md)
---

## 第十一章：發布與打包遊戲

當你完成遊戲後，一定想分享給朋友玩。Pyxel 提供了非常方便的工具，可以讓你把程式碼打包成單一檔案，甚至轉換成可以在瀏覽器上執行的網頁版。

### 1. 打包成 Pyxel 專用格式 (`.pyxapp`)

這是 Pyxel 最基礎的打包方式。它會把你的 Python 檔案和資源壓縮成一個檔案。

**執行命令：**
```bash
# pyxel package [專案目錄] [啟動檔案]
pyxel package . main.py
```
執行後，你會得到一個 `main.pyxapp`。

*   **如何執行：** 只要電腦有安裝 Pyxel，就可以用 `pyxel play main.pyxapp` 來玩。
*   **優點：** 跨平台（Windows/Mac/Linux 通用）、檔案極小。
*   **缺點：** 對方電腦必須安裝 Python 和 Pyxel。

---

### 2. 轉換成網頁版 (HTML/WASM) —— 最推薦！

這是最方便分享的方式。你可以把遊戲變成一個 HTML 檔案，傳給朋友後，他們直接用瀏覽器就能玩，甚至在手機上也能跑。

**執行命令：**
```bash
pyxel app2html main.pyxapp
```
這會產生一個 `main.html`。

*   **如何執行：** 直接用 Chrome 或 Safari 瀏覽器打開即可。
*   **分享平台：** 你可以把這個 HTML 上傳到 [itch.io](https://itch.io/)，讓全世界的人都能在線上玩你的作品。

---

### 3. 打包成獨立執行檔 (`.exe` 或 `.app`)

如果你希望對方「點兩下」就能玩，不需要安裝任何東西，可以使用這個方法。

**執行命令：**
```bash
pyxel app2exe main.pyxapp
```

*   **注意事項：**
    1.  你必須在 Windows 上執行這個指令才能產生 `.exe`。
    2.  在 Mac 上執行則會產生 `.app`。
*   **優點：** 對方不需要安裝 Python。
*   **缺點：** 檔案體積較大（因為裡面包含了 Python 引擎）。

---

### 總結：我該選哪種？

1.  **想放上個人網站或 Itch.io：** 選 **HTML 版**。
2.  **想給一般大眾（非開發者）下載：** 選 **獨立執行檔**。
3.  **想傳給同樣會寫程式的朋友：** 選 **.pyxapp**。

恭喜你！你已經完成了從開發到發布的所有步驟。快去分享你的 Pac-Man 吧！

---
[< 上一章：延伸挑戰](10-challenges.md) | [🏠 回目錄](../TUTORIAL.md) | [下一章：附錄：常用 Pyxel API 速查 >](99-appendix.md)
