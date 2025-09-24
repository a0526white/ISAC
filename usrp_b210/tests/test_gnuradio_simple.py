#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化的GNU Radio測試腳本
測試基本的GNU Radio功能
作者: TMYTEK ISAC Lab
"""

import sys
import numpy as np

def test_gnuradio_import():
    """測試GNU Radio導入"""
    print("🔍 測試GNU Radio導入...")
    
    try:
        # 添加正確的GNU Radio路徑
        sys.path.extend([
            "/usr/local/lib/python3.10/dist-packages",
            "/usr/lib/python3/dist-packages/gnuradio"
        ])
        
        from gnuradio import gr
        print("✅ gnuradio.gr模組載入成功")
        
        # 檢查基本屬性
        if hasattr(gr, 'sync_block'):
            print("✅ gr.sync_block 可用")
        else:
            print("❌ gr.sync_block 不可用")
        
        if hasattr(gr, 'io_signature'):
            print("✅ gr.io_signature 可用")
        else:
            print("❌ gr.io_signature 不可用")
        
        return True
        
    except Exception as e:
        print(f"❌ GNU Radio導入失敗: {e}")
        return False

def test_gnuradio_blocks():
    """測試GNU Radio Blocks"""
    print("\n🔍 測試GNU Radio Blocks...")
    
    try:
        from gnuradio import blocks
        print("✅ gnuradio.blocks模組載入成功")
        
        # 檢查一些基本blocks
        available_blocks = [attr for attr in dir(blocks) if not attr.startswith('_')]
        print(f"✅ 可用blocks數量: {len(available_blocks)}")
        
        return True
        
    except Exception as e:
        print(f"❌ GNU Radio Blocks測試失敗: {e}")
        return False

def test_gnuradio_uhd():
    """測試GNU Radio UHD"""
    print("\n🔍 測試GNU Radio UHD...")
    
    try:
        from gnuradio import uhd
        print("✅ gnuradio.uhd模組載入成功")
        
        # 檢查UHD功能
        if hasattr(uhd, 'usrp'):
            print("✅ uhd.usrp 可用")
        else:
            print("❌ uhd.usrp 不可用")
        
        return True
        
    except Exception as e:
        print(f"❌ GNU Radio UHD測試失敗: {e}")
        return False

def test_custom_blocks():
    """測試自定義Blocks"""
    print("\n🔍 測試自定義Blocks...")
    
    try:
        # 嘗試導入我們的ChirpISAC blocks
        sys.path.append(str(Path(__file__).parent.parent / "scripts"))
        
        from chirp_isac_block import ChirpISACSource
        print("✅ ChirpISACSource 導入成功")
        
        # 創建實例
        source = ChirpISACSource(
            sample_rate=30e6,
            chirp_duration=100e-6,
            bandwidth=20e6,
            mode="radar"
        )
        print("✅ ChirpISACSource 創建成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 自定義Blocks測試失敗: {e}")
        return False

def main():
    """主函數"""
    print("🚀 GNU Radio 簡化測試開始")
    print("=" * 50)
    
    tests = [
        ("GNU Radio導入", test_gnuradio_import),
        ("GNU Radio Blocks", test_gnuradio_blocks),
        ("GNU Radio UHD", test_gnuradio_uhd),
        ("自定義Blocks", test_custom_blocks)
    ]
    
    results = {}
    passed = 0
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            if result:
                passed += 1
        except Exception as e:
            print(f"💥 {test_name} 測試異常: {e}")
            results[test_name] = False
    
    # 結果總結
    print("\n" + "=" * 50)
    print("📊 GNU Radio測試結果總結")
    print("=" * 50)
    
    for test_name, result in results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name:15} : {status}")
    
    print(f"\n總計: {passed}/{len(tests)} 項測試通過")
    
    if passed == len(tests):
        print("🎉 所有GNU Radio測試通過！")
    else:
        print("⚠️  部分GNU Radio測試失敗")
    
    return results

if __name__ == "__main__":
    from pathlib import Path
    main()

