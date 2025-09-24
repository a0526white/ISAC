# TMYTEK 28 GHz OFDM-ISAC 模組化實作

## 📦 模組總覽

本套件提供了模組化的GNU Radio 3.10流程圖，針對UHD 4.8和USRP X410優化，用於28 GHz OFDM-ISAC系統開發。

### 🔧 環境需求
- **Linux** (Ubuntu 20.04/22.04 建議)
- **GNU Radio 3.10.x**
- **UHD 4.8.x**
- **Python 3.10.12**
- **USRP X410 + UDB0630 + TMYTEK BBox**

---

## 📁 檔案結構

```
├── config_parameters.py          # 共用參數配置
├── ofdm_tx_basic.grc             # 基礎OFDM發射器
├── ofdm_rx_basic.grc             # 基礎OFDM接收器
├── ofdm_loopback_test.grc        # 有線Loopback測試
├── debug_data/                   # 除錯資料輸出目錄
└── README_modules.md             # 本說明文件
```

---

## 🚀 快速開始

### 1. 環境準備
```bash
# 建立除錯資料目錄
mkdir -p debug_data

# 確認GNU Radio版本
gnuradio-companion --version

# 確認UHD版本
uhd_find_devices
```

### 2. 模組測試順序

#### Step 1: 參數配置測試
```bash
python3 config_parameters.py
```
**預期輸出**: 顯示OFDM配置摘要，包含採樣率、FFT長度、星座圖點數等。

#### Step 2: 軟體Loopback測試 
```bash
gnuradio-companion ofdm_loopback_test.grc
```
**功能**: 
- 產生QAM16 OFDM訊號
- 通過軟體通道模擬（可調整噪聲）
- 即時顯示Tx/Rx頻譜與星座圖
- 觀察EVM性能

**調整參數**:
- `Noise Level`: 調整通道噪聲 (0~1)
- 觀察星座圖收斂情況

#### Step 3: USRP發射測試
```bash
gnuradio-companion ofdm_tx_basic.grc
```
**功能**:
- 發射30.72 Msps OFDM訊號 @ 2GHz
- 頻譜分析與File Sink記錄
- 驗證USRP Tx功能

**注意**: 確認USRP連接且無錯誤訊息。

#### Step 4: USRP接收測試
```bash
gnuradio-companion ofdm_rx_basic.grc
```
**功能**:
- 接收並解調OFDM訊號
- 同步、等化、星座圖顯示
- 驗證USRP Rx功能

---

## ⚙️ 核心模組說明

### `config_parameters.py`
**功能**: 統一的參數配置模組
- **OFDMConfig類**: 採樣率、FFT長度、調變、導頻設計
- **TDMConfig類**: TDM時槽、雷達參數、波束掃描
- **可重用**: 所有.grc檔案都可引用此配置

**關鍵參數**:
```python
sample_rate = 30.72e6       # 30.72 Msps
fft_len = 2048              # FFT size  
cp_len = 144                # CP length (≈7%)
occupied_carriers = 1200    # 使用的子載波數
modulation = "qam16"        # QAM16調變
```

### `ofdm_tx_basic.grc`
**功能**: 基礎OFDM發射器
- **資料流**: Random → QAM16 → Carrier Allocator → IFFT → CP → USRP
- **導頻插入**: 每50個子載波一個導頻
- **同步字元**: Schmidl-Cox preamble
- **輸出**: USRP Sink @ 2GHz + 頻譜顯示 + File Sink

### `ofdm_rx_basic.grc`
**功能**: 基礎OFDM接收器
- **資料流**: USRP → Sync → Equalizer → Serializer → Constellation Decoder
- **同步方法**: Schmidl-Cox偵測
- **通道等化**: 導頻輔助等化器
- **輸出**: 星座圖、頻譜顯示、解調資料

### `ofdm_loopback_test.grc`
**功能**: 完整Loopback驗證
- **Tx Chain**: 同ofdm_tx_basic
- **Channel**: 軟體通道模擬（AWGN + 可調噪聲）
- **Rx Chain**: 同ofdm_rx_basic
- **GUI**: 雙路比較（Tx vs Rx）、EVM數值顯示、即時調整滑桿

