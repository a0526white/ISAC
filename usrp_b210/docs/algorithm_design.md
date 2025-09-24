# Beam-Aware ISAC 演算法設計

## 概述
本文檔記錄了USRP B210 ISAC系統的核心演算法設計，包括Beam-Aware ISAC類別、角度-距離聯合估測、自適應掃描策略等關鍵功能。

## 核心演算法架構

### 1. BeamAwareISAC 主類別

```python
class BeamAwareISAC:
    """Beam-Aware ISAC系統主類別"""
    
    def __init__(self):
        # Beam控制
        self.beam_api = BeamControlAPI()  # 現有API
        self.tx_beam_id = 0
        self.rx_beam_id = 0
        
        # 掃描參數
        self.scan_enabled = True
        self.scan_angles = range(-45, 46, 10)  # ±45度，10度間隔
        self.scan_speed = "fast"  # fast/slow/adaptive
        
        # ISAC參數
        self.radar_mode = True
        self.communication_mode = False
        self.hybrid_mode = False
        
        # 信號處理參數
        self.chirp_duration = 100e-6      # 100μs
        self.bandwidth = 20e6             # 20 MHz
        self.start_freq = 2.4e9           # 2.4 GHz IF
        self.sample_rate = 30e6           # 30 Msps
        
        # 雷達參數
        self.range_bins = 1024
        self.doppler_bins = 128
        self.cfar_guard = [2, 2]
        self.cfar_training = [8, 8]
        self.cfar_pfa = 1e-3
```

### 2. 工作模式實作

#### 2.1 雷達掃描模式
```python
def radar_scan_mode(self):
    """雷達掃描模式 - 全方位目標檢測"""
    detection_map = {}
    
    for tx_angle in self.scan_angles:
        for rx_angle in self.scan_angles:
            # 設定beam方向
            self.beam_api.set_tx_beam(tx_angle)
            self.beam_api.set_rx_beam(rx_angle)
            
            # 發射Chirp並接收
            tx_signal = self.generate_chirp()
            rx_signal = self.receive_signal()
            
            # 雷達處理
            range_doppler = self.radar_processing(tx_signal, rx_signal)
            detection_map[(tx_angle, rx_angle)] = range_doppler
            
    return self.extract_targets(detection_map)

def generate_chirp(self):
    """產生線性調頻信號"""
    duration = self.chirp_duration
    start_f = self.start_freq
    stop_f = self.start_freq + self.bandwidth
    
    # 時間軸
    t = np.linspace(0, duration, int(duration * self.sample_rate))
    
    # 調頻斜率
    k = (stop_f - start_f) / duration
    
    # 相位積分
    phase = 2 * np.pi * (start_f * t + 0.5 * k * t**2)
    
    # 複數信號
    signal = np.exp(1j * phase)
    
    return signal

def radar_processing(self, tx_signal, rx_signal):
    """雷達信號處理"""
    # 匹配濾波器
    matched_filter_output = np.correlate(rx_signal, tx_signal, mode='full')
    
    # 距離-都卜勒處理
    range_profile = np.abs(matched_filter_output)
    
    # CFAR檢測
    detections = self.cfar_detection(range_profile)
    
    return {
        'range_profile': range_profile,
        'detections': detections,
        'snr': np.max(range_profile)
    }
```

#### 2.2 通訊模式
```python
def communication_mode(self, target_angle, data_bits):
    """通訊模式 - 對準特定方向傳送資料"""
    # TX/RX beam對準目標
    self.beam_api.set_tx_beam(target_angle)
    self.beam_api.set_rx_beam(target_angle)
    
    # 將資料編碼到Chirp參數中
    encoded_signals = self.encode_data_in_chirp(data_bits)
    
    # 傳送信號
    for signal in encoded_signals:
        self.transmit_signal(signal)
        time.sleep(self.chirp_duration)
    
    return True

def encode_data_in_chirp(self, data_bits):
    """將數據編碼到Chirp參數中"""
    chirp_signals = []
    
    for bit in data_bits:
        if bit == 0:
            # 上行Chirp代表0
            signal = self.generate_chirp(
                self.chirp_duration,
                self.start_freq,
                self.start_freq + self.bandwidth
            )
        else:
            # 下行Chirp代表1  
            signal = self.generate_chirp(
                self.chirp_duration,
                self.start_freq + self.bandwidth,
                self.start_freq
            )
        chirp_signals.append(signal)
    
    return chirp_signals
```

