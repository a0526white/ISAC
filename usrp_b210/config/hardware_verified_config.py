#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USRP B210 ISAC系統 - 硬體驗證配置檔案
基於實際硬體測試結果，確保配置與硬體完全匹配
作者: TMYTEK ISAC Lab
"""

import numpy as np
import os
from pathlib import Path

class HardwareVerifiedConfig:
    """基於硬體驗證的USRP B210 ISAC配置類別"""
    
    def __init__(self):
        # === 硬體驗證參數 (基於實際測試) ===
        self.device_info = {
            'type': 'b200',
            'name': 'NI2901',
            'serial': '32C78E1',
            'product': 'B210',
            'firmware_version': '8.0',
            'fpga_version': '16.0'
        }
        
        # === 硬體規格 (已驗證) ===
        self.hardware_specs = {
            'frequency_range': (50e6, 6e9),      # 50 MHz - 6 GHz
            'max_sample_rate': 56e6,             # 56 Msps (理論最大值)
            'verified_sample_rate': 30e6,        # 30 Msps (已驗證穩定)
            'max_bandwidth': 20e6,               # 20 MHz (實際可用)
            'tx_gain_range': (0.0, 89.8),       # TX增益範圍 (步長0.2 dB)
            'rx_gain_range': (0.0, 76.0),       # RX增益範圍 (步長1.0 dB)
            'usb_version': 'USB 3.0',
            'operating_mode': 'SuperSpeed'
        }
        
        # === 當前工作配置 (已驗證) ===
        self.current_config = {
            'sample_rate': 30e6,                 # 30 Msps (已驗證)
            'center_freq_if': 2e9,               # 2 GHz IF頻率
            'center_freq_rf': 28e9,              # 28 GHz RF頻率 (目標)
            'tx_gain': 20.0,                     # TX增益 (已驗證)
            'rx_gain': 20.0,                     # RX增益 (已驗證)
            'tx_antenna': 'TX/RX',               # TX天線 (已驗證)
            'rx_antenna': 'RX2'                  # RX天線 (已驗證)
        }
        
        # === ISAC系統參數 (基於硬體能力) ===
        self.isac_params = {
            'chirp_duration': 100e-6,            # 100μs Chirp持續時間
            'chirp_bandwidth': 20e6,             # 20 MHz頻寬
            'range_resolution': 7.5,              # 7.5米距離解析度
            'mode': 'hybrid',                     # 混合模式
            'radar_duty_cycle': 0.7,             # 雷達70%
            'comm_duty_cycle': 0.3               # 通訊30%
        }
        
        # === 向後兼容性屬性 ===
        # 為了與現有腳本兼容，添加這些屬性
        self.chirp_duration = self.isac_params['chirp_duration']
        self.chirp_bandwidth = self.isac_params['chirp_bandwidth']
        self.sample_rate = self.current_config['sample_rate']
        
        # === 雷達參數 (已驗證) ===
        self.radar_params = {
            'range_bins': 512,                   # 距離bins
            'doppler_bins': 64,                  # 都卜勒bins
            'cfar_guard': [2, 2],                # CFAR保護區域
            'cfar_training': [8, 8],             # CFAR訓練區域
            'cfar_pfa': 1e-3,                    # 虛警機率
            'max_range': 3840.0                  # 最大檢測範圍
        }
        
        # === Beam Forming參數 ===
        self.beam_params = {
            'scan_enabled': True,
            'scan_angles': list(range(-45, 46, 10)),  # ±45度，10度間隔
            'dwell_time': 100e-3,                # 100ms每個beam
            'total_scan_time': 1.0               # 總掃描時間
        }
        
        # === 通訊參數 ===
        self.comm_params = {
            'modulation': 'chirp_bpsk',          # Chirp調變
            'data_rate': 200e3,                  # 200 kbps
            'error_correction': True,            # 錯誤更正
            'frame_size': 1024                   # 幀大小
        }
        
        # === 信號處理參數 ===
        self.signal_params = {
            'fft_size': 1024,                    # FFT大小
            'overlap_factor': 0.5,               # 重疊因子
            'window_type': 'hanning',            # 窗函數
            'buffer_size': 16384,                # 緩衝區大小 (Linux優化)
            'num_recv_frames': 32,               # 接收幀數
            'num_send_frames': 32                # 發送幀數
        }
        
        # === 平台特定配置 ===
        self.platform = self._detect_platform()
        self.uhd_args = self._get_platform_specific_args()
        
        # === 檔案路徑配置 ===
        self.base_path = Path(__file__).parent.parent
        self.log_path = self.base_path / "logs"
        self.data_path = self.base_path / "data"
        self.temp_path = self.base_path / "temp"
        
        # === GNU Radio路徑配置 ===
        self.gnuradio_paths = [
            "/usr/local/lib/python3.10/dist-packages",
            "/usr/lib/python3/dist-packages/gnuradio"
        ]
        
        # 確保目錄存在
        self._create_directories()
    
    def _detect_platform(self):
        """偵測運行平台"""
        import platform
        return platform.system().lower()
    
    def _get_platform_specific_args(self):
        """取得平台特定的UHD參數"""
        if self.platform == "linux":
            return {
                "device_args": f"type={self.device_info['type']}",
                "threading": "thread_priority_high",
                "buffer_size": self.signal_params['buffer_size'],
                "num_recv_frames": self.signal_params['num_recv_frames'],
                "num_send_frames": self.signal_params['num_send_frames']
            }
        else:  # Windows
            return {
                "device_args": f"type={self.device_info['type']}",
                "buffer_size": 8192,
                "num_recv_frames": 16,
                "num_send_frames": 16
            }
    
    def _create_directories(self):
        """創建必要的目錄"""
        for path in [self.log_path, self.data_path, self.temp_path]:
            path.mkdir(exist_ok=True)
    
    def get_device_args(self):
        """獲取設備參數"""
        return f"type={self.device_info['type']}"
    
    def get_verified_config(self):
        """獲取已驗證的配置"""
        return {
            'hardware': self.hardware_specs,
            'current': self.current_config,
            'isac': self.isac_params,
            'radar': self.radar_params,
            'beam': self.beam_params,
            'communication': self.comm_params,
            'signal': self.signal_params,
            'platform': self.platform
        }
    
    def validate_config(self):
        """驗證配置是否與硬體匹配"""
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # 檢查取樣率
        if self.current_config['sample_rate'] > self.hardware_specs['verified_sample_rate']:
            validation_results['warnings'].append(
                f"取樣率 {self.current_config['sample_rate']/1e6:.1f} Msps 超過已驗證的穩定值"
            )
        
        # 檢查頻率
        if not (self.hardware_specs['frequency_range'][0] <= 
                self.current_config['center_freq_if'] <= 
                self.hardware_specs['frequency_range'][1]):
            validation_results['errors'].append(
                f"IF頻率 {self.current_config['center_freq_if']/1e9:.1f} GHz 超出硬體支援範圍"
            )
        
        # 檢查增益
        if not (self.hardware_specs['tx_gain_range'][0] <= 
                self.current_config['tx_gain'] <= 
                self.hardware_specs['tx_gain_range'][1]):
            validation_results['errors'].append(
                f"TX增益 {self.current_config['tx_gain']} dB 超出硬體支援範圍"
            )
        
        if not (self.hardware_specs['rx_gain_range'][0] <= 
                self.current_config['rx_gain'] <= 
                self.hardware_specs['rx_gain_range'][1]):
            validation_results['errors'].append(
                f"RX增益 {self.current_config['rx_gain']} dB 超出硬體支援範圍"
            )
        
        # 檢查頻寬
        if self.isac_params['chirp_bandwidth'] > self.hardware_specs['max_bandwidth']:
            validation_results['warnings'].append(
                f"Chirp頻寬 {self.isac_params['chirp_bandwidth']/1e6:.1f} MHz 接近硬體限制"
            )
        
        validation_results['valid'] = len(validation_results['errors']) == 0
        return validation_results
    
    def print_summary(self):
        """印出配置摘要"""
        print("=" * 60)
        print("🔧 USRP B210 硬體驗證配置摘要")
        print("=" * 60)
        
        print(f"📱 設備資訊:")
        print(f"   類型: {self.device_info['type']}")
        print(f"   名稱: {self.device_info['name']}")
        print(f"   序列號: {self.device_info['serial']}")
        print(f"   產品: {self.device_info['product']}")
        print(f"   固件: v{self.device_info['firmware_version']}")
        print(f"   FPGA: v{self.device_info['fpga_version']}")
        
        print(f"\n⚙️  硬體規格:")
        print(f"   頻率範圍: {self.hardware_specs['frequency_range'][0]/1e6:.0f} MHz - {self.hardware_specs['frequency_range'][1]/1e9:.1f} GHz")
        print(f"   取樣率: {self.current_config['sample_rate']/1e6:.1f} Msps")
        print(f"   頻寬: {self.isac_params['chirp_bandwidth']/1e6:.1f} MHz")
        print(f"   距離解析度: {self.isac_params['range_resolution']:.1f} 米")
        
        print(f"\n🎯 當前配置:")
        print(f"   IF頻率: {self.current_config['center_freq_if']/1e9:.1f} GHz")
        print(f"   RF頻率: {self.current_config['center_freq_rf']/1e9:.1f} GHz")
        print(f"   TX增益: {self.current_config['tx_gain']:.1f} dB")
        print(f"   RX增益: {self.current_config['rx_gain']:.1f} dB")
        print(f"   平台: {self.platform}")
        
        # 驗證配置
        validation = self.validate_config()
        print(f"\n✅ 配置驗證:")
        if validation['valid']:
            print("   配置與硬體完全匹配 ✅")
        else:
            print("   配置存在問題 ❌")
            for error in validation['errors']:
                print(f"   ❌ {error}")
        
        if validation['warnings']:
            print("   警告:")
            for warning in validation['warnings']:
                print(f"   ⚠️  {warning}")
        
        print("=" * 60)

def get_config():
    """獲取配置實例"""
    return HardwareVerifiedConfig()

if __name__ == "__main__":
    config = get_config()
    config.print_summary()
