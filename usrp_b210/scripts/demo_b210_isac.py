#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USRP B210 ISAC系統 - 完整功能演示
不需要硬體，在Windows/Linux環境下驗證所有軟體功能
作者: TMYTEK ISAC Lab
"""

import sys
import numpy as np
import time
from pathlib import Path

# 添加路徑
sys.path.append(str(Path(__file__).parent.parent / "config"))

def test_config_system():
    """測試配置系統"""
    print("\n=== 測試1: 配置系統 ===")
    
    try:
        # 優先使用新的硬體驗證配置
        try:
            from hardware_verified_config import get_config
            config = get_config()
            print("✅ 使用硬體驗證配置")
        except ImportError:
            # 如果無法導入新配置，使用舊配置
            from b210_config import B210ISACConfig
            config = B210ISACConfig()
            print("⚠️  使用舊配置 (建議更新到硬體驗證配置)")
        
        # 驗證配置
        if hasattr(config, 'validate_config'):
            validation = config.validate_config()
        else:
            # 舊配置沒有validate_config方法
            validation = {'valid': True, 'errors': [], 'warnings': []}
        
        # 印出摘要
        if hasattr(config, 'print_summary'):
            config.print_summary()
        else:
            print("✅ 配置載入成功")
        
        # 測試儲存/載入 (如果支援)
        if hasattr(config, 'save_config'):
            config_file = config.save_config()
            print(f"✅ 配置檔案儲存成功: {config_file}")
        else:
            print("⚠️  配置儲存功能不可用")
        
        return {
            'success': validation['valid'],
            'details': {
                'errors': validation.get('errors', []),
                'warnings': validation.get('warnings', []),
                'config_type': 'hardware_verified' if 'hardware_verified_config' in str(type(config)) else 'legacy'
            }
        }
        
    except Exception as e:
        print(f"❌ 配置系統測試失敗: {e}")
        return {'success': False, 'error': str(e)}

def test_chirp_generator():
    """測試Chirp信號產生器"""
    print("\n=== 測試2: Chirp信號產生器 ===")
    
    try:
        from chirp_generator import ChirpGenerator
        
        generator = ChirpGenerator()
        
        # 測試基本線性Chirp
        print("2.1 測試線性Chirp...")
        linear_chirp = generator.generate_linear_chirp()
        print(f"   ✅ 線性Chirp產生成功: {len(linear_chirp['signal'])} 樣本")
        
        # 測試數據編碼
        print("2.2 測試數據編碼...")
        data_bits = [1, 0, 1, 1, 0]
        encoded = generator.encode_data_in_chirp(data_bits)
        print(f"   ✅ 數據編碼成功: {len(encoded['encoded_signals'])} 個Chirp")
        
        # 測試信號分析
        print("2.3 測試信號分析...")
        analysis = generator.analyze_chirp(linear_chirp)
        print(f"   ✅ 信號分析完成: 功率={analysis['time_domain']['power']:.3f}")
        
        # 測試非線性Chirp
        print("2.4 測試非線性Chirp...")
        quad_chirp = generator.generate_nonlinear_chirp(chirp_type="quadratic")
        print(f"   ✅ 二次Chirp產生成功: {len(quad_chirp['signal'])} 樣本")
        
        # 測試多重Chirp
        print("2.5 測試多重Chirp...")
        multi_chirp = generator.generate_multi_chirp(num_chirps=4)
        print(f"   ✅ 多重Chirp產生成功: {multi_chirp['parameters']['num_chirps']} 個Chirp")
        
        # 測試雜訊添加
        print("2.6 測試雜訊添加...")
        noisy = generator.add_noise(linear_chirp['signal'], snr_db=20)
        print(f"   ✅ 雜訊添加成功: SNR={noisy['snr_db']} dB")
        
        # 測試信號儲存
        print("2.7 測試信號儲存...")
        filepath = generator.save_signal(linear_chirp, "test_chirp", "json")
        print(f"   ✅ 信號儲存成功: {filepath}")
        
        return {
            'success': True,
            'details': {
                'linear_chirp_samples': len(linear_chirp['signal']),
                'encoded_signals': len(encoded['encoded_signals']),
                'signal_power': analysis['time_domain']['power'],
                'saved_file': str(filepath)
            }
        }
        
    except Exception as e:
        print(f"❌ Chirp產生器測試失敗: {e}")
        return {'success': False, 'error': str(e)}

def test_gnuradio_blocks():
    """測試GNU Radio Blocks"""
    print("\n=== 測試3: GNU Radio Blocks ===")
    
    try:
        from chirp_isac_block import ChirpISACSource, ChirpISACProcessor, create_chirp_isac_flowgraph
        
        # 測試ChirpISAC Source
        print("3.1 測試ChirpISAC Source...")
        source = ChirpISACSource(
            sample_rate=30e6,
            chirp_duration=100e-6,
            bandwidth=20e6,
            mode="hybrid"
        )
        
        # 配置source
        source.set_mode("radar")
        source.add_data_to_send([1, 0, 1, 1, 0])
        source.set_beam_angle(30)
        print("   ✅ ChirpISAC Source配置成功")
        
        # 測試信號產生
        chirp_data = source.generate_next_chirp()
        print(f"   ✅ Chirp產生成功: {len(chirp_data['signal'])} 樣本")
        
        # 測試模式切換
        for mode in ["radar", "communication", "hybrid"]:
            source.set_mode(mode)
            print(f"   ✅ 模式切換到: {mode}")
        
        # 測試ChirpISAC Processor
        print("3.2 測試ChirpISAC Processor...")
        processor = ChirpISACProcessor(
            sample_rate=30e6,
            processing_mode="both"
        )
        print("   ✅ ChirpISAC Processor建立成功")
        
        # 測試流程圖建立
        print("3.3 測試流程圖建立...")
        flowgraph, fg_source, fg_processor = create_chirp_isac_flowgraph()
        print("   ✅ 流程圖建立成功")
        
        # 模擬運行
        print("3.4 模擬運行...")
        if hasattr(flowgraph, 'run'):
            flowgraph.run()
        else:
            # 手動測試work函數
            mock_output = [np.zeros(1024, dtype=np.complex64)]
            result = source._mock_work(mock_output)
            print(f"   ✅ 模擬運行成功: 輸出 {result} 樣本")
        
        # 檢查統計資訊
        stats = source.get_stats()
        print(f"   ✅ 統計資訊: Chirp數={stats['chirps_generated']}, 模式={stats['current_mode']}")
        
        return {
            'success': True,
            'details': {
                'source_created': True,
                'processor_created': True,
                'flowgraph_created': True,
                'stats': stats
            }
        }
        
    except Exception as e:
        print(f"❌ GNU Radio Blocks測試失敗: {e}")
        return {'success': False, 'error': str(e)}

def test_platform_compatibility():
    """測試平台兼容性"""
    print("\n=== 測試4: 平台兼容性 ===")
    
    try:
        import platform
        import os
        
        # 檢測平台
        system = platform.system()
        print(f"4.1 當前平台: {system}")
        
        # 檢查Python版本
        python_version = sys.version_info
        print(f"4.2 Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # 檢查必要模組
        required_modules = ['numpy', 'pathlib', 'json', 'time', 'collections']
        available_modules = []
        
        for module in required_modules:
            try:
                __import__(module)
                available_modules.append(module)
                print(f"   ✅ {module}: 可用")
            except ImportError:
                print(f"   ❌ {module}: 不可用")
        
        # 檢查可選模組
        optional_modules = ['matplotlib', 'scipy', 'gnuradio']
        for module in optional_modules:
            try:
                __import__(module)
                print(f"   ✅ {module}: 可用 (可選)")
            except ImportError:
                print(f"   ⚠️  {module}: 不可用 (可選)")
        
        # 檢查檔案系統
        current_dir = Path(__file__).parent.parent
        required_dirs = ['config', 'scripts', 'tests', 'docs']
        
        for dir_name in required_dirs:
            dir_path = current_dir / dir_name
            if dir_path.exists():
                print(f"   ✅ 目錄 {dir_name}: 存在")
            else:
                print(f"   ❌ 目錄 {dir_name}: 不存在")
        
        compatibility_score = len(available_modules) / len(required_modules)
        
        return {
            'success': compatibility_score >= 1.0,
            'details': {
                'platform': system,
                'python_version': f"{python_version.major}.{python_version.minor}.{python_version.micro}",
                'available_modules': available_modules,
                'compatibility_score': compatibility_score
            }
        }
        
    except Exception as e:
        print(f"❌ 平台兼容性測試失敗: {e}")
        return {'success': False, 'error': str(e)}

def test_system_integration():
    """測試系統整合"""
    print("\n=== 測試5: 系統整合 ===")
    
    try:
        # 完整的系統工作流程測試
        print("5.1 完整工作流程測試...")
        
        # 1. 載入配置
        try:
            from hardware_verified_config import get_config
            config = get_config()
            print("   ✅ 硬體驗證配置載入完成")
        except ImportError:
            from b210_config import B210ISACConfig
            config = B210ISACConfig()
            print("   ⚠️  舊配置載入完成 (建議更新)")
        
        # 2. 建立Chirp產生器
        from chirp_generator import ChirpGenerator
        generator = ChirpGenerator(config)
        print("   ✅ Chirp產生器建立完成")
        
        # 3. 建立ISAC blocks
        from chirp_isac_block import ChirpISACSource, ChirpISACProcessor
        source = ChirpISACSource(
            sample_rate=config.sample_rate,
            chirp_duration=config.chirp_duration,
            bandwidth=config.chirp_bandwidth,
            mode="hybrid"
        )
        processor = ChirpISACProcessor(
            sample_rate=config.sample_rate,
            processing_mode="both"
        )
        print("   ✅ ISAC blocks建立完成")
        
        # 4. 模擬完整ISAC週期
        print("5.2 模擬ISAC處理週期...")
        
        # 雷達模式
        source.set_mode("radar")
        radar_chirp = source.generate_next_chirp()
        print(f"   ✅ 雷達Chirp: {len(radar_chirp['signal'])} 樣本")
        
        # 通訊模式
        source.set_mode("communication")
        source.add_data_to_send([1, 0, 1, 1])
        comm_chirp = source.generate_next_chirp()
        print(f"   ✅ 通訊Chirp: {len(comm_chirp['signal'])} 樣本")
        
        # 混合模式
        source.set_mode("hybrid")
        for i in range(5):
            hybrid_chirp = source.generate_next_chirp()
            print(f"   ✅ 混合模式Chirp {i+1}: {len(hybrid_chirp['signal'])} 樣本")
        
        # 5. Beam掃描模擬
        print("5.3 Beam掃描模擬...")
        scan_angles = [-30, -15, 0, 15, 30]
        for angle in scan_angles:
            source.set_beam_angle(angle)
            beam_chirp = source.generate_next_chirp()
            print(f"   ✅ Beam角度 {angle}°: 信號產生成功")
        
        # 6. 統計資訊檢查
        stats = source.get_stats()
        print(f"5.4 系統統計: 總Chirp數={stats['chirps_generated']}")
        
        return {
            'success': True,
            'details': {
                'radar_chirps': 1,
                'comm_chirps': 1,
                'hybrid_chirps': 5,
                'beam_angles_tested': len(scan_angles),
                'total_chirps': stats['chirps_generated']
            }
        }
        
    except Exception as e:
        print(f"❌ 系統整合測試失敗: {e}")
        return {'success': False, 'error': str(e)}

def run_comprehensive_demo():
    """執行完整演示"""
    print("🚀 USRP B210 ISAC系統 - 完整功能演示")
    print("=" * 60)
    print("注意: 此演示不需要硬體，純軟體功能驗證")
    print("=" * 60)
    
    # 執行所有測試
    tests = [
        ("配置系統", test_config_system),
        ("Chirp產生器", test_chirp_generator), 
        ("GNU Radio Blocks", test_gnuradio_blocks),
        ("平台兼容性", test_platform_compatibility),
        ("系統整合", test_system_integration)
    ]
    
    results = {}
    passed = 0
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            if result['success']:
                passed += 1
                print(f"\n✅ {test_name}: 通過")
            else:
                print(f"\n❌ {test_name}: 失敗")
                if 'error' in result:
                    print(f"   錯誤: {result['error']}")
        except Exception as e:
            print(f"\n💥 {test_name}: 異常 - {e}")
            results[test_name] = {'success': False, 'error': str(e)}
    
    # 總結
    print("\n" + "=" * 60)
    print("📊 演示結果總結")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ 通過" if result['success'] else "❌ 失敗"
        print(f"{status} {test_name}")
    
    success_rate = passed / len(tests)
    print(f"\n總計: {passed}/{len(tests)} 測試通過 ({success_rate*100:.1f}%)")
    
    if success_rate == 1.0:
        print("\n🎉 所有測試通過！軟體功能驗證完成")
        print("\n📋 下一步建議:")
        print("   1. 在Linux環境中執行硬體測試")
        print("   2. 連接USRP B210進行實際測試")
        print("   3. 驗證up/down converter和beam former")
        print("   4. 進行端到端ISAC系統測試")
    elif success_rate >= 0.8:
        print("\n⚠️  大部分測試通過，系統基本可用")
        print("   建議解決失敗的測試後再進行硬體測試")
    else:
        print("\n❌ 多數測試失敗，需要解決軟體問題")
        print("   建議先修復軟體問題再繼續")
    
    return results

if __name__ == "__main__":
    run_comprehensive_demo()