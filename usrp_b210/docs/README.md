# USRP B210 Beam-Forming ISAC 系統

## 專案簡介

本專案旨在開發基於USRP B210的28GHz ISAC（Integrated Sensing and Communications）系統，結合指向性天線陣列和beam forming技術，實現雷達感測與無線通訊的整合。

## 系統架構

```
USRP B210 (2GHz IF) → Up/Down Converter → 28GHz RF → Beam Former → 指向性天線陣列
```

### 硬體組成
- **USRP B210**: 2x2 MIMO, 70MHz-6GHz, 56Msps
- **Up/Down Converter**: 2GHz ↔ 28GHz頻率轉換
- **Beam Former**: TX/RX獨立控制
- **天線陣列**: 指向性天線，支援掃描與非掃描模式

### 軟體架構
- **開發環境**: Python 3.8+, GNU Radio 3.10+
- **核心演算法**: Beam-Aware ISAC
- **信號處理**: Chirp調變，角度-距離聯合估測
- **Beam控制**: 整合現有API

## 核心功能

### 1. 雷達感測
- **全方位掃描**: ±45度範圍掃描
- **距離測量**: 基於Chirp信號的脈衝壓縮
- **角度估測**: 利用beam forming的空間解析度
- **目標檢測**: 2D CFAR檢測演算法

### 2. 無線通訊
- **定向通訊**: 對準特定方向的資料傳輸
- **Chirp編碼**: 將資料編碼到Chirp參數中
- **多用戶支援**: 時分或頻分複用
- **自適應調變**: 根據通道狀況調整

### 3. ISAC整合
- **時分複用**: 雷達70% + 通訊30%
- **混合模式**: 同時進行感測與通訊
- **自適應策略**: 根據環境動態調整
- **效能優化**: 即時處理與資源管理

### 4. 生命體徵檢測 (未來擴展)
- **非接觸式監測**: 呼吸、心跳檢測
- **微都卜勒技術**: 微小振動感知
- **醫療應用**: 健康監護、睡眠監測
- **研究價值**: 學術研究與原型驗證

## 技術特點

### 演算法優勢
- **Beam-Aware**: 充分利用指向性天線特性
- **空間處理**: 角度-距離聯合估測
- **自適應**: 動態掃描策略與干擾迴避
- **即時性**: 優化的信號處理流程

### 系統優勢
- **高解析度**: 28GHz提供優異的距離與角度解析度
- **低干擾**: 指向性天線天然抑制干擾
- **高效率**: 整合感測與通訊，提升頻譜效率
- **可擴展**: 模組化設計，易於功能擴展

## 開發計畫

### 階段1: 基礎架構 (週1-2)
- [x] 專案規劃與演算法設計
- [ ] 硬體整合與測試
- [ ] 基礎Chirp ISAC系統
- [ ] 基本配置檔案

### 階段2: Beam-Aware ISAC (週3-4)
- [ ] Beam API整合
- [ ] 角度-距離聯合估測
- [ ] 自適應掃描策略
- [ ] 完整ISAC系統

### 階段3: 進階功能 (週5-6)
- [ ] 效能優化
- [ ] 多目標追蹤
- [ ] 干擾迴避
- [ ] 系統整合測試

### 階段4: 生命體徵檢測 (週7-8) - 未來擴展
- [ ] 微都卜勒信號處理
- [ ] 呼吸心跳檢測
- [ ] 醫療級精度驗證
- [ ] 臨床應用測試

## 檔案結構

```
usrp_b210/
├── README.md                 # 專案說明
├── development_plan.md       # 詳細開發計畫
├── algorithm_design.md       # 完整演算法設計
├── algorithm_summary.md      # 演算法摘要
├── config_parameters.py      # 系統參數配置 (待建立)
├── chirp_isac_block.py      # 自定義GNU Radio block (待建立)
├── beam_control.py          # Beam控制介面 (待建立)
├── signal_processing.py     # 信號處理模組 (待建立)
└── test_scripts/            # 測試腳本 (待建立)
```

## 快速開始

### 環境需求
```bash
# Python環境
Python 3.8+
NumPy, SciPy
GNU Radio 3.10+

# 硬體驅動
UHD 4.8+
USRP B210驅動程式
```

### 安裝步驟
```bash
# 1. 克隆專案
git clone <repository_url>
cd usrp_b210

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 硬體測試
python test_hardware.py

# 4. 運行基礎系統
python run_basic_isac.py
```

### 基本使用
```python
from beam_aware_isac import BeamAwareISAC

# 建立ISAC系統
isac = BeamAwareISAC()

# 雷達掃描模式
targets = isac.radar_scan_mode()

# 通訊模式
isac.communication_mode(target_angle=30, data_bits=[1,0,1,1])

# 混合模式
isac.hybrid_mode()
```

## 性能指標

### 雷達性能
- **距離解析度**: ≤10cm (28GHz, 20MHz頻寬)
- **角度解析度**: 由beam former決定
- **檢測範圍**: ≥100m
- **更新率**: ≥10 FPS

### 通訊性能
- **資料率**: ≥1 Mbps
- **誤碼率**: ≤1e-6
- **延遲**: ≤10ms
- **可靠性**: ≥99.9%

### 系統性能
- **即時性**: 處理延遲 ≤100ms
- **穩定性**: 連續運行 ≥24小時
- **資源使用**: CPU <80%, 記憶體 <2GB

## 技術文檔

- [開發計畫](development_plan.md) - 詳細的開發時程與任務
- [演算法設計](algorithm_design.md) - 完整的演算法實作細節
- [演算法摘要](algorithm_summary.md) - 核心演算法快速參考

## 貢獻指南

### 開發流程
1. Fork專案
2. 建立功能分支
3. 實作功能
4. 撰寫測試
5. 提交Pull Request

### 程式碼規範
- 遵循PEP 8 Python風格指南
- 撰寫詳細的docstring
- 包含單元測試
- 更新相關文檔

## 授權

本專案採用MIT授權條款，詳見LICENSE檔案。

## 聯絡資訊

- **專案維護者**: TMYTEK ISAC Lab
- **技術支援**: 請提交Issue或Pull Request
- **合作洽詢**: 請透過專案頁面聯絡

---

*最後更新: 2024年8月*
