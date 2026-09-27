# InSAR ARM

**0.2.0 beta 1：預先編譯的 Apple Silicon Conda 環境。**

[免編譯安裝說明](docs/BINARY_INSTALL.md) · [English binary guide](docs/BINARY_INSTALL.en.md) · [Release](https://github.com/chris20011026/insar-arm/releases/tag/v0.2.0-beta.1)

新版本不需要使用者自行編譯 ISCE2；仍屬公開測試版，尚待另一台實體 Mac 與完整真實資料流程驗證。

---

以下保留第一階段的原始碼安裝方式。

在 Apple Silicon Mac 上建立可重建、可檢查的 InSAR Conda 環境。

第一階段提供**環境配方、自動安裝工具及驗證工具**。整合 ISCE2、三種 Stack 處理器、MintPy、SNAPHU、GDAL 與 mdx 繪圖工具。沿用官方程式與社群編譯方法，不修改科學演算法。

**狀態：0.1.0 公開測試候選版。** 支援 Apple Silicon macOS 的 CPU 處理；不是跨所有作業系統、衛星與資料格式的通用保證。已測試與尚未測試的範圍見 [驗證紀錄](docs/VALIDATION.md)。[English guide](docs/README.en.md)

## 安裝前需要什麼

- Apple Silicon Mac，原生終端機，macOS **14.5 或更新**。此下限來自鎖定套件的需求，不代表所有這些 macOS 版本都已實測。
- 已安裝 Conda；新電腦建議使用 [Miniforge 的 MacOSX arm64 版本](https://github.com/conda-forge/miniforge)。不需要刪除既有 Conda。
- Apple Command Line Tools。若尚未安裝，執行 `xcode-select --install`，完成系統安裝視窗。
- 已安裝 Homebrew 的 GCC 14：`brew install gcc@14`。安裝工具會檢查編譯器，不會自行更新 Homebrew 或修改系統設定。
- 網路連線，以及建議至少 10 GB 可用空間，供環境、套件快取與編譯使用。

環境與建置路徑請使用**不含空白**的路徑，以符合上游編譯工具限制。初版支援 bash / zsh。

## 三個操作

下載並解壓縮這個專案，在終端機進入專案資料夾。

**1. 檢查電腦是否準備好**

```sh
bash insar-arm doctor
```

只想查看安裝內容，可以執行 `bash insar-arm plan`。

**2. 建立全新環境並自動驗證**

```sh
bash install.sh
```

預設建立 Conda 環境目錄下的 `insar_arm`。若已存在，工具會停止，**不會覆蓋或升級原環境**。可另選名稱／路徑：

```sh
bash install.sh --prefix "$HOME/miniforge3/envs/insar_arm_new"
```

找不到 Conda 或 GCC 時可明確指定：

```sh
bash install.sh --conda /path/to/bin/conda --gcc-prefix /path/to/gcc14 --prefix /path/to/new/environment
```

工具會依序下載並核對來源、建立 Conda 環境、編譯 Motif / ISCE2 / SNAPHU、安裝 MintPy、設定環境，最後執行測試。每一步都顯示紀錄檔位置。只有驗證全部通過才會顯示成功。

**3. 啟用並選擇處理工具**

使用安裝完成時顯示的完整環境路徑：

```sh
conda activate /path/to/new/environment
use_alosStack
```

| 你要做的事 | 選擇方式 / 入口 |
|---|---|
| ALOS-2 多日期 | `use_alosStack` → `create_cmds.py` |
| Sentinel-1 TOPS 多日期 | `use_topsStack` → `stackSentinel.py` |
| Stripmap 多日期 | `use_stripmapStack` → `stackStripMap.py` |
| MintPy 時序分析 | `use_mintpy` → `smallbaselineApp.py` |
| 兩日期處理 | `topsApp.py`、`alos2App.py`、`stripmapApp.py` |
| 再次檢查環境 | `insar-check` |

這些選擇命令只設定目前的 shell，不會啟動研究資料處理。新開終端機後需重新啟用與選擇。不同 Stack 的同名指令會優先選用所選 Stack；`use_mintpy` 會切回 MintPy 的同名指令。未選 Stack 時預設優先使用環境 `bin` 中的程式。

## 驗證報告

`insar-check` 會產生 HTML、JSON 及各項檢查紀錄；可以雙擊 HTML 查看。預設寫到 `~/Library/Logs/insar-arm/`，也可指定：

```sh
insar-check --output "$HOME/insar-check-report"
```

不需要先啟用環境時，也能從專案呼叫：

```sh
bash insar-arm verify --prefix /path/to/environment --output /path/to/report
```

驗證涵蓋：

- 所選 Python、工具與套件是否來自正確環境。
- 六種 ISCE2 入口啟動、Stack 套件匯入與 bash / zsh 切換。
- ALOS Stack 四種電離層設定的指令產生；使用合成檔案名稱，不處理真實 SAR 影像。
- 原生多視運算、電離層濾波及 SNAPHU 解纏的小型數值測試。
- mdx、字型、TIFF / PNG 真正產圖。
- MintPy 從合成干涉圖反演位移時間序列與速度，與已知答案比較。
- Python 相依要求、Conda 平台、Mach-O 架構及外部絕對路徑函式庫。

**入口能啟動不等於完整研究流程已驗證。** 真實資料的相干性、配對、DEM、軌道、解纏、電離層判讀，以及大氣校正仍需專業檢查。報告會保留這個範圍說明。

## 失敗後怎麼處理

查看最後顯示的紀錄檔。解決缺少的系統工具或網路問題後，可使用原本的參數加上 `--resume`：

```sh
bash install.sh --prefix /path/to/new/environment --resume
```

續跑只適用於這個工具建立、而且安裝配方及編譯器未變更的環境；會略過已完成階段，最後重新驗證。若安裝程式或鎖定版本已變更，請建立另一個新環境。Conda 建立階段若未完整完成，工具不會自動刪除或覆蓋殘留目錄，請改用新路徑。

工具不會自動刪除原有環境、修改 `.zshrc` / `.bashrc`、切換正在使用的研究專案，或重跑研究資料。

## 可以移除安裝資料夾嗎

正常安裝後，程式與 `insar-check` 都在 Conda 環境內；建置目錄不是執行時依賴。預設 `.work/` 保存下載、編譯、狀態與紀錄，保留可供續跑及排錯。

請保留你指定的 **環境目錄 `--prefix`**。如果自行把環境放在專案或快取裡，移除那個父目錄也會移除環境。另有部分 ISCE2 函式庫連結外部 GCC 14 執行期，請保留該 GCC 14 安裝；本階段不是完全獨立、可任意搬移的二進位套件。

## 版本與可重建性

目前固定使用 Python 3.12、NumPy 1.26.4、GDAL 3.10.3、ISCE2 2.6.5、MintPy 1.6.4.post3 與 SNAPHU 2.0.7。

`conda list` 中的 `snaphu 0.4.1` 是 Python binding；另外從官方來源編譯的命令列 `snaphu` 是 2.0.7。ISCE2 自帶的解纏封裝也隨官方 ISCE2 原始碼建置，這幾個項目不能只靠同名套件的版本欄位判斷。

- `locks/conda-osx-arm64.lock`：精確 Conda 套件 URL 與 MD5。
- `locks/sources.json`：固定版本／commit 的來源與修補檔 URL、SHA256。
- `locks/wheels-osx-arm64-py312.json`：額外 Python wheel 的 URL 與 SHA256。
- SHA256 不符會停止，不會悄悄改用最新版。
- Conda 和 pip 使用鎖定清單；pip 不自行解析、升級相依套件。
- 每次安裝記錄工具指紋、編譯器版本、平台與測試結果。

可重建指「在符合前置條件的機器上，依相同配方重建並驗證」，不保證不同 SDK / 編譯器產出的檔案逐位元相同。未來升級套件應另開新環境測試。

## 支援範圍與已知限制

- 第一階段：Apple Silicon Mac、CPU、bash / zsh。Linux、Intel Mac、Windows / WSL、CUDA 不在此配方支援範圍。
- 使用公開 ISCE2 原始碼，`ISCE2_WITH_STANFORD=OFF`；部分選配的舊模組未包含。不能據此推論所有 Stripmap RAW 處理都不可用；需按衛星與流程驗證。
- mdx 的檔案產圖已測試；互動式 X11 視窗需另備 X server，未納入自動安裝與驗證。
- PyAPS 等需外部服務的實際資料下載仍需使用者帳號與設定。
- SNAP 桌面程式、研究影像下載、NAS 複製、完整研究工作台不包含在這個安裝工具。
- 不是任何套件都能任意升級的環境；安裝其他套件後請重新執行 `insar-check`。

## 開發與貢獻

```sh
python3 -m unittest discover -s tests -v
```

單元測試不需要 ISCE2；GitHub Actions 會執行這些測試。完整 ARM 建置需要符合前置條件的 Mac，目前不宣稱雲端 CI 已執行完整科學流程。

新功能、套件升級與更多衛星範例請附上可重現測試。避免提交 `.work`、環境資料夾、私人 SAR 資料、帳密及含個人路徑的原始報告。授權及既有社群成果見 [THIRD_PARTY.md](THIRD_PARTY.md)；本專案原創安裝工具採 MIT 授權，第三方工具各自的授權仍適用。
