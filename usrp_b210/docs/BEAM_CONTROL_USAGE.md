# Beam Control 模組使用說明

## 📖 概述

Beam Control模組是USRP B210 ISAC系統的核心組件，負責控制TMYTEK Beamformer設備，實現精確的波束控制和功率測量。本模組整合了智能日誌管理系統，防止日誌過度增長影響系統性能。

## 🏗️ 架構設計

```
ISACBeamInterface (主要介面)
├── SmartLogHandler (智能日誌管理)
├── BeamDeviceManager (設備管理)
└── BeamControlConfig (配置管理)
```

## 🚀 快速開始

### **基本導入**
```python
from scripts.beam_control import create_isac_beam_interface, BeamControlConfig
```

### **創建介面**
```python
# 使用預設配置
interface = create_isac_beam_interface()

# 或自定義配置
config = BeamControlConfig()
config.target_freq = 28.0  # GHz
config.scan_range = (-30, 30)  # 掃描範圍
interface = create_isac_beam_interface(config)
```

### **初始化系統**
```python
if interface.initialize():
    print("✅ 系統初始化成功")
else:
    print("❌ 系統初始化失敗")
```

## 📋 核心功能

### **1. 波束模式控制**

#### **設置TX/RX模式**
```python
# 設置為發射模式
if interface.set_bbox_mode("TX"):
    print("✅ 已設置為發射模式")

# 設置為接收模式
if interface.set_bbox_mode("RX"):
    print("✅ 已設置為接收模式")
```

#### **波束角度控制**
```python
# 設定波束指向特定角度
# theta: 水平角度 (-45° 到 +45°)
# phi: 垂直角度 (0° 或 180°)
if interface.set_beam_angle(theta=15, phi=0):
    print("✅ 波束角度設置成功")
```

### **2. 功率測量**

```python
# 測量特定角度的功率
power = interface.measure_power(theta=0, phi=0)
if power is not None:
    print(f"📊 功率測量結果: {power} dBm")
else:
    print("⚠️ 功率測量失敗")
```

### **3. 系統狀態查詢**

```python
# 獲取完整系統狀態
status = interface.get_status()
print(f"📊 系統狀態: {status}")

# 檢查特定設備可用性
if status['bbox_available']:
    print("✅ BBox設備可用")
if status['pd_available']:
    print("✅ Power Detector可用")
```

## 🔧 進階使用

### **自定義配置**

```python
from scripts.beam_control import BeamControlConfig

# 創建自定義配置
config = BeamControlConfig()

# 基本參數
config.target_freq = 28.0  # 目標頻率 (GHz)
config.scan_range = (-60, 60)  # 掃描範圍 (度)
config.default_gain = 20.0  # 預設增益

# 日誌配置
config.log_dir = "custom_logs"  # 日誌目錄
config.max_log_size = 20 * 1024 * 1024  # 20MB
config.max_log_files = 10  # 最多10個日誌檔案

# 安全參數
config.max_retries = 5  # 最大重試次數
config.retry_delay = 0.02  # 重試延遲 (秒)
config.operation_timeout = 10.0  # 操作超時 (秒)

# 使用自定義配置創建介面
interface = create_isac_beam_interface(config)
```

### **批量操作**

```python
def scan_multiple_angles(interface, theta_range, phi_values):
    """掃描多個角度的功率"""
    results = {}
    
    for theta in theta_range:
        for phi in phi_values:
            power = interface.measure_power(theta, phi)
            if power is not None:
                results[(theta, phi)] = power
                print(f"θ={theta}°, φ={phi}°: {power} dBm")
            else:
                print(f"θ={theta}°, φ={phi}°: 測量失敗")
    
    return results

# 使用範例
theta_range = range(-30, 31, 5)  # -30° 到 +30°，步長5°
phi_values = [0, 180]  # 0° 和 180°
power_map = scan_multiple_angles(interface, theta_range, phi_values)
```

### **錯誤處理**

```python
import time

def robust_beam_control(interface, theta, phi, max_retries=3):
    """穩健的波束控制，包含重試機制"""
    
    for attempt in range(max_retries):
        try:
            if interface.set_beam_angle(theta, phi):
                print(f"✅ 波束角度設置成功: θ={theta}°, φ={phi}°")
                return True
            else:
                print(f"⚠️ 第{attempt+1}次嘗試失敗")
                
        except Exception as e:
            print(f"💥 第{attempt+1}次嘗試發生錯誤: {e}")
        
        if attempt < max_retries - 1:
            print(f"⏳ 等待重試... ({attempt+1}/{max_retries})")
            time.sleep(1)  # 等待1秒後重試
    
    print(f"❌ 波束角度設置失敗，已重試{max_retries}次")
    return False

# 使用範例
success = robust_beam_control(interface, 20, 0, max_retries=5)
```