#### 2.3 混合模式
```python
def hybrid_mode(self):
    """混合模式 - 同時雷達與通訊"""
    # 時分複用策略
    frame_duration = 10e-3  # 10ms frame
    radar_slot = 0.7        # 70%時間給雷達
    comms_slot = 0.3        # 30%時間給通訊
    
    while True:
        # 雷達時槽
        radar_start = time.time()
        while time.time() - radar_start < frame_duration * radar_slot:
            self.radar_scan_mode()
        
        # 通訊時槽
        comms_start = time.time()
        while time.time() - comms_start < frame_duration * comms_slot:
            if self.has_communication_data():
                target_angle = self.get_target_angle()
                data = self.get_communication_data()
                self.communication_mode(target_angle, data)
```

### 3. 角度-距離聯合估測

#### 3.1 聯合估測演算法
```python
def joint_angle_range_estimation(self, rx_data):
    """利用beam掃描進行角度-距離聯合估測"""
    
    # 建立角度-距離圖
    angle_range_map = np.zeros((len(self.scan_angles), self.range_bins))
    
    for i, angle in enumerate(self.scan_angles):
        # 該角度的距離profile
        range_profile = self.matched_filter(rx_data[angle])
        angle_range_map[i, :] = np.abs(range_profile)
    
    # 峰值檢測
    peaks = self.cfar_detection_2d(angle_range_map)
    
    # 目標參數估測
    targets = []
    for peak in peaks:
        target = {
            'angle': self.scan_angles[peak[0]],
            'range': peak[1] * self.range_resolution,
            'snr': angle_range_map[peak[0], peak[1]],
            'confidence': self.calculate_confidence(peak, angle_range_map)
        }
        targets.append(target)
    
    return targets

def cfar_detection_2d(self, data_2d):
    """2D CFAR檢測"""
    guard_cells = self.cfar_guard
    training_cells = self.cfar_training
    pfa = self.cfar_pfa
    
    rows, cols = data_2d.shape
    detections = []
    
    for i in range(guard_cells[0], rows - guard_cells[0]):
        for j in range(guard_cells[1], cols - guard_cells[1]):
            # 保護區域
            guard_region = data_2d[
                i-guard_cells[0]:i+guard_cells[0]+1,
                j-guard_cells[1]:j+guard_cells[1]+1
            ]
            
            # 訓練區域
            training_region = []
            for r in range(i-training_cells[0], i+training_cells[0]+1):
                for c in range(j-training_cells[1], j+training_cells[1]+1):
                    if (r < 0 or r >= rows or c < 0 or c >= cols or
                        (r >= i-guard_cells[0] and r <= i+guard_cells[0] and
                         c >= j-guard_cells[1] and c <= j+guard_cells[1])):
                        continue
                    training_region.append(data_2d[r, c])
            
            # CFAR檢測
            if len(training_region) > 0:
                threshold = np.mean(training_region) * self.calculate_cfar_threshold(pfa)
                if data_2d[i, j] > threshold:
                    detections.append((i, j))
    
    return detections
```

#### 3.2 角度解析度計算
```python
def calculate_angle_resolution(self):
    """計算角度解析度"""
    # 基於beam former陣列參數
    wavelength = 3e8 / (28e9)  # 28GHz波長
    array_spacing = 0.5 * wavelength  # 半波長間距
    array_elements = 8  # 假設8元素陣列
    
    # 角度解析度 (rad)
    angle_resolution = wavelength / (array_elements * array_spacing)
    
    # 轉換為度
    angle_resolution_deg = np.degrees(angle_resolution)
    
    return angle_resolution_deg

def calculate_range_resolution(self):
    """計算距離解析度"""
    # 基於Chirp頻寬
    range_resolution = 3e8 / (2 * self.bandwidth)
    return range_resolution
```

### 4. 自適應掃描策略

