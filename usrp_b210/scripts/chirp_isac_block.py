#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChirpISAC自定義GNU Radio Block
整合Chirp信號產生、ISAC處理、Beam控制功能
兼容Linux/Windows環境
作者: TMYTEK ISAC Lab
"""

import numpy as np
from pathlib import Path
import json
import threading
import time
from collections import deque

# 在腳本開始時就設置GNU Radio路徑
import sys

# 移除可能存在的舊GNU Radio路徑
gnuradio_paths_to_remove = [p for p in sys.path if 'gnuradio' in p.lower()]
for path in gnuradio_paths_to_remove:
    if path in sys.path:
        sys.path.remove(path)

# 添加正確的GNU Radio路徑
sys.path.insert(0, "/usr/local/lib/python3.10/dist-packages")
sys.path.insert(0, "/usr/lib/python3/dist-packages/gnuradio")

# GNU Radio相關導入 (在Linux環境中會正常工作)
try:
    import gnuradio as gr
    from gnuradio import blocks
    from gnuradio import uhd
    GNURADIO_AVAILABLE = True
    print("GNU Radio模組載入成功")
    print(f"gr模組類型: {type(gr)}")
    print(f"gr模組屬性: {[attr for attr in dir(gr) if not attr.startswith('_')][:10]}")
    
    # 檢查gr.gr模組
    if hasattr(gr, 'gr'):
        print(f"gr.gr模組類型: {type(gr.gr)}")
        print(f"gr.gr模組屬性: {[attr for attr in dir(gr.gr) if not attr.startswith('_')][:10]}")
    
    # 確保gr.gr.sync_block可用
    if not hasattr(gr.gr, 'sync_block'):
        print(f"gr.gr模組完整屬性: {dir(gr.gr)}")
        raise AttributeError("gr.gr.sync_block不可用")
    
    # 確保gr.gr.io_signature可用
    if not hasattr(gr.gr, 'io_signature'):
        raise AttributeError("gr.gr.io_signature不可用")
        
except ImportError as e:
    GNURADIO_AVAILABLE = False
    print(f"GNU Radio模組未找到: {e}")
    print("將在模擬模式下運行")
    
    # 建立模擬的GNU Radio基礎類別
    class MockGRBlock:
        def __init__(self):
            pass
    
    class gr:
        class gr:
            sync_block = MockGRBlock
            io_signature = lambda x, y, z: None

# 導入配置和Chirp產生器
sys_path = Path(__file__).parent.parent
import sys
sys.path.append(str(sys_path / "config"))
sys.path.append(str(sys_path / "scripts"))

try:
    from hardware_verified_config import get_config
    from chirp_generator import ChirpGenerator
    CONFIG = get_config()
except ImportError:
    # 如果無法導入新配置，嘗試舊配置
    try:
        from b210_config import get_config
        from chirp_generator import ChirpGenerator
        CONFIG = get_config()
    except ImportError as e:
        print(f"警告: 無法導入配置模組: {e}")
        CONFIG = None

class ChirpISACSource(gr.gr.sync_block):
    """
    ChirpISAC信號源Block
    產生ISAC Chirp信號並支援多種模式
    """
    
    def __init__(self, 
                 sample_rate=30e6,
                 chirp_duration=100e-6,
                 bandwidth=20e6,
                 mode="radar"):
        """
        初始化ChirpISAC信號源
        
        Parameters:
        -----------
        sample_rate : float
            取樣率 (Hz)
        chirp_duration : float  
            Chirp持續時間 (秒)
        bandwidth : float
            頻寬 (Hz)
        mode : str
            工作模式: "radar", "communication", "hybrid"
        """
        if GNURADIO_AVAILABLE:
            gr.gr.sync_block.__init__(
                self,
                name="ChirpISAC Source",
                in_sig=None,  # 信號源沒有輸入
                out_sig=[np.complex64]  # 輸出複數信號
            )
        
        # 參數設定
        self.sample_rate = sample_rate
        self.chirp_duration = chirp_duration
        self.bandwidth = bandwidth
        self.mode = mode
        
        # 內部狀態
        self.chirp_generator = ChirpGenerator()
        self.current_chirp = None
        self.chirp_index = 0
        self.data_buffer = deque()
        self.running = False
        
        # 模式特定參數
        self.radar_params = self._init_radar_params()
        self.comm_params = self._init_comm_params()
        self.beam_params = self._init_beam_params()
        
        # 統計資訊
        self.stats = {
            'chirps_generated': 0,
            'data_bits_sent': 0,
            'beam_scans': 0,
            'start_time': time.time()
        }
        
        print(f"ChirpISAC Source初始化完成 - 模式: {mode}")
    
    def _init_radar_params(self):
        """初始化雷達參數"""
        return {
            'scan_enabled': True,
            'scan_angles': list(range(-45, 46, 10)),
            'current_angle': 0,
            'dwell_time': 100e-3,
            'cfar_enabled': True
        }
    
    def _init_comm_params(self):
        """初始化通訊參數"""
        return {
            'encoding': 'direction',  # direction, frequency, phase
            'data_rate': 200e3,
            'frame_size': 1024,
            'error_correction': True
        }
    
    def _init_beam_params(self):
        """初始化beam forming參數"""
        return {
            'tx_beam_angle': 0,
            'rx_beam_angle': 0,
            'beam_width': 10,  # 度
            'scan_pattern': 'sector'  # sector, random, adaptive
        }
    
    def set_mode(self, mode):
        """設定工作模式"""
        if mode in ["radar", "communication", "hybrid"]:
            self.mode = mode
            print(f"模式切換至: {mode}")
        else:
            raise ValueError(f"不支援的模式: {mode}")
    
    def add_data_to_send(self, data_bits):
        """添加要傳送的數據"""
        self.data_buffer.extend(data_bits)
        print(f"添加 {len(data_bits)} 位元到傳送緩衝區")
    
    def set_beam_angle(self, tx_angle, rx_angle=None):
        """設定beam角度"""
        self.beam_params['tx_beam_angle'] = tx_angle
        if rx_angle is not None:
            self.beam_params['rx_beam_angle'] = rx_angle
        else:
            self.beam_params['rx_beam_angle'] = tx_angle
        
        print(f"Beam角度設定: TX={tx_angle}°, RX={self.beam_params['rx_beam_angle']}°")
    
    def generate_next_chirp(self):
        """產生下一個Chirp信號"""
        if self.mode == "radar":
            return self._generate_radar_chirp()
        elif self.mode == "communication":
            return self._generate_comm_chirp()
        elif self.mode == "hybrid":
            return self._generate_hybrid_chirp()
        else:
            # 預設線性Chirp
            return self.chirp_generator.generate_linear_chirp(
                duration=self.chirp_duration,
                bandwidth=self.bandwidth,
                sample_rate=self.sample_rate
            )
    
    def _generate_radar_chirp(self):
        """產生雷達用Chirp"""
        # 根據beam掃描調整參數
        if self.radar_params['scan_enabled']:
            angle_idx = self.chirp_index % len(self.radar_params['scan_angles'])
            current_angle = self.radar_params['scan_angles'][angle_idx]
            self.set_beam_angle(current_angle)
        
        # 產生線性Chirp用於雷達
        chirp = self.chirp_generator.generate_linear_chirp(
            duration=self.chirp_duration,
            bandwidth=self.bandwidth,
            sample_rate=self.sample_rate,
            direction="up"
        )
        
        self.stats['beam_scans'] += 1
        return chirp
    
    def _generate_comm_chirp(self):
        """產生通訊用Chirp"""
        if not self.data_buffer:
            # 沒有數據時產生空載Chirp
            return self.chirp_generator.generate_linear_chirp(
                duration=self.chirp_duration,
                bandwidth=self.bandwidth,
                sample_rate=self.sample_rate
            )
        
        # 從緩衝區取得數據位元
        data_bit = self.data_buffer.popleft()
        
        # 根據編碼方式產生Chirp
        if self.comm_params['encoding'] == 'direction':
            direction = "up" if data_bit == 0 else "down"
            chirp = self.chirp_generator.generate_linear_chirp(
                duration=self.chirp_duration,
                bandwidth=self.bandwidth,
                sample_rate=self.sample_rate,
                direction=direction
            )
        else:
            # 其他編碼方式
            encoded = self.chirp_generator.encode_data_in_chirp(
                [data_bit], 
                encoding=self.comm_params['encoding']
            )
            chirp = encoded['encoded_signals'][0]
        
        self.stats['data_bits_sent'] += 1
        return chirp
    
    def _generate_hybrid_chirp(self):
        """產生混合模式Chirp"""
        # 時分複用：根據時間決定是雷達還是通訊
        current_time = time.time() - self.stats['start_time']
        cycle_time = 100e-3  # 100ms週期
        phase = (current_time % cycle_time) / cycle_time
        
        if phase < 0.7:  # 70%時間用於雷達
            return self._generate_radar_chirp()
        else:  # 30%時間用於通訊
            return self._generate_comm_chirp()
    
    def work(self, input_items, output_items):
        """
        GNU Radio work函數
        這是GNU Radio block的核心處理函數
        """
        if not GNURADIO_AVAILABLE:
            # 模擬模式下的簡單處理
            return self._mock_work(output_items)
        
        output = output_items[0]
        
        # 如果沒有當前Chirp或已經用完，產生新的
        if (self.current_chirp is None or 
            self.chirp_index >= len(self.current_chirp['signal'])):
            
            chirp_data = self.generate_next_chirp()
            self.current_chirp = chirp_data['signal']
            self.chirp_index = 0
            self.stats['chirps_generated'] += 1
        
        # 填充輸出緩衝區
        samples_to_output = min(len(output), 
                              len(self.current_chirp) - self.chirp_index)
        
        output[:samples_to_output] = self.current_chirp[
            self.chirp_index:self.chirp_index + samples_to_output
        ]
        
        self.chirp_index += samples_to_output
        
        return samples_to_output
    
    def _mock_work(self, output_items):
        """模擬GNU Radio work函數"""
        # 在沒有GNU Radio的環境中模擬工作
        if hasattr(output_items, '__len__') and len(output_items) > 0:
            output_size = len(output_items[0]) if hasattr(output_items[0], '__len__') else 1024
        else:
            output_size = 1024
        
        chirp_data = self.generate_next_chirp()
        signal = chirp_data['signal']
        
        # 模擬輸出
        samples_to_output = min(output_size, len(signal))
        return samples_to_output
    
    def get_stats(self):
        """取得統計資訊"""
        current_time = time.time()
        runtime = current_time - self.stats['start_time']
        
        stats = self.stats.copy()
        stats.update({
            'runtime_seconds': runtime,
            'chirp_rate': stats['chirps_generated'] / runtime if runtime > 0 else 0,
            'data_rate': stats['data_bits_sent'] / runtime if runtime > 0 else 0,
            'current_mode': self.mode,
            'beam_angle': self.beam_params['tx_beam_angle']
        })
        
        return stats
    
    def print_stats(self):
        """印出統計資訊"""
        stats = self.get_stats()
        print("=== ChirpISAC統計資訊 ===")
        print(f"運行時間: {stats['runtime_seconds']:.1f} 秒")
        print(f"產生Chirp數: {stats['chirps_generated']}")
        print(f"Chirp速率: {stats['chirp_rate']:.1f} chirps/秒")
        print(f"傳送數據位元: {stats['data_bits_sent']}")
        print(f"數據速率: {stats['data_rate']:.1f} bps")
        print(f"Beam掃描次數: {stats['beam_scans']}")
        print(f"當前模式: {stats['current_mode']}")
        print(f"當前Beam角度: {stats['beam_angle']}°")
        print("========================")

class ChirpISACProcessor(gr.gr.sync_block):
    """
    ChirpISAC信號處理器Block
    處理ISAC信號並支援多種處理模式
    """
    
    def __init__(self, 
                 sample_rate=30e6,
                 processing_mode="both"):
        """
        初始化ChirpISAC處理器
        
        Parameters:
        -----------
        sample_rate : float
            取樣率 (Hz)
        processing_mode : str
            處理模式: "radar", "communication", "both"
        """
        if GNURADIO_AVAILABLE:
            gr.gr.sync_block.__init__(
                self,
                name="ChirpISAC Processor",
                in_sig=[np.complex64],  # 輸入複數信號
                out_sig=[np.complex64]  # 輸出複數信號
            )
        
        self.sample_rate = sample_rate
        self.processing_mode = processing_mode
        
        # 處理緩衝區
        self.input_buffer = deque(maxlen=10000)
        self.processing_results = deque(maxlen=1000)
        
        # 雷達處理參數
        self.radar_processor = RadarProcessor()
        self.comm_processor = CommunicationProcessor()
        
        print(f"ChirpISAC Processor初始化完成 - 模式: {processing_mode}")
    
    def work(self, input_items, output_items):
        """GNU Radio work函數"""
        if not GNURADIO_AVAILABLE:
            return self._mock_work(input_items, output_items)
        
        input_signal = input_items[0]
        output = output_items[0]
        
        # 添加到處理緩衝區
        self.input_buffer.extend(input_signal)
        
        # 處理信號
        if self.processing_mode in ["radar", "both"]:
            radar_result = self.radar_processor.process(input_signal)
            if radar_result:
                self.processing_results.append(('radar', radar_result))
        
        if self.processing_mode in ["communication", "both"]:
            comm_result = self.comm_processor.process(input_signal)
            if comm_result:
                self.processing_results.append(('communication', comm_result))
        
        # 直接傳遞信號（或處理後的信號）
        output[:] = input_signal
        
        return len(input_signal)
    
    def _mock_work(self, input_items, output_items):
        """模擬處理函數"""
        # 模擬信號處理
        return 1024
    
    def get_latest_results(self, result_type=None):
        """取得最新處理結果"""
        if result_type:
            return [result for type_name, result in self.processing_results 
                   if type_name == result_type]
        else:
            return list(self.processing_results)

class RadarProcessor:
    """雷達信號處理器"""
    
    def __init__(self):
        self.matched_filter_template = None
        self.range_bins = 512
        self.detection_threshold = 0.5
    
    def process(self, signal):
        """處理雷達信號"""
        # 簡化的雷達處理
        if len(signal) < 100:
            return None
        
        # 匹配濾波
        correlation = self._matched_filter(signal)
        
        # 峰值檢測
        peaks = self._detect_peaks(correlation)
        
        if peaks:
            # 距離估算
            ranges = self._estimate_ranges(peaks)
            return {
                'type': 'radar_detection',
                'ranges': ranges,
                'num_targets': len(peaks),
                'timestamp': time.time()
            }
        
        return None
    
    def _matched_filter(self, signal):
        """匹配濾波器"""
        # 簡化的自相關
        return np.correlate(signal, signal, mode='full')
    
    def _detect_peaks(self, correlation):
        """峰值檢測"""
        threshold = np.max(np.abs(correlation)) * self.detection_threshold
        peaks = []
        
        for i in range(1, len(correlation)-1):
            if (abs(correlation[i]) > threshold and
                abs(correlation[i]) > abs(correlation[i-1]) and
                abs(correlation[i]) > abs(correlation[i+1])):
                peaks.append(i)
        
        return peaks
    
    def _estimate_ranges(self, peaks):
        """估算距離"""
        # 簡化的距離估算
        c = 3e8  # 光速
        sample_rate = 30e6
        ranges = []
        
        for peak in peaks:
            time_delay = peak / sample_rate
            range_m = time_delay * c / 2
            ranges.append(range_m)
        
        return ranges

class CommunicationProcessor:
    """通訊信號處理器"""
    
    def __init__(self):
        self.symbol_buffer = deque(maxlen=1000)
        self.sync_threshold = 0.8
    
    def process(self, signal):
        """處理通訊信號"""
        # 簡化的通訊處理
        if len(signal) < 100:
            return None
        
        # Chirp解調
        demodulated_bits = self._demodulate_chirp(signal)
        
        if demodulated_bits:
            return {
                'type': 'communication_data',
                'bits': demodulated_bits,
                'num_bits': len(demodulated_bits),
                'timestamp': time.time()
            }
        
        return None
    
    def _demodulate_chirp(self, signal):
        """Chirp解調"""
        # 簡化的方向檢測
        # 實際實現會更複雜
        
        # 計算頻率變化方向
        phase_diff = np.diff(np.angle(signal))
        avg_phase_diff = np.mean(phase_diff)
        
        # 根據相位變化判斷Chirp方向
        if avg_phase_diff > 0:
            return [0]  # 上行Chirp = bit 0
        else:
            return [1]  # 下行Chirp = bit 1

def create_chirp_isac_flowgraph():
    """
    建立ChirpISAC處理流程圖
    這個函數建立一個完整的GNU Radio流程圖
    """
    if not GNURADIO_AVAILABLE:
        print("GNU Radio不可用，將建立模擬流程圖")
        return create_mock_flowgraph()
    
    # 建立GNU Radio flow graph
    tb = gr.top_block()
    
    # 信號源
    chirp_source = ChirpISACSource(
        sample_rate=30e6,
        chirp_duration=100e-6,
        bandwidth=20e6,
        mode="hybrid"
    )
    
    # 信號處理器
    chirp_processor = ChirpISACProcessor(
        sample_rate=30e6,
        processing_mode="both"
    )
    
    # 文件接收器（用於debug）
    file_sink = blocks.file_sink(gr.sizeof_gr_complex, "chirp_isac_output.dat")
    
    # 連接blocks
    tb.connect(chirp_source, chirp_processor)
    tb.connect(chirp_processor, file_sink)
    
    print("ChirpISAC流程圖建立完成")
    return tb, chirp_source, chirp_processor

def create_mock_flowgraph():
    """建立模擬流程圖"""
    class MockFlowgraph:
        def __init__(self):
            self.source = ChirpISACSource()
            self.processor = ChirpISACProcessor()
            self.running = False
        
        def start(self):
            print("模擬流程圖啟動")
            self.running = True
        
        def stop(self):
            print("模擬流程圖停止")
            self.running = False
        
        def run(self):
            self.start()
            try:
                time.sleep(5)  # 模擬運行5秒
                # 模擬一些數據處理
                for i in range(10):
                    self.source._mock_work([])
                    time.sleep(0.1)
            finally:
                self.stop()
    
    fg = MockFlowgraph()
    return fg, fg.source, fg.processor

def demo_chirp_isac_blocks():
    """演示ChirpISAC blocks功能"""
    print("=== ChirpISAC Blocks演示 ===")
    
    # 建立流程圖
    flowgraph, source, processor = create_chirp_isac_flowgraph()
    
    # 配置信號源
    print("\n1. 配置信號源...")
    source.set_mode("hybrid")
    source.add_data_to_send([1, 0, 1, 1, 0, 1, 0])
    source.set_beam_angle(30)
    
    # 運行一段時間
    print("\n2. 運行系統...")
    if GNURADIO_AVAILABLE:
        flowgraph.start()
        time.sleep(3)
        flowgraph.stop()
    else:
        flowgraph.run()
    
    # 檢查統計資訊
    print("\n3. 統計資訊...")
    source.print_stats()
    
    # 檢查處理結果
    print("\n4. 處理結果...")
    results = processor.get_latest_results()
    print(f"   處理結果數量: {len(results)}")
    for i, (result_type, result) in enumerate(results[-5:]):  # 顯示最後5個結果
        print(f"   結果 {i+1}: {result_type} - {result}")
    
    print("\n演示完成！")

if __name__ == "__main__":
    demo_chirp_isac_blocks()

