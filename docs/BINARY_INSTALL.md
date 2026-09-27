# InSAR ARM 0.2.0 beta 1：免編譯安裝

這是 Apple Silicon Mac 的公開測試版。整合 ISCE2、三種 Stack、MintPy、SNAPHU、GDAL、mdx、ImageMagick 和環境檢查工具。使用者不需要 Homebrew GCC 或自行編譯；需要已安裝原生 ARM Conda，以及 macOS 14.5 或更新。

[下載 Release](https://github.com/chris20011026/insar-arm/releases/tag/v0.2.0-beta.1) · [English](BINARY_INSTALL.en.md)

## 建議方式：安裝完全相同的版本

1. 從 Release 下載並解開 `insar-arm-0.2.0b1.zip`。
2. 在終端機進入解開的資料夾，執行：

```sh
bash install-binary.sh --prefix "$HOME/conda-envs/insar_arm_beta"
```

工具會使用固定 URL 與校驗碼下載測試過的套件，建立全新環境，再執行 `insar-check`。已有相同路徑時會停止，不會覆蓋原環境。請使用不含空白的新路徑。

3. 安裝成功後：

```sh
conda activate "$HOME/conda-envs/insar_arm_beta"
use_alosStack
```

不指定 `--prefix` 時預設使用 Conda 的 `insar_arm`；若已存在，也會停止。下載失敗留下的目錄不會自動刪除，請選另一個新路徑或自行檢查後處理。

## 另一種方式：直接使用 channel

```sh
conda create -n insar_arm_beta --strict-channel-priority --override-channels \
  -c https://chris20011026.github.io/insar-arm -c conda-forge insar-arm=0.2.0b1
conda activate insar_arm_beta
insar-check
```

請使用尚未存在的環境名稱。這個方式會重新解析相依，未必與發布時完全相同；需要穩定重建時，優先使用上面的固定版本安裝工具。

## 日常使用

| 工作 | 命令 |
|---|---|
| ALOS-2 多日期 | `use_alosStack`，接著使用 `create_cmds.py` |
| Sentinel-1 多日期 | `use_topsStack`，接著使用 `stackSentinel.py` |
| Stripmap 多日期 | `use_stripmapStack`，接著使用 `stackStripMap.py` |
| MintPy | `use_mintpy`，接著使用 `smallbaselineApp.py` |
| 雙日期 | `topsApp.py`、`alos2App.py`、`stripmapApp.py` |
| 檢查與報告 | `insar-check` |

這些命令不會自動啟動你的研究資料處理。完整環境已提供命令切換、字型配置和驗證工具，無須手動編輯 `.zshrc`。Conda 環境必須透過 `conda activate` 啟用。

## 版本與適用範圍

- ISCE2 2.6.5、MintPy 1.6.4、SNAPHU CLI 2.0.7、Python 3.12、NumPy 1.26.4、GDAL 3.10 系列。
- MintPy 改用 conda-forge 的正式 1.6.4 套件，與第一階段自行建置的 1.6.4.post3 不同，已另做合成反演驗證。
- `conda list` 的 `snaphu 0.4.1` 是 Python binding；`insar-arm-snaphu-cli` 才是 2.0.7 命令列工具。
- 僅 CPU、Apple Silicon macOS；不是 Intel Mac、Windows 或 Linux 安裝配方。SNAP 桌面程式仍須另外安裝。
- 已驗證範圍見 [驗證紀錄](BINARY_VALIDATION.md)。六種入口能啟動，不代表所有衛星資料的完整研究流程已認證。
- 合成測試不使用私人 SAR 資料。線上資料與氣象服務可能仍需要使用者自行設定帳號。

## 授權與來源

安裝及驗證工具採 MIT；各依賴保留各自授權。**含 CS2 的 SNAPHU / ISCE2 元件有非商業用途限制，不能把整個環境當成不受限制的商業套件。**

Release 提供 `insar-arm-0.2.0b1-sources.tar.gz`，內含自製原生套件對應的上游來源、修補與建置工具；SHA256 清單隨附。ISCE2 套件內也保留 `share/isce2/upstream-source.tar.gz`，SNAPHU 保留 `share/snaphu/README`。其他 Conda 套件直接從 conda-forge 取得，保留其套件內授權資料。

需要回報另一台 Mac 的結果時，執行 `insar-check --output "$HOME/insar-validation"`；分享報告前請檢查其中的本機路徑。請附 Mac 晶片、macOS 版本、成功或失敗項目，並避免附私人影像或帳號資料。
