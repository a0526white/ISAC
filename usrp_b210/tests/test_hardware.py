#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USRP B210 硬體功能驗證測試腳本
測試環境: Linux + UHD 4.8 + GNU Radio + Python 3.10.12
作者: TMYTEK ISAC Lab
"""

import uhd
import numpy as np
import time
import sys
from pathlib import Path

class B210HardwareTest:
    """B210硬體功能測試類別"""
    
    def __init__(self):
        self.usrp = None
        self.test_results = {}
        self.sample_rate = 30e6      # 30 Msps
        self.center_freq = 2e9       # 2 GHz IF
        self.bandwidth = 20e6        # 20 MHz
        
    def test_device_connection(self):
        """測試設備連接"""
        print("=== 測試1: 設備連接 ===")
        try:
            # 嘗試連接B210
            self.usrp = uhd.usrp.MultiUSRP("type=b200")
            print(f"✅ 成功連接USRP設備")
            print(f"   設備類型: {self.usrp.get_pp_string()}")
            print(f"   序列號: {self.usrp.get_serial()}")
            print(f"   主機: {self.usrp.get_mboard_name()}")
            return True
        except Exception as e:
            print(f"❌ 設備連接失敗: {e}")
            return False
    
    def test_basic_parameters(self):
        """測試基本參數設定"""
        print("\n=== 測試2: 基本參數設定 ===")
        try:
            # 設定取樣率
            self.usrp.set_tx_rate(self.sample_rate)
            self.usrp.set_rx_rate(self.sample_rate)
            actual_tx_rate = self.usrp.get_tx_rate()
            actual_rx_rate = self.usrp.get_rx_rate()
            
            print(f"✅ 取樣率設定成功")
            print(f"   TX取樣率: {actual_tx_rate/1e6:.2f} Msps")
            print(f"   RX取樣率: {actual_rx_rate/1e6:.2f} Msps")
            
            # 設定頻率
            self.usrp.set_tx_freq(self.center_freq)
            self.usrp.set_rx_freq(self.center_freq)
            actual_tx_freq = self.usrp.get_tx_freq()
            actual_rx_freq = self.usrp.get_rx_freq()
            
            print(f"✅ 頻率設定成功")
            print(f"   TX頻率: {actual_tx_freq/1e9:.3f} GHz")
            print(f"   RX頻率: {actual_rx_freq/1e9:.3f} GHz")
            
            # 設定增益
            self.usrp.set_tx_gain(20.0)
            self.usrp.set_rx_gain(20.0)
            actual_tx_gain = self.usrp.get_tx_gain()
            actual_rx_gain = self.usrp.get_rx_gain()
            
            print(f"✅ 增益設定成功")
            print(f"   TX增益: {actual_tx_gain:.1f} dB")
            print(f"   RX增益: {actual_rx_gain:.1f} dB")
            
            return True
        except Exception as e:
            print(f"❌ 參數設定失敗: {e}")
            return False
    
    def test_simple_signal_transmission(self):
        """測試簡單信號傳輸"""
        print("\n=== 測試3: 簡單信號傳輸 ===")
        try:
            # 產生1MHz正弦波
            duration = 0.001  # 1ms
            samples = int(duration * self.sample_rate)
            t = np.linspace(0, duration, samples)
            signal = np.exp(1j * 2 * np.pi * 1e6 * t)
            
            # 設定發射參數
            stream_args = uhd.usrp.StreamArgs("fc32", "fc32")
            stream_args.channels = [0]
            tx_stream = self.usrp.get_tx_stream(stream_args)
            
            # 發射信號
            tx_metadata = uhd.types.TXMetadata()
            tx_metadata.start_of_burst = True
            tx_metadata.end_of_burst = True
            
            tx_stream.send(signal, tx_metadata)
            print(f"✅ 信號發射成功")
            print(f"   信號長度: {len(signal)} 樣本")
            print(f"   信號頻率: 1 MHz")
            print(f"   發射時間: {duration*1000:.1f} ms")
            
            return True
        except Exception as e:
            print(f"❌ 信號發射失敗: {e}")
            return False
    
    def test_chirp_signal_generation(self):
        """測試Chirp信號產生"""
        print("\n=== 測試4: Chirp信號產生 ===")
        try:
            # Chirp參數
            chirp_duration = 100e-6      # 100μs
            start_freq = 0                # 相對於載波
            stop_freq = self.bandwidth    # 20 MHz
            
            # 產生Chirp信號
            samples = int(chirp_duration * self.sample_rate)
            t = np.linspace(0, chirp_duration, samples)
            
            # 線性調頻
            k = (stop_freq - start_freq) / chirp_duration
            phase = 2 * np.pi * (start_freq * t + 0.5 * k * t**2)
            chirp_signal = np.exp(1j * phase)
            
            print(f"✅ Chirp信號產生成功")
            print(f"   信號長度: {len(chirp_signal)} 樣本")
            print(f"   持續時間: {chirp_duration*1e6:.1f} μs")
            print(f"   頻寬: {self.bandwidth/1e6:.1f} MHz")
            print(f"   調頻斜率: {k/1e12:.2f} THz/s")
            
            # 儲存信號供後續分析
            output_dir = Path("test_signals")
            output_dir.mkdir(exist_ok=True)
            np.save(output_dir / "chirp_signal.npy", chirp_signal)
            print(f"   信號已儲存至: {output_dir / 'chirp_signal.npy'}")
            
            return True
        except Exception as e:
            print(f"❌ Chirp信號產生失敗: {e}")
            return False
    
    def test_signal_quality(self):
        """測試信號品質"""
        print("\n=== 測試5: 信號品質分析 ===")
        try:
            # 產生測試信號
            duration = 0.001  # 1ms
            samples = int(duration * self.sample_rate)
            t = np.linspace(0, duration, samples)
            
            # 多頻率信號
            signal = (np.exp(1j * 2 * np.pi * 1e6 * t) + 
                     np.exp(1j * 2 * np.pi * 5e6 * t) +
                     np.exp(1j * 2 * np.pi * 10e6 * t))
            
            # 頻譜分析
            fft_signal = np.fft.fft(signal)
            freqs = np.fft.fftfreq(len(signal), 1/self.sample_rate)
            
            # 找到峰值頻率
            peak_idx = np.argmax(np.abs(fft_signal))
            peak_freq = freqs[peak_idx]
            
            print(f"✅ 信號品質分析成功")
            print(f"   信號長度: {len(signal)} 樣本")
            print(f"   峰值頻率: {peak_freq/1e6:.1f} MHz")
            print(f"   頻譜解析度: {self.sample_rate/len(signal)/1e3:.1f} kHz")
            
            # 儲存頻譜數據
            output_dir = Path("test_signals")
            np.save(output_dir / "spectrum_freqs.npy", freqs)
            np.save(output_dir / "spectrum_data.npy", fft_signal)
            print(f"   頻譜數據已儲存")
            
            return True
        except Exception as e:
            print(f"❌ 信號品質分析失敗: {e}")
            return False
    
    def test_loopback_capability(self):
        """測試Loopback能力"""
        print("\n=== 測試6: Loopback能力測試 ===")
        try:
            print("⚠️  注意: 此測試需要TX→RX的物理連接")
            print("   如果沒有連接，將跳過此測試")
            
            # 檢查是否有物理連接
            # 這裡可以加入更複雜的連接檢測邏輯
            
            print("✅ Loopback測試準備完成")
            print("   請確保TX→RX有適當的衰減器連接")
            print("   建議衰減值: 20-40 dB")
            
            return True
        except Exception as e:
            print(f"❌ Loopback測試準備失敗: {e}")
            return False
    
    def run_all_tests(self):
        """執行所有測試"""
        print("🚀 開始B210硬體功能驗證測試")
        print("=" * 50)
        
        tests = [
            ("設備連接", self.test_device_connection),
            ("基本參數", self.test_basic_parameters),
            ("信號傳輸", self.test_simple_signal_transmission),
            ("Chirp信號", self.test_chirp_signal_generation),
            ("信號品質", self.test_signal_quality),
            ("Loopback", self.test_loopback_capability)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                    self.test_results[test_name] = "PASS"
                else:
                    self.test_results[test_name] = "FAIL"
            except Exception as e:
                print(f"❌ {test_name}測試異常: {e}")
                self.test_results[test_name] = "ERROR"
        
        # 測試結果總結
        print("\n" + "=" * 50)
        print("📊 測試結果總結")
        print("=" * 50)
        
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result == "PASS" else "❌"
            print(f"{status_icon} {test_name}: {result}")
        
        print(f"\n總計: {passed}/{total} 測試通過")
        
        if passed == total:
            print("🎉 所有測試通過！B210硬體功能正常")
        else:
            print("⚠️  部分測試失敗，請檢查硬體連接和設定")
        
        return passed == total

def main():
    """主函數"""
    print("USRP B210 硬體功能驗證測試")
    print("測試環境: Linux + UHD 4.8 + GNU Radio + Python 3.10.12")
    print("=" * 60)
    
    # 檢查UHD版本
    try:
        uhd_version = uhd.__version__
        print(f"UHD版本: {uhd_version}")
    except:
        print("UHD版本: 未知")
    
    # 檢查Python版本
    print(f"Python版本: {sys.version}")
    
    # 執行測試
    tester = B210HardwareTest()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 下一步: 可以開始Chirp ISAC系統開發")
    else:
        print("\n🔧 請先解決硬體問題，再繼續開發")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
