# USRP B210 硬體測試指南

## 測試環境
- **作業系統**: Linux
- **UHD版本**: 4.8+
- **GNU Radio**: 3.10+
- **Python**: 3.10.12+

## 測試腳本說明

### 1. 環境檢查腳本
```bash
python test_environment.py
```
**功能**: 檢查系統環境是否滿足要求
- Python版本檢查
- UHD安裝檢查
- GNU Radio安裝檢查
- Python套件檢查
- USRP設備檢測

### 2. 硬體功能測試腳本
```bash
python test_hardware.py
```
**功能**: 測試B210硬體功能
- 設備連接測試
- 基本參數設定
- 信號傳輸測試
- Chirp信號產生
- 信號品質分析
- Loopback能力測試

## 測試流程

### 步驟1: 環境檢查
```bash
# 首先檢查環境
python test_environment.py
```
**預期結果**: 所有檢查項目都通過 ✅

### 步驟2: 硬體測試
```bash
# 環境檢查通過後，執行硬體測試
python test_hardware.py
```
**預期結果**: 所有測試項目都通過 ✅

## 測試項目詳解

### 環境檢查項目
1. **Python版本**: 確保版本 ≥ 3.10
2. **UHD安裝**: 檢查命令列工具和Python綁定
3. **GNU Radio**: 檢查命令列工具和Python綁定
4. **Python套件**: 檢查必要套件（numpy, scipy等）
5. **USRP設備**: 檢測B200/B210設備連接

### 硬體測試項目
1. **設備連接**: 測試B210連接與識別
2. **基本參數**: 測試取樣率、頻率、增益設定
3. **信號傳輸**: 測試簡單正弦波發射
4. **Chirp信號**: 測試線性調頻信號產生
5. **信號品質**: 測試頻譜分析與信號完整性
6. **Loopback**: 測試TX→RX迴路能力

## 故障排除

### 常見問題

#### 1. UHD設備未找到
```bash
# 檢查USB連接
lsusb | grep Ettus

# 檢查UHD驅動
uhd_usrp_probe

# 檢查權限
sudo usermod -a -G usb $USER
```

#### 2. Python套件缺失
```bash
# 安裝必要套件
pip install numpy scipy matplotlib pandas

# 或使用系統套件管理器
sudo apt install python3-numpy python3-scipy python3-matplotlib python3-pandas
```

#### 3. 權限問題
```bash
# 重新登入或重啟
# 或檢查udev規則
sudo nano /etc/udev/rules.d/99-uhd.rules
```

### 測試結果解讀

#### 全部通過 ✅
```
🎉 所有測試通過！B210硬體功能正常
下一步: 可以開始Chirp ISAC系統開發
```

#### 部分通過 ⚠️
```
⚠️  環境基本可用，但建議解決問題後再繼續
下一步: 解決問題後執行 python test_hardware.py
```

#### 多數失敗 ❌
```
❌ 環境問題較多，請先解決基本環境問題
建議: 檢查UHD安裝、設備連接、Python套件
```

## 下一步行動

### 測試通過後
1. **開始階段1開發**: 基礎Chirp ISAC系統
2. **建立配置檔案**: 系統參數管理
3. **開發GNU Radio blocks**: 自定義信號處理

### 測試失敗時
1. **檢查硬體連接**: USB線、電源
2. **驗證軟體安裝**: UHD、GNU Radio
3. **檢查系統權限**: 用戶組、udev規則
4. **重新執行測試**: 解決問題後重試

## 技術支援

### 日誌檔案
測試過程中會產生以下檔案：
- `test_signals/`: 測試信號數據
- 控制台輸出: 詳細測試結果

### 除錯建議
1. 檢查USB連接穩定性
2. 確認B210電源供應
3. 驗證UHD驅動程式版本
4. 檢查Python環境完整性

---

*如有問題，請檢查日誌輸出並參考故障排除指南*
