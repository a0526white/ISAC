# GNU Radio 整合說明

## 🎯 **整合架構**

```
GNU Radio Flowgraph
    ↓
ChirpISACBlock (自定義Python Block)
    ↓
Beam Control API (gnuradio_beam_control.py)
    ↓
TMYTEK Hardware (BBox, Power Detector)
```

## 🚀 **快速整合**

### **1. 在GNU Radio中使用**

#### **方法A: 直接導入Python Block**
```python
# 在GNU Radio Companion中創建Python Block
# 在Block的Python代碼中導入：

import sys
import os
sys.path.append('/path/to/usrp_b210/scripts')

from gnuradio_beam_control import create_beam_control_block

class ChirpISACWithBeam(gr.sync_block):
    def __init__(self):
        gr.sync_block.__init__(self,
            name="ChirpISACWithBeam",
            in_sig=[np.complex64],
            out_sig=[np.complex64])
        
        # 創建Beam控制器
        self.beam_controller = create_beam_control_block()
        
        # 初始化
        if not self.beam_controller.initialize():
            print("⚠️ Beam控制器初始化失敗")
    
    def work(self, input_items, output_items):
        # 在這裡實現ISAC邏輯
        # 可以調用beam_controller的方法
        
        # 例如：設置雷達模式
        if self.beam_controller.set_radar_mode():
            # 開始掃描
            self.beam_controller.start_scan(step=5)
        
        # 處理信號...
        output_items[0][:] = input_items[0]
        return len(output_items[0])
    
    def stop(self):
        # 清理資源
        if self.beam_controller:
            self.beam_controller.cleanup()
        return True
```

#### **方法B: 使用預製的Beam Control Block**
```python
# 創建專門的Beam Control Block
class BeamControlBlock(gr.sync_block):
    def __init__(self, scan_enabled=True, scan_step=5):
        gr.sync_block.__init__(self,
            name="BeamControlBlock",
            in_sig=[],
            out_sig=[])
        
        self.beam_controller = create_beam_control_block()
        self.scan_enabled = scan_enabled
        self.scan_step = scan_step
        
        # 初始化
        self.beam_controller.initialize()
        
        # 如果啟用掃描，開始掃描
        if self.scan_enabled:
            self.beam_controller.start_scan(step=scan_step)
    
    def work(self, input_items, output_items):
        # 這個Block主要用於控制，不需要處理信號
        return 0
    
    def stop(self):
        if self.beam_controller:
            self.beam_controller.cleanup()
        return True
```

### **2. 在Flowgraph中的使用方式**

#### **基本設置**
1. **添加Python Block**: 在GNU Radio Companion中添加Python Block
2. **導入路徑**: 確保Python能找到我們的腳本路徑
3. **初始化**: 在Block的`__init__`中初始化Beam控制器
4. **清理**: 在`stop`方法中清理資源

#### **實時控制**
```python
# 在work方法中實時控制波束
def work(self, input_items, output_items):
    # 根據信號強度調整波束方向
    signal_strength = np.mean(np.abs(input_items[0]))
    
    if signal_strength > threshold:
        # 信號強，指向當前方向
        current_angle = self.get_current_angle()
        self.beam_controller.point_to_angle(current_angle)
    else:
        # 信號弱，開始掃描
        if not self.beam_controller.get_status()['scan_enabled']:
            self.beam_controller.start_scan(step=10)
    
    # 處理信號...
    return len(output_items[0])
```

## 🔧 **配置選項**

### **掃描參數**
```python
# 掃描範圍：左右各45度
scan_range = (-45, 45)

# 掃描步長：5度（可調整）
scan_step = 5

# 掃描速度：每個角度停留時間
scan_delay = 0.1  # 秒
```

### **模式切換**
```python
# 雷達模式 (TX)
self.beam_controller.set_radar_mode()

# 通訊模式 (RX)
self.beam_controller.set_communication_mode()

# 手動指向
self.beam_controller.point_to_angle(theta=15)
```

## 📊 **使用範例**

