#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TMYTEK 28 GHz OFDM-ISAC 共用參數配置
Compatible with GNU Radio 3.10 + UHD 4.8
Author: TMYTEK ISAC Lab
"""

import numpy as np

# ==== 基本系統參數 ====
class OFDMConfig:
    def __init__(self):
        # 採樣率與頻率
        self.sample_rate = 30.72e6      # 30.72 Msps (LTE numerology)
        self.center_freq = 2.0e9        # 2 GHz IF (USRP)
        self.rf_freq = 28.0e9           # 28 GHz RF (via UDB)
        
        # OFDM參數
        self.fft_len = 2048             # FFT size
        self.cp_len = 144               # CP length (1/14 ≈ 7%)
        self.occupied_carriers = 1200   # 實際使用的子載波
        self.pilot_carriers = ()        # 導頻子載波位置（稍後定義）
        self.pilot_symbols = ()         # 導頻符號
        
        # 子載波分配
        self.subcarrier_spacing = self.sample_rate / self.fft_len  # 15 kHz
        self.bandwidth = self.occupied_carriers * self.subcarrier_spacing  # ~18 MHz
        
        # 調變參數
        self.modulation = "qam16"       # qpsk, qam16, qam64
        self.constellation = self._get_constellation()
        
        # 同步參數
        self.sync_word1 = [1, 1, 1, 1, 1, 1, -1, -1, -1, -1, -1, -1, 1, 1, 1, 1]  # Schmidl-Cox
        self.sync_word2 = [1, 1, -1, -1, 1, 1, -1, -1, 1, 1, -1, -1, 1, 1, -1, -1] # Frame sync
        
        # 導頻設計
        self.pilot_carriers = tuple(range(-600, 601, 50))  # 每50個子載波一個導頻
        self.pilot_symbols = tuple([1, 1, 1, -1] * (len(self.pilot_carriers)//4 + 1))[:len(self.pilot_carriers)]
        
        # USRP參數
        self.usrp_device_args = ""      # 空字串使用預設
        self.usrp_tx_gain = 20.0        # dB
        self.usrp_rx_gain = 20.0        # dB
        self.usrp_tx_antenna = "TX/RX"
        self.usrp_rx_antenna = "RX2"
        
        # 除錯參數
        self.enable_file_sink = True    # 是否儲存中間資料
        self.file_sink_path = "./debug_data/"
        
    def _get_constellation(self):
        """取得星座圖點"""
        if self.modulation == "qpsk":
            return [1+1j, -1+1j, 1-1j, -1-1j]
        elif self.modulation == "qam16":
            return [complex(real, imag) for real in [-3, -1, 1, 3] 
                   for imag in [-3, -1, 1, 3]]
        elif self.modulation == "qam64":
            return [complex(real, imag) for real in [-7, -5, -3, -1, 1, 3, 5, 7] 
                   for imag in [-7, -5, -3, -1, 1, 3, 5, 7]]
        else:
            raise ValueError(f"不支援的調變方式: {self.modulation}")
    
    def get_packet_length_tag_key(self):
        """取得封包長度標籤鍵值"""
        return "packet_len"
    
    def get_sync_words(self):
        """取得同步字元"""
        return (self.sync_word1, self.sync_word2)
    
    def get_occupied_carriers(self):
        """取得佔用的子載波索引"""
        # 避開DC與邊緣子載波
        occupied = list(range(-self.occupied_carriers//2, self.occupied_carriers//2 + 1))
        occupied.remove(0)  # 移除DC
        return tuple(occupied)
    
    def print_config(self):
        """印出配置摘要"""
        print("=== TMYTEK OFDM-ISAC 配置 ===")
        print(f"採樣率: {self.sample_rate/1e6:.2f} Msps")
        print(f"中心頻率: {self.center_freq/1e9:.1f} GHz (IF)")
        print(f"RF頻率: {self.rf_freq/1e9:.1f} GHz")
        print(f"FFT長度: {self.fft_len}")
        print(f"CP長度: {self.cp_len}")
        print(f"子載波間距: {self.subcarrier_spacing/1e3:.1f} kHz")
        print(f"佔用頻寬: {self.bandwidth/1e6:.1f} MHz")
        print(f"調變方式: {self.modulation.upper()}")
        print(f"佔用子載波數: {len(self.get_occupied_carriers())}")
        print(f"導頻子載波數: {len(self.pilot_carriers)}")
        print("============================")

# ==== TDM-ISAC 參數 ====
class TDMConfig:
    def __init__(self):
        # 時框參數
        self.frame_duration_ms = 10.0    # 10ms frame
        self.radar_duration_ms = 2.0     # 2ms radar slot  
        self.comms_duration_ms = 7.85    # 7.85ms comms slot
        self.guard_duration_us = 50.0    # 50μs guard time
        
        # 波束掃描參數
        self.n_beams = 9                 # 波束數量
        self.azimuth_range = [-45, 45]   # 掃描角度範圍
        self.beam_dwell_us = 180.0       # 每個beam的停留時間
        self.beam_settle_us = 30.0       # beam切換穩定時間
        
        # 雷達參數
        self.prf_hz = 5000              # 脈衝重複頻率
        self.range_bins = 1024          # 距離bins
        self.doppler_bins = 128         # 都卜勒bins
        self.cfar_guard = [2, 2]        # CFAR保護cell
        self.cfar_training = [8, 8]     # CFAR訓練cell
        self.cfar_pfa = 1e-3            # 虛警機率

# ==== 使用範例 ====
if __name__ == "__main__":
    # 建立配置實例
    ofdm_cfg = OFDMConfig()
    tdm_cfg = TDMConfig()
    
    # 印出配置
    ofdm_cfg.print_config()
    
    # 範例：取得星座圖
    constellation = ofdm_cfg.get_constellation()
    print(f"\n星座圖點數: {len(constellation)}")
    print(f"前4個點: {constellation[:4]}")
    
    # 範例：取得佔用子載波
    occupied = ofdm_cfg.get_occupied_carriers()
    print(f"\n佔用子載波範圍: {min(occupied)} ~ {max(occupied)}")
    print(f"總數: {len(occupied)}")