## 🔒 安全功能

### **緊急停止**
```python
# 緊急停止 - 將波束設為安全角度 (0°, 0°)
if interface.emergency_stop():
    print("🛑 緊急停止執行成功")
else:
    print("❌ 緊急停止執行失敗")
```

### **資源清理**
```python
# 清理所有資源
interface.cleanup()
print("🧹 資源清理完成")
```

## 📊 日誌管理

### **日誌配置**
- **自動輪轉**: 單個檔案最大10MB
- **檔案限制**: 最多保留5個日誌檔案
- **自動清理**: 防止日誌過度增長
- **分級日誌**: 不同模組的日誌分類

### **日誌查看**
```bash
# 查看當前日誌
tail -f logs/beam_control.log

# 查看日誌檔案大小
ls -lh logs/

# 清理舊日誌
python -c "from scripts.beam_control import SmartLogHandler; SmartLogHandler().cleanup_old_logs()"
```

## 🧪 測試範例

### **基本功能測試**
```python
from scripts.beam_control import test_beam_control

# 執行內建測試
test_beam_control()
```

### **自定義測試**
```python
def custom_test():
    """自定義測試函數"""
    interface = create_isac_beam_interface()
    
    try:
        # 初始化測試
        print("🧪 開始初始化測試...")
        if not interface.initialize():
            print("❌ 初始化測試失敗")
            return False
        
        # 模式切換測試
        print("🧪 開始模式切換測試...")
        for mode in ["TX", "RX"]:
            if interface.set_bbox_mode(mode):
                print(f"✅ {mode}模式測試通過")
            else:
                print(f"❌ {mode}模式測試失敗")
                return False
        
        # 角度控制測試
        print("🧪 開始角度控制測試...")
        test_angles = [(0, 0), (15, 0), (-15, 0), (0, 180)]
        for theta, phi in test_angles:
            if interface.set_beam_angle(theta, phi):
                print(f"✅ 角度({theta}, {phi})測試通過")
            else:
                print(f"❌ 角度({theta}, {phi})測試失敗")
                return False
        
        print("🎉 所有測試通過！")
        return True
        
    except Exception as e:
        print(f"💥 測試過程中發生錯誤: {e}")
        return False
        
    finally:
        interface.cleanup()

# 執行自定義測試
if custom_test():
    print("✅ 自定義測試完成")
else:
    print("❌ 自定義測試失敗")
```

## 🚨 常見問題

### **Q1: 初始化失敗怎麼辦？**
**A**: 檢查以下項目：
1. TMYTEK設備是否正確連接
2. TLKCoreService是否正常運行
3. 設備驅動是否正確安裝
4. 權限是否足夠

### **Q2: 波束角度設置失敗？**
**A**: 檢查以下項目：
1. 角度是否在支援範圍內
2. 設備是否已初始化
3. 當前模式是否正確
4. 硬體連接是否穩定

### **Q3: 功率測量異常？**
**A**: 檢查以下項目：
1. Power Detector是否可用
2. 波束角度是否正確設置
3. 頻率設定是否正確
4. 校準檔案是否載入

### **Q4: 日誌檔案過大？**
**A**: 系統會自動管理日誌：
1. 單個檔案超過10MB會自動輪轉
2. 最多保留5個日誌檔案
3. 舊檔案會自動清理
4. 可手動調用`cleanup_old_logs()`

## 📞 技術支援

### **錯誤報告**
當遇到問題時，請提供：
1. 錯誤訊息和堆疊追蹤
2. 系統環境資訊
3. 設備連接狀態
4. 相關日誌檔案

### **聯繫方式**
- **專案維護者**: TMYTEK ISAC Lab
- **文檔版本**: v1.0
- **最後更新**: 2024年

---

## 📝 更新日誌

- **v1.0** (2024): 初始版本，包含基本波束控制功能
- 智能日誌管理系統
- 完整的設備管理
- 安全機制和錯誤處理
- 豐富的使用範例