---

## 🔍 除錯與驗證

### 檔案輸出
每個流程圖都會在`debug_data/`目錄產生`.bin`檔案：
- `tx_ofdm_signal.bin`: 發射訊號（complex float32）
- `rx_ofdm_signal.bin`: 接收訊號（complex float32）

### 離線分析
```python
import numpy as np
import matplotlib.pyplot as plt

# 讀取發射訊號
tx_data = np.fromfile('debug_data/tx_ofdm_signal.bin', dtype=np.complex64)
print(f"Tx samples: {len(tx_data)}")

# 繪製頻譜
plt.figure()
plt.psd(tx_data, NFFT=2048, Fs=30.72e6)
plt.title('Tx Signal PSD')
plt.show()
```

### 常見問題排除

1. **USRP找不到設備**
   ```bash
   uhd_find_devices --args="type=usrp"
   # 確認網路連接與IP設定
   ```

2. **GNU Radio版本不相容**
   ```bash
   # 檢查block名稱是否正確
   grep -r "blocks_signal_source" /usr/share/gnuradio/grc/blocks/
   ```

3. **記憶體使用過高**
   - 調降packet_len (預設100)
   - 增加buffer管理
   - 檢查File Sink檔案大小

4. **EVM過高**
   - 降低噪聲電平
   - 檢查時序同步
   - 確認導頻序列正確

---

## 🎛️ 參數調整指南

### OFDM參數優化
```python
# 效能 vs 複雜度權衡
fft_len = 1024      # 降低計算負載
cp_len = 72         # 縮短CP (仍>最大延遲擴散)
occupied_carriers = 600  # 降低佔用頻寬

# 調變階數調整
modulation = "qpsk"     # 降階提升可靠性
# 或
modulation = "qam64"    # 升階提升頻譜效率
```

### 同步參數調整
```python
# 同步閾值
sync_threshold = 0.8    # 降低→更敏感，提高→更可靠

# 導頻密度
pilot_spacing = 25      # 更密集→更好通道估計，更稀疏→更高效率
```

---

## 🔗 後續整合

### BBox API整合
```python
# 在.grc中加入自訂Python Block
import tmytek_bbox_api

class BeamController:
    def work(self, input_items, output_items):
        # 波束切換邏輯
        beam_id = self.get_next_beam()
        tmytek_bbox_api.set_beam(beam_id)
```

### TDM調度整合
```python
# TDM時槽切換
if current_slot == "radar":
    self.enable_radar_mode()
elif current_slot == "comms":
    self.enable_comms_mode()
```

### 雷達處理整合
```python
# Range-Doppler處理
range_fft = np.fft.ifft(ofdm_symbols, axis=0)  # Range dimension
doppler_fft = np.fft.fft(range_fft, axis=1)    # Doppler dimension
```

---

## 📈 性能基準

### 目標指標
- **EVM**: ≤ 8% (QAM16)
- **同步時間**: ≤ 10ms (冷開始)
- **處理延遲**: ≤ 1ms (即時系統)
- **記憶體使用**: ≤ 512MB

### 測試條件
- **SNR**: 20dB (AWGN)
- **採樣率**: 30.72 Msps
- **封包長度**: 100 symbols
- **硬體**: Intel i7-10700K + 16GB RAM

---

## 📝 開發筆記

### 已知限制
1. **單天線**: 目前只支援1T1R，多天線需修改carrier allocator
2. **固定調變**: 目前只支援QAM16，動態調變需額外開發
3. **無FEC**: 未加入通道編碼，可靠性依賴重傳

### 擴展計畫
1. **多天線MIMO**: 擴展至2T2R/4T4R
2. **自適應調變**: 根據通道品質動態切換
3. **雷達模組**: 加入Range-Doppler處理
4. **TDM調度**: 實現完整時分切換

---

## 📞 技術支援

如有問題，請檢查：
1. **日誌檔**: GNU Radio console輸出
2. **除錯檔案**: `debug_data/`目錄內容
3. **硬體狀態**: USRP LED指示與UHD log
4. **參數設定**: 與`config_parameters.py`比對

**聯絡資訊**: TMYTEK ISAC Lab