#### 4.1 自適應掃描
```python
def adaptive_scan_strategy(self, previous_detections):
    """根據歷史檢測結果調整掃描策略"""
    
    if not previous_detections:
        # 初始掃描：全範圍
        return self.full_sector_scan()
    
    # 有目標歷史：重點掃描
    priority_angles = []
    for target in previous_detections:
        # 預測目標可能位置
        predicted_angle = self.predict_target_angle(target)
        priority_angles.append(predicted_angle)
    
    # 分配掃描時間
    scan_schedule = {
        'priority_scan': priority_angles,     # 70%時間
        'surveillance_scan': self.scan_angles, # 30%時間
    }
    
    return scan_schedule

def predict_target_angle(self, target):
    """預測目標角度變化"""
    if len(target['history']) < 2:
        return target['current_angle']
    
    # 簡單線性預測
    angles = [h['angle'] for h in target['history']]
    times = [h['timestamp'] for h in target['history']]
    
    # 線性回歸
    slope = np.polyfit(times, angles, 1)[0]
    
    # 預測下一時刻角度
    current_time = time.time()
    time_diff = current_time - times[-1]
    predicted_angle = angles[-1] + slope * time_diff
    
    return predicted_angle

def full_sector_scan(self):
    """全範圍掃描"""
    return {
        'scan_pattern': 'sector',
        'angles': self.scan_angles,
        'dwell_time': 100e-3,  # 100ms per beam
        'total_time': len(self.scan_angles) * 100e-3
    }
```

#### 4.2 掃描模式優化
```python
def optimize_scan_pattern(self, targets, interference_sources):
    """優化掃描模式以避開干擾"""
    
    # 識別干擾源
    interference_angles = [src['angle'] for src in interference_sources]
    
    # 調整掃描角度避開干擾
    optimized_angles = []
    for angle in self.scan_angles:
        # 檢查是否接近干擾源
        min_interference_distance = 10  # 度
        is_interference_free = True
        
        for int_angle in interference_angles:
            if abs(angle - int_angle) < min_interference_distance:
                is_interference_free = False
                break
        
        if is_interference_free:
            optimized_angles.append(angle)
    
    # 根據目標密度調整掃描密度
    if len(targets) > 0:
        # 高目標密度：細緻掃描
        scan_density = 'high'
        dwell_time = 50e-3  # 50ms
    else:
        # 低目標密度：粗略掃描
        scan_density = 'low'
        dwell_time = 200e-3  # 200ms
    
    return {
        'angles': optimized_angles,
        'dwell_time': dwell_time,
        'density': scan_density
    }
```

### 5. 信號處理優化

#### 5.1 匹配濾波器優化
```python
def optimized_matched_filter(self, rx_signal, tx_template):
    """優化的匹配濾波器"""
    
    # 使用FFT加速相關運算
    rx_fft = np.fft.fft(rx_signal)
    tx_fft = np.fft.fft(tx_template, len(rx_signal))
    
    # 頻域相乘
    correlation_fft = rx_fft * np.conj(tx_fft)
    
    # 反FFT得到相關結果
    correlation = np.fft.ifft(correlation_fft)
    
    return correlation

def range_doppler_processing(self, rx_data, tx_template):
    """距離-都卜勒處理"""
    
    # 脈衝壓縮
    compressed_data = self.optimized_matched_filter(rx_data, tx_template)
    
    # 都卜勒處理
    doppler_data = np.fft.fft(compressed_data, axis=1)
    
    # 距離-都卜勒圖
    range_doppler_map = np.abs(doppler_data)
    
    return range_doppler_map
```

