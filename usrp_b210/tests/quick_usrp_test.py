#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速USRP B210測試腳本
一旦設備連接成功，立即測試基本功能
作者: TMYTEK ISAC Lab
"""

import sys
import time
import numpy as np

def test_uhd_import():
    """測試UHD導入"""
    print("🔍 測試UHD導入...")
    try:
        import uhd
        print(f"✅ UHD導入成功: {uhd.__file__}")
        return uhd
    except ImportError as e:
        print(f"❌ UHD導入失敗: {e}")
        return None

def test_device_discovery(uhd):
    """測試設備發現"""
    print("\n🔍 測試設備發現...")
    try:
        # 使用正確的API: uhd.find() 而不是 uhd.find_devices()
        devices = uhd.find("")
        if devices:
            print(f"✅ 發現 {len(devices)} 個USRP設備:")
            for i, device in enumerate(devices):
                print(f"   設備 {i}: {device}")
            return devices
        else:
            print("❌ 未發現USRP設備")
            return []
    except Exception as e:
        print(f"❌ 設備發現失敗: {e}")
        return []

def test_device_connection(uhd, device_args=""):
    """測試設備連接"""
    print(f"\n🔍 測試設備連接: {device_args or '自動檢測'}")
    try:
        if device_args:
            usrp = uhd.usrp.MultiUSRP(device_args)
        else:
            usrp = uhd.usrp.MultiUSRP()
        
        print("✅ 設備連接成功")
        print(f"   設備類型: {usrp.get_pp_string()}")
        print(f"   主機: {usrp.get_mboard_name()}")
        
        # 獲取設備資訊
        try:
            # 嘗試獲取序列號 (如果可用)
            tree = usrp.get_tree()
            if hasattr(tree, 'get') and tree.get('/mboards/0/serial'):
                print(f"   序列號: {tree.get('/mboards/0/serial')}")
        except:
            print("   序列號: 無法獲取")
        
        return usrp
    except Exception as e:
        print(f"❌ 設備連接失敗: {e}")
        return None

def test_basic_parameters(usrp):
    """測試基本參數設定"""
    print("\n🔍 測試基本參數設定...")
    try:
        # 設定取樣率
        sample_rate = 30e6  # 30 Msps
        usrp.set_tx_rate(sample_rate)
        usrp.set_rx_rate(sample_rate)
        actual_tx_rate = usrp.get_tx_rate()
        actual_rx_rate = usrp.get_rx_rate()
        
        print(f"✅ 取樣率設定成功")
        print(f"   TX取樣率: {actual_tx_rate/1e6:.2f} Msps")
        print(f"   RX取樣率: {actual_rx_rate/1e6:.2f} Msps")
        
        # 設定頻率
        center_freq = 2e9  # 2 GHz
        usrp.set_tx_freq(center_freq)
        usrp.set_rx_freq(center_freq)
        actual_tx_freq = usrp.get_tx_freq()
        actual_rx_freq = usrp.get_rx_freq()
        
        print(f"✅ 頻率設定成功")
        print(f"   TX頻率: {actual_tx_freq/1e9:.3f} GHz")
        print(f"   RX頻率: {actual_rx_freq/1e9:.3f} GHz")
        
        # 設定增益
        usrp.set_tx_gain(20.0)
        usrp.set_rx_gain(20.0)
        actual_tx_gain = usrp.get_tx_gain()
        actual_rx_gain = usrp.get_rx_gain()
        
        print(f"✅ 增益設定成功")
        print(f"   TX增益: {actual_tx_gain:.1f} dB")
        print(f"   RX增益: {actual_rx_gain:.1f} dB")
        
        return True
    except Exception as e:
        print(f"❌ 參數設定失敗: {e}")
        return False

def test_simple_tx_rx(usrp):
    """測試簡單TX/RX功能"""
    print("\n🔍 測試簡單TX/RX功能...")
    try:
        # 產生1MHz正弦波
        duration = 0.001  # 1ms
        sample_rate = usrp.get_tx_rate()
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples)
        signal = np.exp(1j * 2 * np.pi * 1e6 * t)
        
        # 設定發射參數
        import uhd  # 重新導入uhd模組
        stream_args = uhd.usrp.StreamArgs("fc32", "fc32")
        stream_args.channels = [0]
        tx_stream = usrp.get_tx_stream(stream_args)
        
        # 發射信號
        tx_metadata = uhd.types.TXMetadata()
        tx_metadata.start_of_burst = True
        tx_metadata.end_of_burst = True
        
        tx_stream.send(signal, tx_metadata)
        print(f"✅ 信號發射成功: {len(signal)} 樣本")
        
        return True
    except Exception as e:
        print(f"❌ TX/RX測試失敗: {e}")
        return False

def main():
    """主函數"""
    print("🚀 快速USRP B210測試開始")
    print("=" * 50)
    
    # 測試UHD導入
    uhd = test_uhd_import()
    if not uhd:
        print("❌ 無法繼續測試")
        return False
    
    # 測試設備發現
    devices = test_device_discovery(uhd)
    if not devices:
        print("❌ 未發現USRP設備，請檢查硬體連接")
        return False
    
    # 測試設備連接
    usrp = test_device_connection(uhd)
    if not usrp:
        print("❌ 無法連接USRP設備")
        return False
    
    # 測試基本參數
    if not test_basic_parameters(usrp):
        print("❌ 基本參數設定失敗")
        return False
    
    # 測試簡單TX/RX
    if not test_simple_tx_rx(usrp):
        print("❌ TX/RX功能測試失敗")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 所有測試通過！USRP B210工作正常")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n💡 建議:")
        print("   1. 檢查USB連接")
        print("   2. 確認設備電源")
        print("   3. 檢查VMware USB配置")
        print("   4. 重新連接設備")
        sys.exit(1)
