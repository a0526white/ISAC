# 28 GHz 1T1R TDM‑ISAC 系統藍圖（增強完整版）

> 基於原藍圖，補充關鍵技術細節、風險緩解策略與完整測試驗證計畫

---

## 目錄
1. [系統概覽與指標](#1-系統概覽與指標)
2. [詳細頻率規劃與RF校準](#2-詳細頻率規劃與rf校準)
3. [TDM時序設計與硬體響應](#3-tdm時序設計與硬體響應)
4. [同步與校準完整流程](#4-同步與校準完整流程)
5. [系統整合與風險緩解](#5-系統整合與風險緩解)
6. [GNU Radio即時性能優化](#6-gnu-radio即時性能優化)
7. [段階性測試驗證計畫](#7-段階性測試驗證計畫)
8. [完整配置文件](#8-完整配置文件)
9. [風險矩陣與緩解策略](#9-風險矩陣與緩解策略)
10. [法規與標準相容性](#10-法規與標準相容性)

---

## 1) 系統概覽與指標
> 承襲原藍圖，保持核心指標不變

- 頻段：**28 GHz**（27.5-28.35 GHz，符合各國5G mmWave分配）
- 架構：**TDM‑ISAC**（10ms frame，雷達/通訊時分切換）
- 通道：**1T1R**（可擴展至2T2R/4T4R）
- 波形：**OFDM 20MHz**（FFT=2048, SCS=15kHz）
- Beam：±45° 掃描，更新≥100Hz
- 同步：外部10MHz+PPS（GPSDO級精度）

---

## 2) 詳細頻率規劃與RF校準

### 2.1 頻率分配與轉換
```
RF: 28.0 GHz (可調 27.5-28.35 GHz)
LO: 26.0 GHz (固定，避免頻繁重鎖)
IF: 2.0 GHz (USRP操作頻段)
BBF: 20 MHz (OFDM佔用頻寬)
```

### 2.2 關鍵RF指標
| 參數 | 目標值 | 測試方法 |
|------|--------|----------|
| LO洩漏抑制 | ≤-50 dBc | 頻譜分析儀@28GHz |
| 鏡像抑制比 | ≤-40 dBc | 雙音測試 |
| I/Q相位誤差 | ≤0.5° | 星座圖分析 |
| I/Q幅度誤差 | ≤0.1 dB | 星座圖分析 |
| 相位噪聲@10kHz | ≤-90 dBc/Hz | 相位噪聲分析儀 |
| 1dB壓縮點 | ≥10 dBm | 功率掃描 |

### 2.3 RF校準流程
```python
# RF校準序列（embedded in GNU Radio）
def rf_calibration_sequence():
    # 1. LO洩漏校正
    dc_offset_i, dc_offset_q = measure_lo_leakage()
    apply_dc_correction(dc_offset_i, dc_offset_q)
    
    # 2. I/Q不平衡校正
    phase_err, amp_err = measure_iq_imbalance()
    apply_iq_correction(phase_err, amp_err)
    
    # 3. 通道群延遲校正
    delay_tx, delay_rx = measure_group_delay()
    apply_delay_correction(delay_tx, delay_rx)
    
    # 4. 驗證校準效果
    evm_post = measure_evm()
    return evm_post < 2.0  # 2% EVM threshold
```

---

## 3) TDM時序設計與硬體響應

### 3.1 精確時序分配（10ms Frame）
```
Frame Structure (10ms = 307,200 samples @ 30.72Msps):
┌─────┬─────────────────────┬─────┬─────────────────────────────┬─────┐
│Guard│     Radar Slot      │Guard│        Comms Slot           │Guard│
│50μs │        2ms          │50μs │          7.85ms             │50μs │
│1536 │      61,440         │1536 │        241,152             │1536 │
└─────┴─────────────────────┴─────┴─────────────────────────────┴─────┘
```

### 3.2 硬體切換時序預算
| 動作 | 時間預算 | 備註 |
|------|----------|------|
| BBox beam切換 | 30μs | 相位器設定+穩定 |
| UDB T/R切換 | 10μs | PIN二極體切換 |
| USRP gain切換 | 5μs | 數位增益調整 |
| Stream routing | 5μs | GNU Radio tag routing |
| **總切換時間** | **50μs** | 包含餘裕 |

### 3.3 TDM調度器實作
```python
class TDMScheduler:
    def __init__(self, frame_len=307200):
        self.frame_len = frame_len
        self.radar_start = 1536
        self.radar_len = 61440
        self.comms_start = 64512
        self.comms_len = 241152
        
    def work(self, input_items, output_items):
        sample_num = self.nitems_read(0)
        frame_pos = sample_num % self.frame_len
        
        if self.radar_start <= frame_pos < (self.radar_start + self.radar_len):
            self.send_command("bbox", "next_beam")
            self.send_command("udb", "tx_rx_mode")
            mode = "radar"
        elif self.comms_start <= frame_pos < (self.comms_start + self.comms_len):
            self.send_command("bbox", "best_beam")
            self.send_command("udb", "tx_mode")
            mode = "comms"
        else:
            mode = "guard"
            
        # Add stream tags
        self.add_item_tag(0, self.nitems_written(0), 
                         pmt.intern("mode"), pmt.intern(mode))
```

---

## 4) 同步與校準完整流程

### 4.1 時鐘同步架構
```
GPSDO (1PPS + 10MHz) 
    ├── USRP External Ref
    ├── UDB Reference Clock
    └── BBox Control Timing
```

### 4.2 校準階段定義
#### Phase 1: RF前端校準
- [ ] LO洩漏消除（DC offset correction）
- [ ] I/Q平衡校正（Phase/Amplitude imbalance）
- [ ] 通道間延遲校正（TX/RX path delay）

#### Phase 2: 天線校準
- [ ] BBox相位器校準（已知角度vs實際beam pattern）
- [ ] 天線元素校準（互耦與增益不一致性）
- [ ] 極化校準（Cross-pol isolation）

#### Phase 3: 系統校準
- [ ] TDM時序校準（Frame alignment precision）
- [ ] 雷達回波校準（已知目標距離驗證）
- [ ] 通訊鏈路校準（EVM optimization）

### 4.3 校準健康度監控
```yaml
calibration_health:
  rf_frontend:
    lo_leakage_db: -52.3      # Current measurement
    iq_phase_deg: 0.2         # Current I/Q phase error
    iq_amp_db: 0.05           # Current I/Q amplitude error
    status: "GOOD"            # GOOD/WARN/FAIL
  beam_pattern:
    peak_error_deg: 1.2       # Peak direction error
    sidelobe_level_db: -18.5  # Peak sidelobe level
    status: "GOOD"
  timing:
    frame_jitter_ns: 15.3     # Frame alignment jitter
    beam_settle_us: 28.7      # Beam switching settle time
    status: "GOOD"
```

---

## 5) 系統整合與風險緩解

### 5.1 功率預算分析（28 GHz鏈路）
```
Tx Chain:
USRP DAC: +5 dBm → UDB PA: +30 dBm → BBox: +33 dBm EIRP
Cable Loss: -1.5 dB, Connector Loss: -0.5 dB

Rx Chain:
Antenna: -10 dBm → BBox: -7 dBm → UDB LNA: +20 dB → USRP: +13 dBm
Noise Figure: BBox(3dB) + UDB(2dB) + USRP(6dB) = 11dB (system)

Link Budget (10m range):
Tx Power: +33 dBm EIRP
Path Loss (28GHz, 10m): -92 dBm
Rx Sensitivity: -80 dBm (for 2% EVM)
Link Margin: +13 dB ✓
```

### 5.2 溫度管理策略
```python
class ThermalManager:
    def __init__(self):
        self.temp_sensors = ["usrp", "udb", "bbox"]
        self.temp_limits = {"usrp": 85, "udb": 70, "bbox": 60}
        
    def thermal_control(self):
        for sensor in self.temp_sensors:
            temp = self.read_temperature(sensor)
            if temp > self.temp_limits[sensor]:
                self.apply_thermal_mitigation(sensor, temp)
    
    def apply_thermal_mitigation(self, device, temp):
        if device == "usrp":
            self.reduce_tx_power(3)  # Reduce by 3dB
        elif device == "udb":
            self.enable_cooling_fan()
        elif device == "bbox":
            self.reduce_beam_duty_cycle(0.8)
```

---

## 6) GNU Radio即時性能優化

### 6.1 處理能力評估
```python
# 計算處理負載
sample_rate = 30.72e6  # 30.72 Msps
ofdm_fft = 2048
radar_fft = 2048 * 128  # Range x Doppler
fps_requirement = 100   # 100 Hz GUI update

# CPU需求估算
ofdm_ops_per_sec = sample_rate * np.log2(ofdm_fft) * 2  # IFFT+FFT
radar_ops_per_sec = fps_requirement * np.log2(radar_fft) * 2
total_mops = (ofdm_ops_per_sec + radar_ops_per_sec) / 1e6

print(f"估算需求: {total_mops:.1f} MOPS")
# 建議: Intel i7-10700K以上 或 AMD Ryzen 7以上
```

### 6.2 記憶體優化策略
```python
# 循環緩衝區設計
class CircularBuffer:
    def __init__(self, size_mb=512):
        self.size_samples = int(size_mb * 1e6 / 8)  # cf32 = 8 bytes
        self.buffer = np.zeros(self.size_samples, dtype=np.complex64)
        self.write_ptr = 0
        self.read_ptr = 0
        
    def write(self, data):
        # 避免記憶體重新分配
        len_data = len(data)
        if self.write_ptr + len_data > self.size_samples:
            # Wrap around
            self.buffer[self.write_ptr:] = data[:self.size_samples-self.write_ptr]
            self.buffer[:len_data-(self.size_samples-self.write_ptr)] = \
                data[self.size_samples-self.write_ptr:]
        else:
            self.buffer[self.write_ptr:self.write_ptr+len_data] = data
        self.write_ptr = (self.write_ptr + len_data) % self.size_samples
```

### 6.3 RFNoC加速選項
```yaml
# RFNoC卸載配置（X410限定）
rfnoc_blocks:
  fft_range:
    enable: true
    fft_size: 2048
    overlap: 0.5
    location: "FPGA"
  fft_doppler:
    enable: true  
    fft_size: 128
    location: "FPGA"
  cfar_detector:
    enable: false  # 暫時host-based
    guard_cells: [2, 2]
    training_cells: [8, 8]
```

---

## 7) 段階性測試驗證計畫

### 7.1 Phase 1: RF基礎驗證（Week 1-2）
**目標**: 驗證28 GHz RF鏈路基本功能
- [ ] **測試1.1**: UDB上下變頻器單獨測試
  - 輸入: 2GHz CW, 輸出: 28GHz CW
  - 驗證: 轉換增益、雜散、相位噪聲
- [ ] **測試1.2**: BBox beam pattern量測  
  - 設備: 近場掃描儀或far-field chamber
  - 驗證: 9個beam的實際方向vs理論
- [ ] **測試1.3**: 完整RF鏈路測試
  - 配置: USRP → UDB → BBox → (空中) → BBox → UDB → USRP
  - 驗證: 鏈路損耗、EVM、頻率響應

### 7.2 Phase 2: OFDM通訊驗證（Week 3-4）
**目標**: 建立穩定的OFDM通訊鏈路
- [ ] **測試2.1**: 有線OFDM測試
  - 配置: USRP Tx → Cable+Atten → USRP Rx
  - 驗證: EVM<2%, BER<1e-3, CFO tracking
- [ ] **測試2.2**: 28GHz OFDM測試
  - 配置: 完整RF鏈路，固定beam
  - 驗證: EVM<8%, goodput>20Mbps
- [ ] **測試2.3**: Beam掃描通訊測試
  - 配置: 固定時間beam掃描
  - 驗證: 通訊中斷時間<10ms

### 7.3 Phase 3: 雷達功能驗證（Week 5-6）  
**目標**: 驗證雷達檢測與追蹤能力
- [ ] **測試3.1**: Corner reflector檢測
  - 目標: 10cm corner reflector @ 5m
  - 驗證: 距離精度±0.5m, SNR>20dB
- [ ] **測試3.2**: 移動目標檢測
  - 目標: 運動中的金屬板
  - 驗證: 速度精度±0.2m/s, Doppler resolution
- [ ] **測試3.3**: Multi-beam雷達
  - 目標: 不同角度的多個目標
  - 驗證: 角度分辨率±5°, false alarm rate

### 7.4 Phase 4: TDM-ISAC整合（Week 7-8）
**目標**: 驗證雷達與通訊同時運作
- [ ] **測試4.1**: TDM切換驗證
  - 驗證: 切換時間<50μs, 無串流中斷
- [ ] **測試4.2**: ISAC性能測試  
  - 目標: 同時檢測目標與傳輸資料
  - 驗證: 雷達更新率≥5Hz, 通訊goodput≥20Mbps
- [ ] **測試4.3**: 長時間穩定性測試
  - 配置: 連續運行24小時
  - 驗證: 無記憶體洩漏, 性能無衰減

---

## 8) 完整配置文件

### 8.1 主配置文件 (`config/isac_main.yaml`)
```yaml
# 28 GHz TDM-ISAC 主配置文件
system:
  name: "TMYTEK 28GHz TDM-ISAC Demo"
  version: "1.0.0"
  description: "1T1R OFDM 20MHz, Beam-scanning ISAC"

radio:
  # 頻率配置
  rf_hz: 28.0e9
  if_hz: 2.0e9
  lo_hz: 26.0e9
  bandwidth_hz: 20e6
  sample_rate: 30.72e6
  
  # 增益配置
  usrp_tx_gain_db: 0.0
  usrp_rx_gain_db: 20.0
  udb_tx_gain_db: 30.0
  udb_rx_gain_db: 20.0
  
  # 同步配置
  ref_source: "external"    # external/internal
  pps_source: "external"    # external/internal
  
  # 校準配置
  calibration:
    auto_cal_on_start: true
    cal_interval_hours: 24
    rf_cal_targets:
      lo_leakage_db: -50
      image_reject_db: -40
      iq_phase_deg: 0.5
      iq_amp_db: 0.1

ofdm:
  # 基本參數
  fft_size: 2048
  cp_length: 144
  scs_hz: 15000
  n_used_subcarriers: 1333
  n_guard_subcarriers: 355
  
  # 調變配置
  modulation: "QAM16"       # QPSK/QAM16/QAM64
  coding_rate: 0.75
  
  # 導頻配置
  pilot_pattern:
    type: "comb_block"      # comb/block/comb_block
    comb_spacing: 12
    block_period: 4
    pilot_power_db: 3
  
  # 同步配置
  sync:
    method: "schmidl_cox"   # schmidl_cox/pn_sequence
    threshold: 0.6
    search_window: 1000

radar:
  # 基本參數
  dwell_time_us: 180
  prf_hz: 5000
  n_doppler_bins: 128
  n_range_bins: 1333       # 等於使用的子載波數
  
  # 處理參數
  window_type: "hann"      # hann/hamming/blackman
  overlap_ratio: 0.5
  
  # CFAR檢測
  cfar:
    type: "CA_2D"          # CA_2D/OS_2D/GO_2D
    guard_cells: [2, 2]    # [range, doppler]
    training_cells: [8, 8] # [range, doppler]
    pfa: 1e-3
    threshold_factor: 1.5

beam:
  # 掃描配置
  n_beams: 9
  azimuth_range_deg: [-45, 45]
  elevation_deg: 0
  scan_rate_hz: 100
  dwell_time_us: 180
  settle_time_us: 30
  
  # 天線配置
  n_elements: 4            # 4-ch or 8-ch BBox
  element_spacing_mm: 5.4  # λ/2 @ 28GHz
  
  # 掃描表檔案
  scan_table_file: "config/beam_scan_table.json"

tdm:
  # 時框配置
  frame_duration_ms: 10
  radar_duration_ms: 2
  comms_duration_ms: 7.85
  guard_duration_us: 50
  
  # 調度配置
  scheduler_priority: "realtime"
  buffer_size_ms: 50
  
timing:
  # GUI更新率
  gui_update_hz: 30
  metrics_update_hz: 100
  plot_update_hz: 10
  
  # 處理配置
  processing_threads: 4
  max_buffer_size_mb: 512

sigmf:
  # 錄製配置
  auto_record: false
  record_duration_sec: 60
  max_file_size_gb: 2
  
  # 檔案路徑
  output_directory: "./recordings"
  rx_filename_template: "rx_echo_{timestamp}.sigmf"
  tx_filename_template: "tx_ref_{timestamp}.sigmf"
  
  # Metadata
  global_info:
    hw: "USRP X410 + UDB0630 + TMYTEK BBox"
    author: "TMYTEK ISAC Lab"
  
debug:
  log_level: "INFO"        # DEBUG/INFO/WARNING/ERROR
  enable_profiling: true
  save_intermediate_data: false
  plot_constellation: true
  plot_range_doppler: true
```

### 8.2 波束掃描表 (`config/beam_scan_table.json`)
```json
{
  "metadata": {
    "description": "28 GHz 4-element beam scanning table",
    "frequency_ghz": 28.0,
    "element_spacing_mm": 5.4,
    "generated_date": "2024-01-15",
    "coordinate_system": "azimuth_elevation"
  },
  "beams": [
    {
      "beam_id": 0,
      "description": "Left edge beam",
      "azimuth_deg": -45,
      "elevation_deg": 0,
      "phases_deg": [315, 225, 135, 45],
      "gains_db": [0, 0, 0, 0],
      "expected_gain_db": 12.0,
      "sidelobe_level_db": -15.0
    },
    {
      "beam_id": 1,
      "description": "Left mid beam",
      "azimuth_deg": -35,
      "elevation_deg": 0,
      "phases_deg": [300, 220, 140, 60],
      "gains_db": [0, 0, 0, 0],
      "expected_gain_db": 12.2,
      "sidelobe_level_db": -16.0
    },
    {
      "beam_id": 2,
      "description": "Left quarter beam",
      "azimuth_deg": -25,
      "elevation_deg": 0,
      "phases_deg": [285, 235, 155, 75],
      "gains_db": [0, 0, 0, 0],
      "expected_gain_db": 12.5,
      "sidelobe_level_db": -17.0
    },
    {
      "beam_id": 3,
      "description": "Left narrow beam",
      "azimuth_deg": -15,
      "elevation_deg": 0,
      "phases_deg": [270, 250, 170, 90],
      "gains_db": [0, 0, 0, 0],
      "expected_gain_db": 12.8,
      "sidelobe_level_db": -18.0
    },
    {
      "beam_id": 4,
      "description": "Boresight beam",
      "azimuth_deg": 0,
      "elevation_deg": 0,
      "phases_deg": [0, 0, 0, 0],
      "gains_db": [0, 0, 0, 0],
      "expected_gain_db": 13.0,
      "sidelobe_level_db": -20.0
    },
    {
      "beam_id": 5,
      "description": "Right narrow beam",
      "azimuth_deg": 15,
      "elevation_deg": 0,
      "phases_deg": [90, 110, 190, 270],
      "gains_db": [0, 0, 0, 0],
      "expected_gain_db": 12.8,
      "sidelobe_level_db": -18.0
    },
    {
      "beam_id": 6,
      "description": "Right quarter beam",
      "azimuth_deg": 25,
      "elevation_deg": 0,
      "phases_deg": [75, 125, 205, 285],
      "gains_db": [0, 0, 0, 0],
      "expected_gain_db": 12.5,
      "sidelobe_level_db": -17.0
    },
    {
      "beam_id": 7,
      "description": "Right mid beam",
      "azimuth_deg": 35,
      "elevation_deg": 0,
      "phases_deg": [60, 140, 220, 300],
      "gains_db": [0, 0, 0, 0],
      "expected_gain_db": 12.2,
      "sidelobe_level_db": -16.0
    },
    {
      "beam_id": 8,
      "description": "Right edge beam",
      "azimuth_deg": 45,
      "elevation_deg": 0,
      "phases_deg": [45, 155, 235, 315],
      "gains_db": [0, 0, 0, 0],
      "expected_gain_db": 12.0,
      "sidelobe_level_db": -15.0
    }
  ]
}
```

---

## 9) 風險矩陣與緩解策略

| 風險項目 | 機率 | 影響度 | 風險等級 | 緩解策略 | 備用方案 |
|----------|------|--------|----------|----------|----------|
| **28 GHz鏈路損耗過大** | 中 | 高 | 🔴高 | 增加PA功率、優化天線增益 | 降低距離需求至5m |
| **BBox beam切換延遲** | 高 | 中 | 🟡中 | Pre-loading next beam | 降低掃描速率至50Hz |
| **GNU Radio即時處理** | 中 | 中 | 🟡中 | 使用RFNoC卸載 | 降低FFT點數至1024 |
| **TDM切換同步精度** | 低 | 高 | 🟡中 | 精確時戳校準 | 增加guard time至100μs |
| **溫度漂移** | 中 | 中 | 🟡中 | 主動溫控與補償 | 週期性校準 |
| **記憶體洩漏** | 中 | 低 | 🟢低 | 循環緩衝區設計 | 定期重啟服務 |
| **法規功率限制** | 低 | 中 | 🟢低 | 預先法規諮詢 | 降低EIRP至法規範圍 |

### 緩解策略詳細說明

#### 🔴 高風險：28 GHz鏈路損耗
```python
# 鏈路預算監控與動態調整
class LinkBudgetMonitor:
    def __init__(self):
        self.min_snr_db = 15  # 最低SNR需求
        self.rssi_history = deque(maxlen=100)
        
    def monitor_link_quality(self, rssi, evm):
        self.rssi_history.append(rssi)
        avg_rssi = np.mean(self.rssi_history)
        
        if avg_rssi < -80:  # dBm
            self.increase_tx_power(2)  # +2dB
            self.select_best_beam()
        elif evm > 8:  # %
            self.reduce_modulation_order()  # QAM16→QPSK
        
    def fallback_to_short_range(self):
        # 緊急方案：切換至近距離模式
        self.set_target_range(5)  # 5m instead of 10m
        self.increase_tx_power(6)  # +6dB boost
```

#### 🟡 中風險：Beam切換延遲
```python
# 預載波束控制
class BeamPreloader:
    def __init__(self):
        self.next_beam_ready = False
        self.beam_queue = deque(maxlen=3)
        
    def preload_next_beam(self, beam_id):
        # 在當前dwell期間預先計算下個beam參數
        next_phases = self.calculate_beam_phases(beam_id)
        self.bbox_api.prepare_beam(beam_id, next_phases)
        self.next_beam_ready = True
        
    def fast_beam_switch(self):
        if self.next_beam_ready:
            self.bbox_api.apply_prepared_beam()  # <10μs
            return True
        else:
            self.bbox_api.set_beam_immediate()   # ~30μs fallback
            return False
```

---

## 10) 法規與標準相容性

### 10.1 頻譜法規檢查表

#### 台灣NCC
- [ ] **頻段許可**: 27.5-28.35 GHz (5G NR n257/n261)
- [ ] **功率限制**: EIRP ≤ 40 dBm (實驗室使用)
- [ ] **頻譜遮罩**: 符合3GPP TS 38.104 ACLR要求
- [ ] **實驗許可**: 申請研發實驗執照

#### 美國FCC  
- [ ] **頻段許可**: 27.5-28.35 GHz (Part 15/Part 97)
- [ ] **功率限制**: EIRP ≤ 40 dBm (unlicensed)
- [ ] **DFS需求**: 雷達共存機制（如適用）

#### 歐盟ETSI
- [ ] **頻段許可**: 27.5-29.5 GHz (ECC Report 32)
- [ ] **功率限制**: EIRP ≤ 40 dBm
- [ ] **TPC需求**: 功率控制機制
- [ ] **LBT需求**: Listen-Before-Talk（如適用）

### 10.2 標準相容性

#### 3GPP 5G NR相容性
```yaml
# 5G NR參數對照
nr_compliance:
  frequency_bands: ["n257", "n261"]  # 28 GHz bands
  scs_hz: 15000                      # 符合NR numerology
  cp_type: "normal"                  # Normal CP
  frame_structure: "custom_tdm"      # 非標準TDM結構
  modulation: ["QPSK", "16QAM"]      # 支援NR調變
  mimo: "1x1"                       # SISO，可擴展
```

#### IEEE 802.11ad/ay相容性  
```yaml
# WiGig相容性檢查
wigig_compliance:
  frequency_ghz: 28.0                # 非標準頻段
  bandwidth_mhz: 20                  # 部分相容（標準為2.16GHz）
  modulation: "OFDM"                 # 相容
  beamforming: "analog"              # 相容
```

### 10.3 EMC/EMI測試需求
- [ ] **輻射發射**: EN 55022 Class A
- [ ] **傳導發射**: EN 55022 Class A  
- [ ] **輻射抗擾**: EN 55024
- [ ] **諧波失真**: IEC 61000-3-2
- [ ] **電壓閃爍**: IEC 61000-3-3

---

## 總結與下一步

### 增強版藍圖補充重點
1. ✅ **詳細RF校準流程** - LO洩漏、I/Q平衡、群延遲校正
2. ✅ **精確TDM時序設計** - 50μs切換預算，硬體響應時間
3. ✅ **完整同步校準** - 三階段校準與健康度監控
4. ✅ **系統整合策略** - 功率預算、溫度管理、記憶體優化
5. ✅ **段階性測試計畫** - 8週完整驗證流程
6. ✅ **風險緩解矩陣** - 主要風險點與具體對策
7. ✅ **法規相容性** - 多國法規與標準檢查清單

### 建議實作優先順序
1. **Week 1-2**: RF基礎驗證（最高風險項目）
2. **Week 3-4**: OFDM通訊建立（核心功能）
3. **Week 5-6**: 雷達功能開發（差異化功能）  
4. **Week 7-8**: TDM-ISAC整合（系統整合）

### 關鍵成功因子
- 🎯 **28 GHz鏈路預算充足** - 決定系統可行性
- ⏱️ **TDM切換時間<50μs** - 決定beam掃描速度
- 💻 **GNU Radio即時處理** - 決定系統穩定性
- 📋 **完整測試驗證** - 決定demo成功率

這個增強版藍圖現在應該涵蓋了原始藍圖的所有缺失，你認為還有哪些部分需要進一步細化？
