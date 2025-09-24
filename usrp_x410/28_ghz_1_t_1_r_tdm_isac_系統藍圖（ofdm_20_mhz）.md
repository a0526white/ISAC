# 28 GHz 1T1R TDM‑ISAC 系統藍圖（OFDM 20 MHz）

> 目標：以 **USRP + U/D 轉換 + TMYTEK Beamformer（BBox）** 實作 **28 GHz、OFDM 20 MHz、1T1R** 的 **TDM‑ISAC**（Radar+Comms）Demo，強調可落地、可展示、可擴展。

---

## 目錄
1. 系統概覽與指標
2. 方塊圖（Tx / Rx / 時槽 / 控制）
3. 頻率規劃（28 GHz，上下變頻與鏡像/雜散）
4. 波形與參數（OFDM 20 MHz）
5. 時槽設計（TDM‑ISAC 10 ms Frame）
6. 硬體 BOM 與連接
7. 軟體/韌體架構（GNU Radio + PyQt5 + API）
8. PyQt5 GUI 草圖
9. GNU Radio Block 參數表
10. 校準與同步流程（Internal Loopback → OTA）
11. 量測指標與預期數值
12. 風險點與對策
13. Demo 變體（「是否需要雙向互傳？」的兩種呈現）
14. 測試計畫（Step‑by‑Step）
15. 交付清單（給業務與客戶）

---

## 1) 系統概覽與指標
- 頻段：**28 GHz**（可拓至 27–29 GHz 視濾波器）
- 架構：**TDM‑ISAC**（雷達/通訊在 10 ms 影格內切換；雷達時段需 Tx/Rx 同時工作）
- 通道：**1T1R**（單流示範；後續可擴 2T2R/4T4R）
- 波形：**OFDM，佔用 20 MHz**（可視 SCS/FFT 調整）
- Beam：±45° 掃描，**更新 ≥100 Hz**（雷達時段執行掃描）
- 時頻同步：外部 **10 MHz + PPS**（GPSDO/分配器）
- 目標 KPI：
  - 通訊：EVM ≤ **8%**（16QAM），UDP goodput ≥ **20–50 Mbps**（取決於保護與 CP）
  - 雷達：距離解析 **≈ 7.5 m**（BW=20 MHz），速度解析 **≈ 0.2 m/s**（PRF=5 kHz, N=128）
  - ISAC：在 **≥5 Hz** 雷達刷新下，保持 ≥20 Mbps 的資料通訊

---

## 2) 方塊圖
（略，與前一版相同，保持）

---

## 3) 頻率規劃（28 GHz）
（略，與前一版相同，保持）

---

## 4) 波形與參數（OFDM 20 MHz）
（略，與前一版相同，保持）

---

## 5) 時槽設計（TDM‑ISAC 10 ms Frame）
（略，與前一版相同，保持）

---

## 6) 硬體 BOM 與連接
（略，與前一版相同，保持）

---

## 7) 軟體/韌體架構
（略，與前一版相同，保持）

---

## 8) PyQt5 GUI 草圖
```
┌─────────────────────────────────────┐
│ [系統狀態列]  時鐘鎖定 ✓   PPS ✓   溫度: 42°C │
├─────────────────────────────────────┤
│ [分頁] 儀表板 | 通訊 | 雷達 | Beam 控制 | 校準 | 錄放 │
├─────────────────────────────────────┤
│ 儀表板頁面：                          │
│ - 左上：即時頻譜/瀑布圖              │
│ - 右上：Beam-SNR 曲線                │
│ - 左下：EVM/BER 計量表               │
│ - 右下：Range-Doppler 熱圖           │
├─────────────────────────────────────┤
│ 底部控制列： [Start] [Stop] [錄製] [載入掃描表] │
└─────────────────────────────────────┘
```
**特點**：
- 實時更新通訊與雷達指標
- Beam 控制分頁可載入 CSV/JSON beam table，或手動點擊調整
- 校準分頁顯示「內迴路/OTA 校準健康度」指標

---

