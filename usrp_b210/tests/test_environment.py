#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
環境檢查測試腳本
檢查Linux環境中的UHD、GNU Radio和Python套件
"""

import sys
import subprocess
import importlib

def check_python_version():
    """檢查Python版本"""
    print("=== Python環境檢查 ===")
    print(f"Python版本: {sys.version}")
    
    if sys.version_info >= (3, 10):
        print("✅ Python 3.10+ 版本符合要求")
        return True
    else:
        print("❌ Python版本過低，需要3.10+")
        return False

def check_uhd_installation():
    """檢查UHD安裝"""
    print("\n=== UHD安裝檢查 ===")
    
    # 檢查UHD命令列工具
    try:
        result = subprocess.run(['uhd_usrp_probe'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ UHD命令列工具可用")
            print("   輸出預覽:")
            for line in result.stdout.split('\n')[:5]:
                if line.strip():
                    print(f"   {line}")
        else:
            print("❌ UHD命令列工具不可用")
            return False
    except FileNotFoundError:
        print("❌ UHD命令列工具未找到")
        return False
    except subprocess.TimeoutExpired:
        print("⚠️  UHD命令列工具執行超時")
        return False
    
    # 檢查UHD Python綁定
    try:
        import uhd
        print("✅ UHD Python綁定可用")
        
        # 嘗試獲取版本
        try:
            version = uhd.__version__
            print(f"   UHD版本: {version}")
        except:
            print("   UHD版本: 未知")
        
        return True
    except ImportError as e:
        print(f"❌ UHD Python綁定不可用: {e}")
        return False

def check_gnuradio_installation():
    """檢查GNU Radio安裝"""
    print("\n=== GNU Radio安裝檢查 ===")
    
    # 檢查GNU Radio命令列工具
    try:
        result = subprocess.run(['gnuradio-companion', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ GNU Radio Companion可用")
            print("   輸出預覽:")
            for line in result.stdout.split('\n')[:3]:
                if line.strip():
                    print(f"   {line}")
        else:
            print("❌ GNU Radio Companion不可用")
            return False
    except FileNotFoundError:
        print("❌ GNU Radio Companion未找到")
        return False
    except subprocess.TimeoutExpired:
        print("⚠️  GNU Radio Companion執行超時")
        return False
    
    # 檢查GNU Radio Python綁定
    try:
        import gnuradio
        print("✅ GNU Radio Python綁定可用")
        
        # 嘗試獲取版本
        try:
            version = gnuradio.__version__
            print(f"   GNU Radio版本: {version}")
        except:
            print("   GNU Radio版本: 未知")
        
        return True
    except ImportError as e:
        print(f"❌ GNU Radio Python綁定不可用: {e}")
        return False

def check_python_packages():
    """檢查Python套件"""
    print("\n=== Python套件檢查 ===")
    
    required_packages = [
        'numpy',
        'scipy', 
        'matplotlib',
        'pandas'
    ]
    
    optional_packages = [
        'plotly',
        'pytest',
        'pyyaml',
        'tqdm',
        'rich'
    ]
    
    print("必要套件:")
    required_ok = True
    for package in required_packages:
        try:
            module = importlib.import_module(package)
            version = getattr(module, '__version__', '未知')
            print(f"   ✅ {package}: {version}")
        except ImportError:
            print(f"   ❌ {package}: 未安裝")
            required_ok = False
    
    print("\n可選套件:")
    for package in optional_packages:
        try:
            module = importlib.import_module(package)
            version = getattr(module, '__version__', '未知')
            print(f"   ✅ {package}: {version}")
        except ImportError:
            print(f"   ⚠️  {package}: 未安裝 (可選)")
    
    return required_ok

def check_usrp_devices():
    """檢查USRP設備"""
    print("\n=== USRP設備檢查 ===")
    
    try:
        result = subprocess.run(['uhd_usrp_probe'], 
                              capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            print("✅ USRP設備檢測成功")
            
            # 分析輸出找到設備信息
            output_lines = result.stdout.split('\n')
            device_found = False
            
            for line in output_lines:
                if 'B200' in line or 'B210' in line:
                    print(f"   🎯 找到B200/B210設備: {line.strip()}")
                    device_found = True
                elif 'Device' in line and 'type' in line:
                    print(f"   設備類型: {line.strip()}")
                elif 'Serial' in line:
                    print(f"   序列號: {line.strip()}")
            
            if not device_found:
                print("   ⚠️  未檢測到B200/B210設備")
                print("   請檢查設備連接")
            
            return device_found
        else:
            print("❌ USRP設備檢測失敗")
            print(f"   錯誤輸出: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ USRP設備檢測異常: {e}")
        return False

def main():
    """主函數"""
    print("🔍 USRP B210 ISAC 系統環境檢查")
    print("=" * 50)
    
    checks = [
        ("Python版本", check_python_version),
        ("UHD安裝", check_uhd_installation),
        ("GNU Radio安裝", check_gnuradio_installation),
        ("Python套件", check_python_packages),
        ("USRP設備", check_usrp_devices)
    ]
    
    results = {}
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"❌ {check_name}檢查異常: {e}")
            results[check_name] = False
    
    # 總結
    print("\n" + "=" * 50)
    print("📊 環境檢查結果總結")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for check_name, result in results.items():
        status_icon = "✅" if result else "❌"
        status_text = "通過" if result else "失敗"
        print(f"{status_icon} {check_name}: {status_text}")
        if result:
            passed += 1
    
    print(f"\n總計: {passed}/{total} 檢查通過")
    
    if passed == total:
        print("\n🎉 環境檢查完全通過！可以開始硬體測試")
        print("下一步: 執行 python test_hardware.py")
    elif passed >= 3:
        print("\n⚠️  環境基本可用，但建議解決問題後再繼續")
        print("下一步: 解決問題後執行 python test_hardware.py")
    else:
        print("\n❌ 環境問題較多，請先解決基本環境問題")
    
    return passed == total

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