#### 5.2 即時處理優化
```python
def real_time_processing_optimization(self):
    """即時處理優化策略"""
    
    # 1. 資料流緩衝
    self.input_buffer = collections.deque(maxlen=1000)
    self.output_buffer = collections.deque(maxlen=1000)
    
    # 2. 多執行緒處理
    self.processing_thread = threading.Thread(target=self.signal_processing_worker)
    self.processing_thread.daemon = True
    self.processing_thread.start()
    
    # 3. 記憶體池
    self.signal_pool = []
    for _ in range(100):
        self.signal_pool.append(np.zeros(self.range_bins, dtype=np.complex64))
    
    # 4. 效能監控
    self.processing_times = []
    self.frame_drops = 0

def signal_processing_worker(self):
    """信號處理工作執行緒"""
    while True:
        if self.input_buffer:
            # 取得輸入資料
            input_data = self.input_buffer.popleft()
            
            # 處理時間測量
            start_time = time.time()
            
            # 信號處理
            output_data = self.process_signal(input_data)
            
            # 記錄處理時間
            processing_time = time.time() - start_time
            self.processing_times.append(processing_time)
            
            # 輸出緩衝
            self.output_buffer.append(output_data)
            
            # 效能檢查
            if processing_time > 0.1:  # 100ms
                self.frame_drops += 1
                print(f"警告：處理時間過長: {processing_time*1000:.1f}ms")
        
        time.sleep(0.001)  # 1ms
```

## 演算法參數配置

### 預設參數
```python
DEFAULT_PARAMETERS = {
    # Chirp參數
    'chirp_duration': 100e-6,      # 100μs
    'bandwidth': 20e6,             # 20 MHz
    'start_freq': 2.4e9,           # 2.4 GHz IF
    
    # 掃描參數
    'scan_angles': range(-45, 46, 10),  # ±45度，10度間隔
    'dwell_time': 100e-3,          # 100ms per beam
    'scan_speed': 'adaptive',      # fast/slow/adaptive
    
    # 雷達參數
    'range_bins': 1024,
    'doppler_bins': 128,
    'cfar_guard': [2, 2],
    'cfar_training': [8, 8],
    'cfar_pfa': 1e-3,
    
    # 通訊參數
    'data_rate': 1e6,              # 1 Mbps
    'modulation': 'chirp_bpsk',    # chirp_bpsk/chirp_qpsk
    'error_correction': 'reed_solomon',
    
    # 效能參數
    'max_processing_time': 0.1,    # 100ms
    'target_fps': 10,              # 10 FPS
    'memory_pool_size': 100
}
```

### 參數調校指南
```python
PARAMETER_TUNING_GUIDE = {
    'chirp_duration': {
        'description': 'Chirp持續時間',
        'range': [50e-6, 500e-6],  # 50μs - 500μs
        'trade_off': '短時間=高距離解析度，長時間=高SNR',
        'recommendation': '100μs for 20MHz bandwidth'
    },
    
    'bandwidth': {
        'description': '掃頻頻寬',
        'range': [10e6, 50e6],     # 10MHz - 50MHz
        'trade_off': '大頻寬=高距離解析度，小頻寬=高SNR',
        'recommendation': '20MHz for 7.5cm range resolution'
    },
    
    'scan_angles': {
        'description': '掃描角度範圍',
        'range': [(-90, 90), (-45, 45), (-30, 30)],
        'trade_off': '大範圍=長掃描時間，小範圍=快速更新',
        'recommendation': '±45度 for general surveillance'
    },
    
    'dwell_time': {
        'description': '每個beam停留時間',
        'range': [50e-3, 500e-3],  # 50ms - 500ms
        'trade_off': '短時間=快速掃描，長時間=高SNR',
        'recommendation': '100ms for balanced performance'
    }
}
```

## 效能評估指標

### 雷達性能
- **距離解析度**: ≤10cm (目標)
- **角度解析度**: 由beam former決定
- **檢測範圍**: ≥100m (目標)
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
- **功耗**: 由硬體決定

## 未來擴展方向

### 短期擴展 (1-3個月)
1. **多目標追蹤**: Kalman濾波器實作
2. **干擾抑制**: 自適應波束成形
3. **移動目標**: 都卜勒處理優化

### 中期擴展 (3-6個月)
1. **機器學習**: 目標分類與識別
2. **協作感知**: 多節點協調
3. **網路優化**: 路由與資源分配

### 長期擴展 (6-12個月)
1. **AI驅動**: 全自動化操作
2. **5G/6G整合**: 標準化介面
3. **商用部署**: 產品化與認證

---

*此演算法設計文件將根據實作進展持續更新*