## 9) GNU Radio Block 參數表
| 區塊 | 功能 | 主要參數 |
|------|------|----------|
| UHD: USRP Sink | 下行發射 | Samp Rate = 30.72 Msps, Center Freq = 2 GHz (IF), Gain = 0–20 dB |
| UHD: USRP Source | 上行接收 | Samp Rate = 30.72 Msps, 同步 10 MHz+PPS |
| OFDM Mod | 通訊 Tx | FFT=2048, CP=144 (1/14), QAM=16/64 |
| OFDM Demod | 通訊 Rx | FFT=2048, 同步=Schmidl&Cox, CFO Estimation=Enabled |
| Channel Est. | 通訊 Rx | Pilot pattern = comb+block, interpolation=linear |
| EVM/BER | 通訊分析 | 更新率=每子幀（1ms） |
| Signal Source (OFDM 序列) | Radar Tx Ref | 同步 Tx Ref 與 Rx Echo |
| Correlator + FFT (Radar) | Range FFT | N=2048, BW=20 MHz, ΔR=7.5 m |
| Doppler FFT | 速度估測 | PRF=5 kHz, N=128, Δv≈0.2 m/s |
| CFAR Block | 目標檢測 | Guard=4, Training=12, Pfa=1e‑3 |
| Python Block (BBox API) | Beam 控制 | 載入掃描表，控制相位/增益 |

---

## 10) 校準與同步流程
（略，與前一版相同，保持）

---

## 11) 量測指標與預期
（略，與前一版相同，保持）

---

## 12) 風險點與對策
（略，與前一版相同，保持）

---

## 13) Demo 變體：是否需要「雙向互傳」？
（略，與前一版相同，保持）

---

## 14) 測試計畫（Step‑by‑Step）
（略，與前一版相同，保持）

---

## 15) 交付清單
（略，與前一版相同，保持）

---

### 備註
- 已新增 **PyQt5 GUI 草圖** 與 **GNU Radio Block 參數表**，可作為初版實作與展示基礎。



---

## 14) PyQt5 GUI 介面規格（可執行初版藍本）
> 目標：單程式啟動，控制 USRP / UDB / BBox，顯示通訊與雷達雙視圖，支援 SigMF 錄放。

**頁籤與面板**
- **儀表板**：裝置狀態（10 MHz/PPS lock、溫度、電源）、模式切換（Radar/Comms/TDM）、Start/Stop、錄放控制
- **通訊**：EVM/BER/Throughput 即時曲線，星座圖、頻譜、瀑布圖；調變、碼率、功率與增益滑桿
- **雷達**：Range‑Doppler 圖、Range‑Profile、目標列表（R、v、θ、SNR、BeamID）、CFAR 閾值與視窗設定
- **Beam 控制**：
  - 掃描表載入（CSV/JSON）/預覽（極座標圖）
  - 角度→相位/增益對映（顯示當前 beam，定相延遲指標）
  - 掃描速率、dwell（µs）、掃描範圍（±°）
- **校準**：內迴路/OTA 校準流程按鈕、進度條、校準健康度（相位/幅度殘差）
- **錄放**：SigMF 錄製（Rx/TX‑ref/Processed）、標籤（場景/目標/環境）、回放速度（×1/×2/×5/×10）

**更新頻率**
- 數據核心以 100–200 Hz 更新（Qt 定時器或 asyncio loop）
- 圖形以 10–30 Hz 重繪（避免 UI 卡頓）

**執行緒/程序**
- **USRP I/O 與 DSP**：獨立工作執行緒（或多進程）
- **GUI 主執行緒**：僅收聽訊號/畫圖；以 thread‑safe queue 傳遞資料

**事件流**
1) 使用者按下 Start → 初始化裝置、載入掃描表、鎖定 10 MHz/PPS → 進入 TDM 調度
2) TDM 計時器：Radar 段觸發 beam 掃描與回波處理；Comms 段切到下行鏈路
3) 指標（EVM/BER/吞吐/ROC）與圖形持續更新；錄製按需寫入 SigMF 檔

---

## 15) GNU Radio Flowgraph 與參數（初版可執行設定）
> 預設採 **Fs = 30.72 Msps、FFT = 2048、Δf = 15 kHz、CP ≈ 1/14**。若資源受限，可切換 **Fs = 20.48 Msps、FFT = 1024、Δf = 20 kHz**（見 §15.6）。

