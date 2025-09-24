#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USRP B210 ISAC系統 - 快速啟動腳本
一鍵執行所有演示功能
作者: TMYTEK ISAC Lab
"""

import sys
from pathlib import Path

# 添加scripts目錄到路徑
scripts_dir = Path(__file__).parent / "scripts"
sys.path.append(str(scripts_dir))

def main():
    """主函數"""
    print("🚀 USRP B210 ISAC系統演示")
    print("=" * 50)
    
    try:
        from demo_b210_isac import run_comprehensive_demo
        results = run_comprehensive_demo()
        
        # 根據結果提供建議
        successful = sum(1 for r in results.values() if r['success'])
        total = len(results)
        
        if successful == total:
            print("\n🎉 全部演示成功！系統準備就緒")
            print("下一步: 在Linux環境中執行硬體測試")
            sys.exit(0)
        else:
            print(f"\n⚠️  {successful}/{total} 個演示成功")
            print("請檢查失敗的模組")
            sys.exit(1)
            
    except ImportError as e:
        print(f"❌ 無法載入演示模組: {e}")
        print("請確認所有檔案都在正確位置")
        sys.exit(1)
    except Exception as e:
        print(f"💥 執行時發生錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
