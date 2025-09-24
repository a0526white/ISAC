#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Beam Control 模組使用範例
包含各種實際應用場景的範例代碼
作者: TMYTEK ISAC Lab
"""

import sys
import time
import numpy as np
from pathlib import Path

# 添加scripts路徑
scripts_path = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_path))

from beam_control import create_isac_beam_interface, BeamControlConfig

class BeamControlExamples:
    """Beam Control使用範例類別"""
    
    def __init__(self):
        self.interface = None
        self.config = None
        
    def setup_interface(self, custom_config=None):
        """設置介面"""
        print("🔧 設置Beam Control介面...")
        
        if custom_config:
            self.config = custom_config
        else:
            self.config = BeamControlConfig()
            # 自定義一些參數
            self.config.target_freq = 28.0
            self.config.scan_range = (-45, 45)
            self.config.max_log_files = 3  # 減少日誌檔案數量
        
        self.interface = create_isac_beam_interface(self.config)
        
        if self.interface.initialize():
            print("✅ 介面初始化成功")
            return True
        else:
            print("❌ 介面初始化失敗")
            return False
    
    def example_1_basic_control(self):
        """範例1: 基本波束控制"""
        print("\n" + "="*50)
        print("📚 範例1: 基本波束控制")
        print("="*50)
        
        if not self.interface:
            print("❌ 介面未初始化")
            return False
        
        try:
            # 1. 設置TX模式
            print("📡 設置TX模式...")
            if self.interface.set_bbox_mode("TX"):
                print("✅ TX模式設置成功")
            else:
                print("❌ TX模式設置失敗")
                return False
            
            # 2. 測試不同角度
            test_angles = [
                (0, 0),      # 正前方
                (15, 0),     # 右側15度
                (-15, 0),    # 左側15度
                (30, 0),     # 右側30度
                (-30, 0),    # 左側30度
                (0, 180),    # 後方
            ]
            
            print("🎯 測試波束角度控制...")
            for theta, phi in test_angles:
                if self.interface.set_beam_angle(theta, phi):
                    print(f"✅ 角度設置成功: θ={theta}°, φ={phi}°")
                    time.sleep(0.1)  # 等待設置生效
                else:
                    print(f"❌ 角度設置失敗: θ={theta}°, φ={phi}°")
            
            # 3. 獲取狀態
            status = self.interface.get_status()
            print(f"📊 當前狀態: 模式={status['current_mode']}, "
                  f"角度=({status['current_theta']}, {status['current_phi']})")
            
            return True
            
        except Exception as e:
            print(f"💥 基本控制範例執行失敗: {e}")
            return False
    
    def example_2_power_measurement(self):
        """範例2: 功率測量掃描"""
        print("\n" + "="*50)
        print("📚 範例2: 功率測量掃描")
        print("="*50)
        
        if not self.interface:
            print("❌ 介面未初始化")
            return False
        
        try:
            # 設置RX模式進行功率測量
            print("📡 設置RX模式...")
            if not self.interface.set_bbox_mode("RX"):
                print("❌ RX模式設置失敗")
                return False
            
            # 執行角度掃描
            theta_range = range(-30, 31, 5)  # -30° 到 +30°，步長5°
            phi_values = [0]  # 只測試水平面
            
            print("🔍 開始功率掃描...")
            power_results = {}
            
            for theta in theta_range:
                power = self.interface.measure_power(theta, 0)
                if power is not None:
                    power_results[theta] = power
                    print(f"📊 θ={theta:3d}°: {power:6.2f} dBm")
                else:
                    print(f"⚠️ θ={theta:3d}°: 測量失敗")
                
                time.sleep(0.05)  # 短暫延遲
            
            # 分析結果
            if power_results:
                powers = list(power_results.values())
                max_power = max(powers)
                min_power = min(powers)
                avg_power = np.mean(powers)
                
                print(f"\n📈 掃描結果分析:")
                print(f"   最大功率: {max_power:.2f} dBm")
                print(f"   最小功率: {min_power:.2f} dBm")
                print(f"   平均功率: {avg_power:.2f} dBm")
                print(f"   測量點數: {len(power_results)}")
                
                # 找到最大功率的角度
                max_angle = max(power_results, key=power_results.get)
                print(f"   最佳角度: θ={max_angle}°")
            
            return True
            
        except Exception as e:
            print(f"💥 功率測量範例執行失敗: {e}")
            return False
    
    def example_3_adaptive_scanning(self):
        """範例3: 自適應掃描"""
        print("\n" + "="*50)
        print("📚 範例3: 自適應掃描")
        print("="*50)
        
        if not self.interface:
            print("❌ 介面未初始化")
            return False
        
        try:
            # 設置TX模式
            if not self.interface.set_bbox_mode("TX"):
                print("❌ TX模式設置失敗")
                return False
            
            print("🎯 執行自適應掃描...")
            
            # 第一階段: 粗略掃描
            print("🔍 第一階段: 粗略掃描 (±45°, 步長15°)")
            coarse_angles = [-45, -30, -15, 0, 15, 30, 45]
            coarse_results = {}
            
            for theta in coarse_angles:
                if self.interface.set_beam_angle(theta, 0):
                    print(f"✅ 粗略掃描: θ={theta}°")
                    time.sleep(0.1)
                else:
                    print(f"❌ 粗略掃描失敗: θ={theta}°")
            
            # 第二階段: 精細掃描 (假設最佳角度在0°附近)
            print("🔍 第二階段: 精細掃描 (0°附近, 步長5°)")
            fine_angles = range(-10, 11, 5)
            
            for theta in fine_angles:
                if self.interface.set_beam_angle(theta, 0):
                    print(f"✅ 精細掃描: θ={theta}°")
                    time.sleep(0.1)
                else:
                    print(f"❌ 精細掃描失敗: θ={theta}°")
            
            # 第三階段: 最終定位
            print("🎯 第三階段: 最終定位 (0°)")
            if self.interface.set_beam_angle(0, 0):
                print("✅ 最終定位成功: θ=0°")
            else:
                print("❌ 最終定位失敗")
            
            return True
            
        except Exception as e:
            print(f"💥 自適應掃描範例執行失敗: {e}")
            return False
    
    def example_4_safety_features(self):
        """範例4: 安全功能演示"""
        print("\n" + "="*50)
        print("📚 範例4: 安全功能演示")
        print("="*50)
        
        if not self.interface:
            print("❌ 介面未初始化")
            return False
        
        try:
            # 設置一個非零角度
            print("🎯 設置測試角度...")
            if self.interface.set_beam_angle(25, 0):
                print("✅ 測試角度設置成功: θ=25°")
            else:
                print("❌ 測試角度設置失敗")
                return False
            
            # 獲取當前狀態
            status = self.interface.get_status()
            print(f"📊 當前狀態: θ={status['current_theta']}°, φ={status['current_phi']}°")
            
            # 演示緊急停止
            print("🛑 執行緊急停止...")
            if self.interface.emergency_stop():
                print("✅ 緊急停止執行成功")
                
                # 檢查停止後的狀態
                new_status = self.interface.get_status()
                print(f"📊 停止後狀態: θ={new_status['current_theta']}°, φ={new_status['current_phi']}°")
            else:
                print("❌ 緊急停止執行失敗")
            
            return True
            
        except Exception as e:
            print(f"💥 安全功能範例執行失敗: {e}")
            return False
    
    def example_5_error_handling(self):
        """範例5: 錯誤處理和重試機制"""
        print("\n" + "="*50)
        print("📚 範例5: 錯誤處理和重試機制")
        print("="*50)
        
        if not self.interface:
            print("❌ 介面未初始化")
            return False
        
        try:
            print("🔄 演示錯誤處理和重試機制...")
            
            # 測試超出範圍的角度
            invalid_angles = [
                (50, 0),     # 超出範圍
                (-50, 0),    # 超出範圍
                (0, 90),     # 不支援的phi角度
                (0, 270),    # 不支援的phi角度
            ]
            
            for theta, phi in invalid_angles:
                print(f"🧪 測試無效角度: θ={theta}°, φ={phi}°")
                result = self.interface.set_beam_angle(theta, phi)
                if result:
                    print(f"⚠️ 意外成功: θ={theta}°, φ={phi}°")
                else:
                    print(f"✅ 正確拒絕: θ={theta}°, φ={phi}°")
                
                time.sleep(0.1)
            
            # 測試穩健的角度設置
            print("\n🔄 測試穩健的角度設置...")
            success = self._robust_angle_setting(20, 0, max_retries=3)
            if success:
                print("✅ 穩健角度設置成功")
            else:
                print("❌ 穩健角度設置失敗")
            
            return True
            
        except Exception as e:
            print(f"💥 錯誤處理範例執行失敗: {e}")
            return False
    
    def _robust_angle_setting(self, theta, phi, max_retries=3):
        """穩健的角度設置，包含重試機制"""
        for attempt in range(max_retries):
            try:
                if self.interface.set_beam_angle(theta, phi):
                    print(f"✅ 第{attempt+1}次嘗試成功: θ={theta}°, φ={phi}°")
                    return True
                else:
                    print(f"⚠️ 第{attempt+1}次嘗試失敗")
                    
            except Exception as e:
                print(f"💥 第{attempt+1}次嘗試發生錯誤: {e}")
            
            if attempt < max_retries - 1:
                print(f"⏳ 等待重試... ({attempt+1}/{max_retries})")
                time.sleep(0.5)  # 等待0.5秒後重試
        
        print(f"❌ 角度設置失敗，已重試{max_retries}次")
        return False
    
    def run_all_examples(self):
        """執行所有範例"""
        print("🚀 開始執行所有Beam Control範例...")
        
        examples = [
            ("基本波束控制", self.example_1_basic_control),
            ("功率測量掃描", self.example_2_power_measurement),
            ("自適應掃描", self.example_3_adaptive_scanning),
            ("安全功能演示", self.example_4_safety_features),
            ("錯誤處理機制", self.example_5_error_handling),
        ]
        
        results = {}
        for name, func in examples:
            print(f"\n{'='*20} 執行: {name} {'='*20}")
            try:
                result = func()
                results[name] = result
                if result:
                    print(f"✅ {name} 執行成功")
                else:
                    print(f"❌ {name} 執行失敗")
            except Exception as e:
                print(f"💥 {name} 執行異常: {e}")
                results[name] = False
        
        # 總結結果
        print("\n" + "="*60)
        print("📊 範例執行總結")
        print("="*60)
        
        success_count = sum(1 for result in results.values() if result)
        total_count = len(results)
        
        for name, result in results.items():
            status = "✅ 成功" if result else "❌ 失敗"
            print(f"{name:15s}: {status}")
        
        print(f"\n總體結果: {success_count}/{total_count} 個範例成功")
        
        if success_count == total_count:
            print("🎉 所有範例執行成功！")
        else:
            print("⚠️ 部分範例執行失敗，請檢查錯誤信息")
        
        return results
    
    def cleanup(self):
        """清理資源"""
        if self.interface:
            print("🧹 清理資源...")
            self.interface.cleanup()
            print("✅ 資源清理完成")

def main():
    """主函數"""
    print("🌟 Beam Control 模組使用範例")
    print("="*50)
    
    examples = BeamControlExamples()
    
    try:
        # 設置介面
        if not examples.setup_interface():
            print("❌ 介面設置失敗，無法繼續")
            return
        
        # 執行所有範例
        results = examples.run_all_examples()
        
        # 根據結果決定是否繼續
        if all(results.values()):
            print("\n🎯 所有範例執行成功，系統運行正常！")
        else:
            print("\n⚠️ 部分範例執行失敗，請檢查系統配置")
        
    except KeyboardInterrupt:
        print("\n⏹️ 用戶中斷執行")
    except Exception as e:
        print(f"\n💥 執行過程中發生錯誤: {e}")
    finally:
        examples.cleanup()
        print("\n🏁 範例執行完成")

if __name__ == "__main__":
    main()
