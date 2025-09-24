#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USRP B210 ISAC系統配置檔案
針對B210硬體限制優化的參數設定
測試環境: Linux + UHD 4.8 + GNU Radio + Python 3.10+
作者: TMYTEK ISAC Lab
"""

import numpy as np
import os
from pathlib import Path

class B210ISACConfig:
    """USRP B210 ISAC系統配置類別"""
    
    def __init__(self):
        # === 基本硬體參數 ===
        self.device_args = "type=b200"
        self.sample_rate = 30e6         # 30 Msps (B210最佳性能)
        self.center_freq_if = 2e9       # 2 GHz IF頻率
        self.center_freq_rf = 28e9      # 28 GHz RF頻率 (透過up/down converter)
        
        # === B210硬體限制 ===
        self.max_sample_rate = 56e6     # B210理論最大值
        self.practical_sample_rate = 30e6  # 實際穩定使用值
        self.max_bandwidth = 20e6       # 實際可用頻寬
        self.max_tx_power = 10          # dBm
        self.max_rx_gain = 76           # dB
        self.max_tx_gain = 89.8         # dB
        
        # === ISAC系統參數 ===
        self.chirp_duration = 100e-6    # 100μs Chirp持續時間
        self.chirp_bandwidth = 20e6     # 20 MHz頻寬
        self.range_resolution = 3e8 / (2 * self.chirp_bandwidth)  # 7.5米
        
        # === 工作模式配置 ===
        self.mode = "hybrid"            # radar, communication, hybrid
        self.radar_duty_cycle = 0.7     # 雷達模式占70%
        self.comm_duty_cycle = 0.3      # 通訊模式占30%
        
        # === Beam Forming參數 ===
        self.beam_scan_enabled = True
        self.scan_angles = list(range(-45, 46, 10))  # ±45度，10度間隔
        self.beam_dwell_time = 100e-3   # 100ms每個beam
        
        # === 信號處理參數 ===
        self.fft_size = 1024            # FFT大小
        self.overlap_factor = 0.5       # 重疊因子
        self.window_type = "hanning"    # 窗函數類型
        
        # === 雷達參數 ===
        self.range_bins = 512           # 距離bins (減少以適應B210)
        self.doppler_bins = 64          # 都卜勒bins
        self.cfar_guard = [2, 2]        # CFAR保護區域
        self.cfar_training = [8, 8]     # CFAR訓練區域
        self.cfar_pfa = 1e-3            # 虛警機率
        
        # === 通訊參數 ===
        self.modulation = "chirp_bpsk"  # Chirp調變方式
        self.data_rate = 200e3          # 200 kbps (B210實際能力)
        self.error_correction = True    # 錯誤更正
        self.frame_size = 1024          # 幀大小
        
        # === 檔案路徑配置 ===
        self.base_path = Path(__file__).parent.parent
        self.log_path = self.base_path / "logs"
        self.data_path = self.base_path / "data"
        self.temp_path = self.base_path / "temp"
        
        # 確保目錄存在
        self._create_directories()
        
        # === Linux/Windows兼容性 ===
        self.platform = self._detect_platform()
        self.uhd_args = self._get_platform_specific_args()
        
    def _detect_platform(self):
        """偵測運行平台"""
        import platform
        return platform.system().lower()
    
    def _get_platform_specific_args(self):
        """取得平台特定的UHD參數"""
        if self.platform == "linux":
            return {
                "device_args": self.device_args,
                "threading": "thread_priority_high",
                "buffer_size": 16384,
                "num_recv_frames": 32,
                "num_send_frames": 32
            }
        else:  # Windows
            return {
                "device_args": self.device_args,
                "buffer_size": 8192,
                "num_recv_frames": 16,
                "num_send_frames": 16
            }
    
    def _create_directories(self):
        """建立必要的目錄"""
        for path in [self.log_path, self.data_path, self.temp_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    def get_chirp_params(self):
        """取得Chirp信號參數"""
        return {
            'duration': self.chirp_duration,
            'bandwidth': self.chirp_bandwidth,
            'sample_rate': self.sample_rate,
            'start_freq': 0,  # 相對於載波
            'stop_freq': self.chirp_bandwidth,
            'samples': int(self.chirp_duration * self.sample_rate)
        }
    
    def get_radar_params(self):
        """取得雷達參數"""
        return {
            'range_resolution': self.range_resolution,
            'max_range': self.range_resolution * self.range_bins,
            'range_bins': self.range_bins,
            'doppler_bins': self.doppler_bins,
            'cfar_params': {
                'guard': self.cfar_guard,
                'training': self.cfar_training,
                'pfa': self.cfar_pfa
            }
        }
    
    def get_beam_params(self):
        """取得beam forming參數"""
        return {
            'scan_enabled': self.beam_scan_enabled,
            'scan_angles': self.scan_angles,
            'dwell_time': self.beam_dwell_time,
            'total_scan_time': len(self.scan_angles) * self.beam_dwell_time
        }
    
    def get_usrp_params(self):
        """取得USRP參數"""
        return {
            'device_args': self.device_args,
            'sample_rate': self.sample_rate,
            'center_freq': self.center_freq_if,
            'tx_gain': min(20.0, self.max_tx_gain),  # 安全增益值
            'rx_gain': min(20.0, self.max_rx_gain),
            'tx_antenna': "TX/RX",
            'rx_antenna': "RX2",
            'platform_args': self.uhd_args
        }
    
    def get_communication_params(self):
        """取得通訊參數"""
        return {
            'modulation': self.modulation,
            'data_rate': self.data_rate,
            'frame_size': self.frame_size,
            'error_correction': self.error_correction,
            'bandwidth_efficiency': self.data_rate / self.chirp_bandwidth
        }
    
    def validate_config(self):
        """驗證配置參數合理性"""
        errors = []
        warnings = []
        
        # 檢查取樣率
        if self.sample_rate > self.max_sample_rate:
            errors.append(f"取樣率 {self.sample_rate/1e6:.1f} Msps 超過B210最大值 {self.max_sample_rate/1e6:.1f} Msps")
        
        # 檢查頻寬
        if self.chirp_bandwidth > self.max_bandwidth:
            errors.append(f"Chirp頻寬 {self.chirp_bandwidth/1e6:.1f} MHz 超過B210最大值 {self.max_bandwidth/1e6:.1f} MHz")
        
        # 檢查Chirp參數
        if self.chirp_duration * self.sample_rate < 10:
            warnings.append("Chirp持續時間過短，可能影響信號品質")
        
        # 檢查距離解析度
        if self.range_resolution > 10:
            warnings.append(f"距離解析度 {self.range_resolution:.1f}米 較粗糙，可能影響雷達性能")
        
        # 檢查beam參數
        if len(self.scan_angles) * self.beam_dwell_time > 5:
            warnings.append("Beam掃描時間過長，可能影響即時性")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def save_config(self, filename=None):
        """儲存配置到檔案"""
        if filename is None:
            filename = self.base_path / "config" / "current_config.json"
        
        import json
        config_dict = {
            'hardware': {
                'device_args': self.device_args,
                'sample_rate': self.sample_rate,
                'center_freq_if': self.center_freq_if,
                'center_freq_rf': self.center_freq_rf
            },
            'chirp': self.get_chirp_params(),
            'radar': self.get_radar_params(),
            'beam': self.get_beam_params(),
            'usrp': self.get_usrp_params(),
            'communication': self.get_communication_params(),
            'platform': self.platform
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
        
        return filename
    
    def load_config(self, filename):
        """從檔案載入配置"""
        import json
        
        with open(filename, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        
        # 更新參數
        if 'hardware' in config_dict:
            hw = config_dict['hardware']
            self.sample_rate = hw.get('sample_rate', self.sample_rate)
            self.center_freq_if = hw.get('center_freq_if', self.center_freq_if)
            
        # 可以根據需要添加更多載入邏輯
        
        return True
    
    def print_summary(self):
        """印出配置摘要"""
        print("=" * 60)
        print("USRP B210 ISAC系統配置摘要")
        print("=" * 60)
        
        print(f"平台: {self.platform.upper()}")
        print(f"設備: {self.device_args}")
        print(f"取樣率: {self.sample_rate/1e6:.1f} Msps")
        print(f"IF頻率: {self.center_freq_if/1e9:.1f} GHz")
        print(f"RF頻率: {self.center_freq_rf/1e9:.1f} GHz")
        
        print(f"\nChirp參數:")
        chirp = self.get_chirp_params()
        print(f"  持續時間: {chirp['duration']*1e6:.1f} μs")
        print(f"  頻寬: {chirp['bandwidth']/1e6:.1f} MHz")
        print(f"  樣本數: {chirp['samples']}")
        
        print(f"\n雷達參數:")
        radar = self.get_radar_params()
        print(f"  距離解析度: {radar['range_resolution']:.1f} 米")
        print(f"  最大距離: {radar['max_range']:.1f} 米")
        print(f"  距離bins: {radar['range_bins']}")
        
        print(f"\nBeam參數:")
        beam = self.get_beam_params()
        print(f"  掃描範圍: {min(beam['scan_angles'])}° ~ {max(beam['scan_angles'])}°")
        print(f"  掃描點數: {len(beam['scan_angles'])}")
        print(f"  總掃描時間: {beam['total_scan_time']*1000:.1f} ms")
        
        print(f"\n通訊參數:")
        comm = self.get_communication_params()
        print(f"  調變方式: {comm['modulation']}")
        print(f"  資料率: {comm['data_rate']/1e3:.1f} kbps")
        print(f"  頻譜效率: {comm['bandwidth_efficiency']*1e3:.3f} bps/Hz")
        
        # 驗證結果
        validation = self.validate_config()
        if validation['errors']:
            print(f"\n❌ 配置錯誤:")
            for error in validation['errors']:
                print(f"  - {error}")
        
        if validation['warnings']:
            print(f"\n⚠️  配置警告:")
            for warning in validation['warnings']:
                print(f"  - {warning}")
        
        if validation['valid'] and not validation['warnings']:
            print(f"\n✅ 配置驗證通過")
        
        print("=" * 60)

# 建立全域配置實例
CONFIG = B210ISACConfig()

def get_config():
    """取得配置實例"""
    return CONFIG

if __name__ == "__main__":
    # 測試配置
    config = B210ISACConfig()
    config.print_summary()
    
    # 儲存配置
    config_file = config.save_config()
    print(f"\n配置已儲存至: {config_file}")

