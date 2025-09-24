#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USRP B210 硬體診斷腳本
診斷硬體連接問題，提供詳細的故障排除建議
作者: TMYTEK ISAC Lab
"""

import sys
import subprocess
import os
from pathlib import Path

def run_command(cmd, sudo=False):
    """執行命令並返回結果"""
    try:
        if sudo:
            cmd = f"echo '24749879' | sudo -S {cmd}"
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip(),
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'stdout': '',
            'stderr': '命令執行超時',
            'returncode': -1
        }
    except Exception as e:
        return {
            'success': False,
            'stdout': '',
            'stderr': str(e),
            'returncode': -1
        }

def check_uhd_installation():
    """檢查UHD安裝狀態"""
    print("🔍 檢查UHD安裝狀態...")
    
    # 檢查UHD版本
    result = run_command("uhd_config_info --version")
    if result['success']:
        print(f"✅ UHD版本: {result['stdout']}")
        return True
    else:
        print(f"❌ UHD版本檢查失敗: {result['stderr']}")
        return False

def check_udev_rules():
    """檢查UHD udev規則"""
    print("\n🔍 檢查UHD udev規則...")
    
    # 檢查規則檔案
    result = run_command("ls -la /etc/udev/rules.d/70-usrp.rules")
    if result['success']:
        print("✅ UHD udev規則檔案存在")
        
        # 檢查規則內容
        result = run_command("cat /etc/udev/rules.d/70-usrp.rules")
        if result['success']:
            print("✅ UHD udev規則內容:")
            for line in result['stdout'].split('\n'):
                if 'idVendor' in line and 'idProduct' in line:
                    print(f"   {line.strip()}")
        return True
    else:
        print("❌ UHD udev規則檔案不存在")
        return False

def check_usb_devices():
    """檢查USB設備"""
    print("\n🔍 檢查USB設備...")
    
    # 檢查所有USB設備
    result = run_command("lsusb")
    if result['success']:
        print("✅ USB設備列表:")
        for line in result['stdout'].split('\n'):
            if line.strip():
                print(f"   {line.strip()}")
        
        # 檢查是否有USRP設備
        usrp_found = False
        for line in result['stdout'].split('\n'):
            if '2500:' in line or '3923:' in line:
                usrp_found = True
                print(f"🎯 發現USRP設備: {line.strip()}")
                break
        
        if not usrp_found:
            print("⚠️  未發現USRP設備")
            return False
        
        return True
    else:
        print(f"❌ USB設備檢查失敗: {result['stderr']}")
        return False

def check_specific_usrp_ids():
    """檢查特定的USRP設備ID"""
    print("\n🔍 檢查特定USRP設備ID...")
    
    usrp_ids = [
        "2500:0020",  # B200
        "2500:0021",  # B200
        "2500:0022",  # B200
        "3923:7813",  # B200
        "3923:7814"   # B200
    ]
    
    found_any = False
    for usrp_id in usrp_ids:
        result = run_command(f"lsusb -d {usrp_id}")
        if result['success'] and result['stdout'].strip():
            print(f"✅ 發現USRP設備 {usrp_id}: {result['stdout'].strip()}")
            found_any = True
    
    if not found_any:
        print("❌ 未發現任何USRP設備")
        return False
    
    return True

def check_sys_usb_devices():
    """檢查/sys/bus/usb/devices/中的設備"""
    print("\n🔍 檢查系統USB設備詳細資訊...")
    
    result = run_command("ls /sys/bus/usb/devices/ | grep -v 'usb'")
    if result['success']:
        print("✅ 系統USB設備:")
        for device in result['stdout'].split('\n'):
            if device.strip():
                print(f"   {device.strip()}")
        
        # 檢查每個設備的vendor和product ID
        print("\n🔍 檢查設備詳細資訊...")
        for device in result['stdout'].split('\n'):
            if device.strip() and not device.startswith('usb'):
                vendor_result = run_command(f"cat /sys/bus/usb/devices/{device}/idVendor 2>/dev/null", sudo=True)
                product_result = run_command(f"cat /sys/bus/usb/devices/{device}/idProduct 2>/dev/null", sudo=True)
                
                if vendor_result['success'] and product_result['success']:
                    vendor_id = vendor_result['stdout'].strip()
                    product_id = product_result['stdout'].strip()
                    print(f"   設備 {device}: Vendor={vendor_id}, Product={product_id}")
                    
                    # 檢查是否是USRP設備
                    if vendor_id in ['2500', '3923']:
                        print(f"   🎯 這可能是USRP設備!")
    
    return True

def check_vmware_usb():
    """檢查VMware USB配置"""
    print("\n🔍 檢查VMware USB配置...")
    
    # 檢查是否在虛擬機中
    result = run_command("dmesg | grep -i 'vmware\|virtual' | head -5")
    if result['success'] and result['stdout']:
        print("⚠️  檢測到VMware虛擬機環境")
        print("   這可能影響USB設備連接")
        
        print("\n📋 VMware USB配置建議:")
        print("   1. 在VMware中啟用USB 3.0直通")
        print("   2. 將USRP B210連接到主機")
        print("   3. 在VMware中連接USB設備")
        print("   4. 確認設備在VMware中可見")
        
        return False
    
    return True

def provide_troubleshooting_advice():
    """提供故障排除建議"""
    print("\n" + "="*60)
    print("🔧 USRP B210 故障排除建議")
    print("="*60)
    
    print("\n📋 硬體檢查:")
    print("   1. 確認USB 3.0連接器牢固連接")
    print("   2. 檢查USRP B210上的LED指示燈")
    print("   3. 確認設備有足夠的電源供應")
    print("   4. 嘗試不同的USB端口")
    
    print("\n📋 軟體檢查:")
    print("   1. 確認UHD驅動正確安裝")
    print("   2. 檢查udev規則是否生效")
    print("   3. 嘗試重新載入udev規則")
    print("   4. 檢查用戶權限")
    
    print("\n📋 虛擬機檢查:")
    print("   1. 在VMware中啟用USB直通")
    print("   2. 將設備連接到主機")
    print("   3. 在VMware中連接設備")
    print("   4. 確認設備在虛擬機中可見")
    
    print("\n📋 測試命令:")
    print("   sudo uhd_usrp_probe")
    print("   sudo uhd_find_devices")
    print("   lsusb | grep -i usrp")
    print("   sudo dmesg | grep -i usrp")

def main():
    """主函數"""
    print("🚀 USRP B210 硬體診斷開始")
    print("="*60)
    
    checks = [
        ("UHD安裝", check_uhd_installation),
        ("UHD udev規則", check_udev_rules),
        ("USB設備", check_usb_devices),
        ("特定USRP ID", check_specific_usrp_ids),
        ("系統USB設備", check_sys_usb_devices),
        ("VMware USB配置", check_vmware_usb)
    ]
    
    results = {}
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"💥 {check_name} 檢查異常: {e}")
            results[check_name] = False
    
    # 結果總結
    print("\n" + "="*60)
    print("📊 診斷結果總結")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for check_name, result in results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{check_name:15} : {status}")
    
    print(f"\n總體結果: {passed}/{total} 項檢查通過")
    
    if passed == total:
        print("🎉 所有檢查通過！USRP B210應該正常工作")
    else:
        print("⚠️  部分檢查失敗，需要進一步診斷")
        provide_troubleshooting_advice()
    
    return results

if __name__ == "__main__":
    main()