### 15.1 Comms‑Tx（下行）
- Blocks：
  1. UDP/File Source → Packet Framer (length tag) → QAM Mapper (16QAM)
  2. OFDM Carrier Allocator（使用子載波 ≈ 1333、左右 Guard ≈ 355、Pilot 梳狀/塊狀混合）
  3. IFFT(2048) → CP Inserter（CP 長 ≈ 144）→ PAPR/Clipping（適度）
  4. Gain/AGC（數位）→ UHD Sink（center IF = 2 GHz, rate = 30.72 Msps）
- 主要參數：
  - **Pilot pattern**：每 12 子載波一個梳狀 + 每符號一塊參考
  - **輸出功率**：依 PA back‑off，先抓 **–6 dBFS** 峰值

### 15.2 Comms‑Rx（下行）
- Blocks：
  1. UHD Source → DC Blocker / DDC（可選）
  2. 同步：Schmidl‑Cox 偵測（或 PN preamble）→ 符號對齊
  3. CFO/IFO 校正 → FFT(2048)
  4. Pilot‑aided 通道估計（LS→LMMSE 可選）→ 等化（ZF/MMSE）
  5. QAM 解映射 → 解包 → EVM/BER 計算 → Throughput 計數
- 主要參數：
  - **EVM 視窗**：100–200 ms 滑動
  - **CFO 追蹤**：二階鎖環，更新速率 ≥ 100 Hz

### 15.3 Radar‑Proc（OFDM‑JRC / Radar 段）
- 共用 Tx 參考序列（記錄 Tx‑ref）與 Rx 回波；
- Blocks：
  1. Segmentation：按 TDM Radar 段切割取樣
  2. Range FFT：對子載波維做 **IFFT/FFT**（視採用的 OFDM‑Radar 架構）
  3. Doppler FFT：對慢時間（N_sym）做 FFT（例 **N=128**）
  4. CFAR（2D，CA‑CFAR，Guard=2×2，Train=8×8，可調）
  5. Beam 維度：同一 dwell 多 beam 堆疊，輸出 R‑D‑Beam cube
  6. 目標形成：峰值擷取 → List(R, v, θ, SNR, BeamID)
- 參數建議：
  - **PRF ≈ 5 kHz**（每 dwell 150–200 µs 內放 2–3 個 OFDM 參考區段）
  - **N_range**：等於佔用子載波數（~1333）→ 可依需要 decimate 至 512/1024 顯示
  - **Windowing**：Hann/Hamming 於兩個 FFT 維度

### 15.4 TDM 調度器（Python Block）
- 輸入：當前時間戳、frame counter、GUI 設定
- 輸出：
  - 切換 **Radar/Comms** 的 tag、路由與 UHD 命令
  - Radar 段觸發 **BBox beam 下一筆**；Comms 段恢復最佳 beam

### 15.5 量測器（Metrics）
- **通訊**：EVM、MER、BER、goodput、丟包率、CFO/IFO、RSSI/SNR
- **雷達**：峰值 SNR、Pd/Pfa、R‑v 解算結果數、Beam 命中率

### 15.6 輕量化配置（可切換）
- **Fs = 20.48 Msps、FFT = 1024、Δf = 20 kHz**；佔用 ≈ 900–960 子載波；其餘流程一致

---

## 16) 預設參數（Config 檔示例，YAML）
```yaml
radio:
  fs: 30.72e6
  if_hz: 2.0e9
  rf_hz: 28.0e9
  lo_hz: 26.0e9
  tx_gain_db: 0.0   # 依實測與 PA back-off 調整
  rx_gain_db: 20.0  # 起步值
  ref_10mhz: external
  pps: external
ofdm:
  fft: 2048
  scs_hz: 15000
  n_used_sc: 1333
  cp_len: 144
  modulation: QAM16
  pilots:
    comb_step: 12
    block_every_sym: true
radar:
  dwell_us: 180
  prf_hz: 5000
  n_doppler: 128
  cfar:
    type: CA2D
    guard: [2,2]
    train: [8,8]
    pfa: 1e-3
beam:
  sweep_deg: [-45, 45]
  n_beams: 9
  settle_us: 50
sigmf:
  enable_record: true
  paths:
    rx_echo: ./rec/rx_echo.sigmf
    tx_ref: ./rec/tx_ref.sigmf
```

---

