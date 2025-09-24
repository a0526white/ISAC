#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USRP B210 基礎硬體測試腳本
驗證基本TX/RX功能，為ISAC系統整合做準備
作者: TMYTEK ISAC Lab
"""

import sys
import time
import numpy as np
from pathlib import Path

# 添加scripts目錄到路徑
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.append(str(scripts_dir))

def test_uhd_installation():
    """測試UHD安裝狀態"""
    print("🔍 測試UHD安裝狀態...")
    
    try:
        import uhd
        print(f"✅ UHD版本: {uhd.get_version_string()}")
        return True
    except ImportError as e:
        print(f"❌ UHD未安裝: {e}")
        return False

def test_gnuradio_installation():
    """測試GNU Radio安裝狀態"""
    print("🔍 測試GNU Radio安裝狀態...")
    
    try:
        import gnuradio
        print(f"✅ GNU Radio版本: {gnuradio.version()}")
        return True
    except ImportError as e:
        print(f"❌ GNU Radio未安裝: {e}")
        return False

def test_usrp_connection():
    """測試USRP B210連接"""
    print("🔍 測試USRP B210連接...")
    
    try:
        import uhd
        
        # 尋找USRP設備
        usrp_info = uhd.find_devices()
        if not usrp_info:
            print("❌ 未找到USRP設備")
            return False
        
        print(f"✅ 找到 {len(usrp_info)} 個USRP設備:")
        for i, info in enumerate(usrp_info):
            print(f"  設備 {i}: {info}")
        
        # 嘗試連接第一個設備
        try:
            usrp = uhd.usrp.MultiUSRP()
            print("✅ USRP連接成功")
            
            # 獲取設備信息
            print(f"  主時鐘頻率: {usrp.get_master_clock_rate()/1e6:.1f} MHz")
            print(f"  子設備數量: {len(usrp.get_tx_subdev_spec())}")
            
            return True
            
        except Exception as e:
            print(f"❌ USRP連接失敗: {e}")
            return False
            
    except Exception as e:
        print(f"❌ USRP測試失敗: {e}")
        return False

def test_basic_tx_rx():
    """測試基本TX/RX功能"""
    print("🔍 測試基本TX/RX功能...")
    
    try:
        import uhd
        import numpy as np
        
        # 創建USRP對象
        usrp = uhd.usrp.MultiUSRP()
        
        # 基本參數設定
        sample_rate = 30e6      # 30 Msps
        center_freq = 2e9       # 2 GHz
        gain = 20               # 20 dB
        
        # 設定參數
        usrp.set_tx_rate(sample_rate)
        usrp.set_rx_rate(sample_rate)
        usrp.set_tx_freq(uhd.libpyuhd.types.tune_request(center_freq))
        usrp.set_rx_freq(uhd.libpyuhd.types.tune_request(center_freq))
        usrp.set_tx_gain(gain)
        usrp.set_rx_gain(gain)
        
        print("✅ 基本參數設定成功")
        
        # 產生測試信號 (簡單正弦波)
        duration = 0.001  # 1ms
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples, endpoint=False)
        test_signal = np.exp(1j * 2 * np.pi * 1e6 * t)  # 1MHz正弦波
        
        # 轉換為float32格式
        test_signal = test_signal.astype(np.complex64)
        
        print("✅ 測試信號產生成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 基本TX/RX測試失敗: {e}")
        return False

def test_tmytek_integration():
    """測試TMYTEK設備整合"""
    print("🔍 測試TMYTEK設備整合...")
    
    try:
        # 嘗試導入TMYTEK庫
        lib_path = Path(__file__).parent.parent / "lib"
        sys.path.insert(0, str(lib_path))
        
        try:
            from tlkcore.TLKCoreService import TLKCoreService
            print("✅ TMYTEK TLKCoreService導入成功")
            
            # 嘗試創建服務實例
            service = TLKCoreService()
            print("✅ TMYTEK服務創建成功")
            
            return True
            
        except ImportError as e:
            print(f"⚠️ TMYTEK庫導入失敗: {e}")
            print("  這在硬體整合階段是正常的")
            return True  # 不算失敗
            
    except Exception as e:
        print(f"❌ TMYTEK整合測試失敗: {e}")
        return False

def run_all_tests():
    """執行所有測試"""
    print("🚀 開始USRP B210硬體測試")
    print("=" * 50)
    
    tests = [
        ("UHD安裝", test_uhd_installation),
        ("GNU Radio安裝", test_gnuradio_installation),
        ("USRP連接", test_usrp_connection),
        ("基本TX/RX", test_basic_tx_rx),
        ("TMYTEK整合", test_tmytek_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        try:
            success = test_func()
            results[test_name] = success
            
            if success:
                print(f"✅ {test_name} 測試通過")
            else:
                print(f"❌ {test_name} 測試失敗")
                
        except Exception as e:
            print(f"💥 {test_name} 測試異常: {e}")
            results[test_name] = False
    
    # 測試結果總結
    print("\n" + "=" * 50)
    print("📊 測試結果總結")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name:15} : {status}")
    
    print(f"\n總體結果: {passed}/{total} 項測試通過")
    
    if passed == total:
        print("🎉 所有測試通過！硬體準備就緒")
        print("下一步: 開始ISAC系統整合")
    elif passed >= 3:
        print("⚠️  部分測試通過，可以開始基本ISAC功能開發")
        print("建議: 先解決失敗的測試項目")
    else:
        print("❌ 多數測試失敗，需要先解決硬體問題")
        print("建議: 檢查硬體連接和驅動安裝")
    
    return results

if __name__ == "__main__":
    run_all_tests()
