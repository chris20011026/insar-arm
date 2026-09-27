# 第二階段：原生 Conda 套件（開發中）

目標：使用者直接下載套件，不必在自己的電腦編譯 ISCE2；執行時不依賴 Homebrew。
此分支尚不是可公開宣稱完成的安裝環境。第一階段 `install.sh` 保持原樣。

## 套件拆分

- `insar-arm-motif`：沿用第一階段固定來源及 Homebrew / MacPorts 修補，提供 ARM Motif 函式庫與標頭。
- `isce2`：沿用官方固定版本，改用 Conda C / C++ / Fortran 編譯器和執行期，安裝三種 Stack。
- 後續整合包：環境啟用、命令切換、驗證工具、MintPy 與固定相依。
- `insar-arm-snaphu-cli`：獨立命令列程式配方，保留上游 CS2 功能、完整 README 與非商業限制；與 Python binding 分開。

## 開發者建置

先在**獨立環境**安裝 conda-build、conda-index（可使用 `build-tools-osx-arm64.lock` 重建本次工具版本），再指定其中的 conda-build：

```sh
CONDA_BUILD_EXE=/path/to/build-env/bin/conda-build bash packaging/build-local.sh
```

需要 Apple Command Line Tools / SDK。建置工具使用 Conda 編譯器；不是沿用第一階段 Homebrew GCC 的產物。
預設產物、下載與紀錄都在忽略追蹤的 `.work/`；不會安裝到研究環境。

## 發布門檻

1. 從公開且校驗過的來源建立 ARM 套件。
2. 在不同路徑的全新環境安裝，檢查相依與所有原生函式庫。
3. 不得連到 Homebrew、編譯目錄或其他環境；保留系統函式庫依賴。
4. 完成第一階段數值與繪圖驗證；不能只有 import 成功。
5. 列出來源、修補、授權、測試主機與已知限制；對含 LGPL 程式的二進位保留對應來源取得方式。
6. 準備 channel 索引、版本鎖定、下載校驗與另一台 Mac 的回報流程。

尚未建立公開 Conda channel；配方存在不代表套件已建置或通過移機測試。

## 來源與方法

- ISCE2：`locks/sources.json` 的官方來源與 SHA256，CMake 建置。
- Motif 三個修補從第一階段固定來源複製，來源與 SHA256 見同一鎖定檔，保留原始內容。
- 參考 [conda-forge ISCE2 配方](https://github.com/conda-forge/isce2-feedstock)。此配方採用 CMake，並非宣稱是官方 conda-forge ARM 發行。
- 依 [Conda relocation 文件](https://docs.conda.io/projects/conda-build/en/stable/resources/make-relocatable.html) 由 conda-build 處理安裝前綴與動態連結，再於新環境驗證。


## 目前實測紀錄（2026-09-28）

- 獨立的 Conda 打包工具環境已建立，精確版本記於 `build-tools-osx-arm64.lock`。
- ISCE2、Motif 與 SNAPHU CLI 已產生 osx-arm64 `.conda` 成品，檔名與 SHA256 見 `prototype-artifacts.json`；成品仍只在本機，不代表公開下載連結。
- ISCE2 使用 Conda 的 Clang / GFortran 建置，53 / 53 項上游 CTest 通過。
- 打包後的 ISCE2 隔離安裝測試通過：六個入口啟動、多視運算與 mdx 實際產生 PPM。
- 三個成品重新安裝到另一個全新、較短路徑的環境後，六個入口、合成核心運算與 ALOS 四種電離層設定的指令產生共 8 / 8 項檢查通過。
- SNAPHU 合成解纏最大誤差為 1.9073486328125e-6 弧度；多視運算最大誤差約 3.89e-8。這些不是實際衛星位移精度。
- 新環境成功載入 Motif 的 libXm、libMrm、libUil。
- 最終新環境共 1,170 個原生檔案通過 ARM 與絕對載入路徑稽核，未發現 Homebrew 或其他環境依賴。相依套件清單記於 `prototype-runtime.json`，不是可直接安裝的 lock file。
- 稽核可重跑：`python3 packaging/audit-prefix.py /path/to/new/conda/environment`。它不取代真正載入與數值測試，也不宣稱解析所有相對路徑。
- 這些結果來自同一台 Apple Silicon Mac 的不同環境，尚未在第二台實體 Mac 驗證。
- 完整環境整合與公開發行尚未完成；第一階段的研究環境與 main 分支沒有替換。

## 核心套件的新環境檢查

在全新的 Conda 環境安裝本機 channel 的三個核心套件後，可執行：

```sh
python3 packaging/check-core.py /path/to/new/environment --output /path/to/report
python3 packaging/audit-prefix.py /path/to/new/environment
```

前者沿用第一階段的六個入口、合成核心運算與 ALOS 指令產生檢查；後者拒絕 Intel-only 檔案及環境外的非系統絕對載入路徑。這是核心套件子集，尚未涵蓋 MintPy、完整啟用工具包、全部繪圖流程或真實 SAR 資料端到端驗證。

公開二進位前還需整理完整第三方 notices 與對應來源包（尤其 Motif / ISCE2 內含元件 / SNAPHU CS2）；目前本機試驗產物不作公開發行。