## 17) BBox 掃描表（CSV/JSON 範例）
> 針對 4‑ch 與 8‑ch 兩種版型提供模板。欄位可依 BBox API 版本調整。

**CSV（4‑ch 範例）**
```csv
beam_id,az_deg,el_deg,ch1_phase_deg,ch1_gain_db,ch2_phase_deg,ch2_gain_db,ch3_phase_deg,ch3_gain_db,ch4_phase_deg,ch4_gain_db
0,-45,0,  315,0,  225,0,  135,0,   45,0
1,-35,0,  300,0,  220,0,  140,0,   60,0
2,-25,0,  285,0,  235,0,  155,0,   75,0
3,-15,0,  270,0,  250,0,  170,0,   90,0
4,  0,0,  255,0,  255,0,  255,0,  255,0
5, 15,0,  240,0,  270,0,  190,0,  110,0
6, 25,0,  225,0,  285,0,  205,0,  125,0
7, 35,0,  210,0,  300,0,  220,0,  140,0
8, 45,0,  195,0,  315,0,  235,0,  155,0
```

**JSON（8‑ch 範例）**
```json
[
  {"beam_id":0, "az":-45, "el":0, "ph":[315,225,135,45,315,225,135,45], "ga":[0,0,0,0,0,0,0,0]},
  {"beam_id":1, "az":-35, "el":0, "ph":[300,220,140,60,300,220,140,60], "ga":[0,0,0,0,0,0,0,0]},
  {"beam_id":2, "az":-25, "el":0, "ph":[285,235,155,75,285,235,155,75], "ga":[0,0,0,0,0,0,0,0]},
  {"beam_id":3, "az":-15, "el":0, "ph":[270,250,170,90,270,250,170,90], "ga":[0,0,0,0,0,0,0,0]},
  {"beam_id":4, "az":0,  "el":0, "ph":[255,255,255,255,255,255,255,255], "ga":[0,0,0,0,0,0,0,0]},
  {"beam_id":5, "az":15, "el":0, "ph":[240,270,190,110,240,270,190,110], "ga":[0,0,0,0,0,0,0,0]},
  {"beam_id":6, "az":25, "el":0, "ph":[225,285,205,125,225,285,205,125], "ga":[0,0,0,0,0,0,0,0]},
  {"beam_id":7, "az":35, "el":0, "ph":[210,300,220,140,210,300,220,140], "ga":[0,0,0,0,0,0,0,0]},
  {"beam_id":8, "az":45, "el":0, "ph":[195,315,235,155,195,315,235,155], "ga":[0,0,0,0,0,0,0,0]}
]
```
> 註：實際相位表需依天線元素間距與期望主瓣方向重新產生；此處為展示格式與 GUI 測試用途。

---

## 18) SigMF 錄製（最小 metadata 範例）
```json
{
  "global": {
    "datatype": "cf32",
    "sample_rate": 30.72e6,
    "version": "1.0.0",
    "hw": "USRP X410 + UDB0630 + BBox",
    "description": "28GHz TDM-ISAC demo, Rx echo / Tx ref",
    "recorder": "tmylab-isac"
  },
  "captures": [
    {"core:frequency": 2.0e9, "core:datetime": "2025-08-31T00:00:00Z", "isac:mode": "radar"}
  ],
  "annotations": [
    {"core:sample_start": 0, "core:sample_count": 614400, "isac:beam_id": 4, "isac:frame": 1}
  ]
}
```

---

## 19) 執行腳本（啟動順序概述）
1. 啟動外部 10 MHz + PPS；確認鎖定（ULN‑1100/OctoClock）
2. 啟動 `tm_isac_gui.py`（讀取 YAML 與 CSV/JSON 掃描表）
3. GUI 儀表板顯示 LOCK → 按 **Start** 進入 TDM 調度
4. 視需要按 **Record** 產生 SigMF；或切 **Replay** 做離線除錯

---

## 20) 後續可選強化
- RFNoC：將 Range/Doppler FFT 與 CFAR 下放，Host 輕量化
- DPD：針對 28 GHz PA 建立 LUT/記憶多項式
- 雙向互傳：加入 UE‑SDR，展示 UL 與 bi‑static 量測
- AI‑Beam：以掃描資料訓練 XGBoost/CNN，做快速 beam 預測