### **範例1: 簡單的ISAC Block**
```python
class SimpleISACBlock(gr.sync_block):
    def __init__(self):
        gr.sync_block.__init__(self,
            name="SimpleISAC",
            in_sig=[np.complex64],
            out_sig=[np.complex64])
        
        # 初始化Beam控制器
        self.beam_controller = create_beam_control_block()
        self.beam_controller.initialize()
        
        # 設置為雷達模式
        self.beam_controller.set_radar_mode()
        
        # 開始掃描
        self.beam_controller.start_scan(step=5)
    
    def work(self, input_items, output_items):
        # 簡單的信號處理
        output_items[0][:] = input_items[0]
        return len(output_items[0])
    
    def stop(self):
        self.beam_controller.cleanup()
        return True
```

### **範例2: 自適應波束控制**
```python
class AdaptiveBeamISAC(gr.sync_block):
    def __init__(self):
        gr.sync_block.__init__(self,
            name="AdaptiveBeamISAC",
            in_sig=[np.complex64],
            out_sig=[np.complex64])
        
        self.beam_controller = create_beam_control_block()
        self.beam_controller.initialize()
        
        # 掃描參數
        self.scan_step = 5
        self.signal_threshold = 0.1
        self.last_strong_angle = 0
        
    def work(self, input_items, output_items):
        # 分析信號強度
        signal = input_items[0]
        signal_strength = np.mean(np.abs(signal))
        
        # 根據信號強度調整策略
        if signal_strength > self.signal_threshold:
            # 信號強，停止掃描，指向當前方向
            if self.beam_controller.get_status()['scan_enabled']:
                self.beam_controller.stop_scan()
            
            # 計算最佳角度（這裡簡化處理）
            best_angle = self.calculate_best_angle(signal)
            self.beam_controller.point_to_angle(best_angle)
            self.last_strong_angle = best_angle
            
        else:
            # 信號弱，開始掃描
            if not self.beam_controller.get_status()['scan_enabled']:
                self.beam_controller.start_scan(step=self.scan_step)
        
        # 輸出信號
        output_items[0][:] = signal
        return len(output_items[0])
    
    def calculate_best_angle(self, signal):
        # 這裡實現角度計算邏輯
        # 簡化版本：返回最後一個強信號的角度
        return self.last_strong_angle
    
    def stop(self):
        self.beam_controller.cleanup()
        return True
```

## 🚨 **注意事項**

### **1. 路徑設置**
```python
# 確保Python能找到我們的腳本
import sys
sys.path.append('/absolute/path/to/usrp_b210/scripts')

# 或者設置環境變數
os.environ['PYTHONPATH'] = '/path/to/usrp_b210/scripts'
```

### **2. 資源管理**
- 在Block的`stop`方法中調用`cleanup()`
- 使用`try-finally`確保資源被正確釋放
- 避免在`work`方法中進行耗時操作

### **3. 實時性考慮**
- 波束控制操作應該快速完成
- 避免在`work`方法中進行複雜計算
- 使用線程進行掃描操作

### **4. 錯誤處理**
```python
def work(self, input_items, output_items):
    try:
        # 檢查Beam控制器狀態
        status = self.beam_controller.get_status()
        if not status['initialized']:
            print("⚠️ Beam控制器未初始化")
            return 0
        
        # 處理信號...
        
    except Exception as e:
        print(f"💥 處理過程中發生錯誤: {e}")
        return 0
```

## 🔍 **調試技巧**

### **1. 日誌輸出**
```python
# 設置詳細日誌
import logging
logging.basicConfig(level=logging.DEBUG)

# 在Block中添加調試信息
print(f"當前波束角度: {self.beam_controller.get_status()}")
```

### **2. 狀態監控**
```python
def work(self, input_items, output_items):
    # 定期檢查狀態
    if self.counter % 1000 == 0:  # 每1000個樣本檢查一次
        status = self.beam_controller.get_status()
        print(f"Beam狀態: {status}")
    
    self.counter += 1
    # ... 其他處理
```

### **3. 性能監控**
```python
import time

def work(self, input_items, output_items):
    start_time = time.time()
    
    # 處理信號...
    
    processing_time = time.time() - start_time
    if processing_time > 0.001:  # 超過1ms
        print(f"⚠️ 處理時間過長: {processing_time*1000:.2f}ms")
```

## 📝 **總結**

通過這種整合方式，您可以：

1. **在GNU Radio中直接控制波束**
2. **實現實時的ISAC功能**
3. **自動化波束掃描和定位**
4. **根據信號強度自適應調整**

關鍵是將Beam Control API封裝在GNU Radio的Python Block中，這樣既保持了靈活性，又能與GNU Radio的數據流無縫整合。
