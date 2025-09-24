#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Beam Control Module for USRP B210 ISAC System
整合TMYTEK Beamformer控制功能到ISAC系統
包含智能日誌管理系統，防止日誌過度增長
作者: TMYTEK ISAC Lab
"""

import sys
import time
import threading
import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional, Tuple, Dict, List, Union
import numpy as np

# 添加lib路徑以便導入tlkcore
lib_path = Path(__file__).parent.parent / "lib"
sys.path.insert(0, str(lib_path))

try:
    from tlkcore.TLKCoreService import TLKCoreService
    from tlkcore.TMYPublic import (
        DevInterface, RetCode, RFMode, BeamType, 
        UDState, UDMState, UD_REF, UD_LO_CONFIG
    )
    from tlkcore.TMYBeamConfig import TMYBeamConfig
    TLKCORE_AVAILABLE = True
    print("✅ TMYTEK Beam Control庫導入成功")
except ImportError as e:
    TLKCORE_AVAILABLE = False
    print(f"⚠️ TMYTEK Beam Control庫導入失敗: {e}")
    print("將在模擬模式下運行")

class SmartLogHandler:
    """智能日誌處理器 - 防止日誌過度增長"""
    
    def __init__(self, log_dir: str = "logs", max_file_size: int = 10*1024*1024, 
                 max_files: int = 5, log_level: int = logging.INFO):
        """
        初始化智能日誌處理器
        
        Args:
            log_dir: 日誌目錄
            max_file_size: 單個日誌檔案最大大小 (bytes)
            max_files: 最大日誌檔案數量
            log_level: 日誌級別
        """
        self.log_dir = Path(log_dir)
        self.max_file_size = max_file_size
        self.max_files = max_files
        
        # 創建日誌目錄
        self.log_dir.mkdir(exist_ok=True)
        
        # 設定日誌檔案路徑
        self.log_file = self.log_dir / "beam_control.log"
        
        # 創建日誌處理器
        self.handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=max_file_size,
            backupCount=max_files,
            encoding='utf-8'
        )
        
        # 設定格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.handler.setFormatter(formatter)
        self.handler.setLevel(log_level)
        
        # 創建logger
        self.logger = logging.getLogger('BeamControl')
        self.logger.addHandler(self.handler)
        self.logger.setLevel(log_level)
        
        # 防止日誌重複
        self.logger.propagate = False
        
        # 記錄初始化信息
        self.logger.info("智能日誌系統初始化完成")
        self.logger.info(f"日誌檔案: {self.log_file}")
        self.logger.info(f"最大檔案大小: {max_file_size/1024/1024:.1f}MB")
        self.logger.info(f"最大檔案數量: {max_files}")
    
    def get_logger(self, name: str = None):
        """獲取logger實例"""
        if name:
            return logging.getLogger(f'BeamControl.{name}')
        return self.logger
    
    def cleanup_old_logs(self):
        """清理舊的日誌檔案"""
        try:
            log_files = sorted(self.log_dir.glob("*.log.*"), key=os.path.getctime)
            if len(log_files) > self.max_files:
                # 刪除多餘的舊檔案
                for old_file in log_files[:-self.max_files]:
                    old_file.unlink()
                    self.logger.info(f"清理舊日誌檔案: {old_file}")
        except Exception as e:
            self.logger.error(f"清理日誌檔案失敗: {e}")

class BeamControlError(Exception):
    """Beam控制錯誤"""
    pass

class BeamControlConfig:
    """Beam控制配置類別"""
    
    def __init__(self):
        # 基本參數
        self.target_freq = 28.0  # GHz
        self.scan_range = (-45, 45)  # 掃描範圍 (度) - 水平掃描左右各45度
        self.default_gain = 15.0  # 預設增益
        
        # 日誌配置
        self.log_dir = "logs"
        self.max_log_size = 10 * 1024 * 1024  # 10MB
        self.max_log_files = 5
        
        # 安全參數
        self.max_retries = 3
        self.retry_delay = 0.01
        self.operation_timeout = 5.0

class BeamDeviceManager:
    """Beam設備管理器"""
    
    def __init__(self, config: BeamControlConfig, log_handler: SmartLogHandler):
        self.config = config
        self.log_handler = log_handler
        self.logger = log_handler.get_logger("DeviceManager")
        
        self.service = None
        self.bbox_sn = None
        self.pd_sn = None
        self.ris_sn = None
        self.device_list = []
        self.is_initialized = False
        
        # 設備狀態
        self.device_status = {}
        
    def init_service(self) -> bool:
        """初始化TLKCoreService"""
        try:
            if not TLKCORE_AVAILABLE:
                self.logger.warning("TMYTEK庫不可用，無法初始化硬體服務")
                return False
                
            self.logger.info("初始化TLKCoreService...")
            self.service = TLKCoreService()
            
            if not self.service.running:
                self.logger.error("TLKCoreService啟動失敗")
                return False
                
            version = self.service.queryTLKCoreVer()
            self.logger.info(f"TLKCoreService v{version} 初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"初始化TLKCoreService失敗: {e}")
            return False
    
    def scan_devices(self) -> List[Dict]:
        """掃描連接的設備"""
        if not self.service:
            self.logger.error("服務未初始化")
            return []
            
        try:
            self.logger.info("開始掃描設備...")
            interface = DevInterface.ALL
            
            ret = self.service.scanDevices(interface=interface)
            if not hasattr(ret, 'RetData') or ret.RetCode != RetCode.OK:
                self.logger.error("設備掃描失敗")
                return []
                
            scan_info = self.service.getScanInfo()
            if not hasattr(scan_info, 'RetData'):
                self.logger.error("無法獲取掃描信息")
                return []
                
            scan_dict = scan_info.RetData
            self.device_list = []
            
            for sn, (addr, devtype, in_dfu) in scan_dict.items():
                if in_dfu:
                    self.logger.warning(f"設備 {sn} 在DFU模式，跳過")
                    continue
                    
                # 初始化設備
                init_ret = self.service.initDev(sn)
                if init_ret.RetCode != RetCode.OK:
                    self.logger.warning(f"設備 {sn} 初始化失敗")
                    continue
                    
                # 獲取設備類型
                dev_type_ret = self.service.getDevTypeName(sn)
                dev_type = dev_type_ret.RetData if hasattr(dev_type_ret, 'RetData') else str(dev_type_ret)
                
                device_info = {
                    'sn': sn,
                    'type': dev_type,
                    'address': addr,
                    'devtype': devtype,
                    'in_dfu': in_dfu
                }
                
                self.device_list.append(device_info)
                self.logger.info(f"發現設備: {dev_type} ({sn})")
                
                # 自動分配設備角色
                if "PD" in dev_type:
                    self.pd_sn = sn
                    self.logger.info(f"分配為Power Detector: {sn}")
                elif "BBox" in dev_type:
                    if not self.bbox_sn:
                        self.bbox_sn = sn
                        self.logger.info(f"分配為Beamformer: {sn}")
                elif "RIS" in dev_type:
                    self.ris_sn = sn
                    self.logger.info(f"分配為RIS: {sn}")
            
            self.logger.info(f"設備掃描完成，發現 {len(self.device_list)} 個設備")
            return self.device_list
            
        except Exception as e:
            self.logger.error(f"設備掃描失敗: {e}")
            return []
    
    def setup_bbox_device(self, sn: str, mode: RFMode) -> Optional[float]:
        """設置BBox設備"""
        try:
            self.logger.info(f"設置BBox設備 {sn}...")
            
            # 1. 設置RF模式
            ret = self.service.setRFMode(sn, mode)
            if ret.RetCode != RetCode.OK:
                self.logger.error(f"設置RF模式失敗: {ret.RetMsg}")
                return None
                
            # 2. 獲取頻率列表
            freq_ret = self.service.getFrequencyList(sn)
            if not hasattr(freq_ret, 'RetData') or not freq_ret.RetData:
                self.logger.error(f"無法獲取頻率列表: {sn}")
                return None
                
            freq_list = freq_ret.RetData
            self.logger.info(f"可用頻率: {freq_list}")
            
            # 3. 設置工作頻率
            target_freq = self.config.target_freq
            if target_freq not in freq_list:
                self.logger.warning(f"目標頻率 {target_freq} 不支援，使用第一個可用頻率")
                target_freq = freq_list[0]
                
            ret = self.service.setOperatingFreq(sn, target_freq)
            if ret.RetCode != RetCode.OK:
                self.logger.error(f"設置頻率失敗: {ret.RetMsg}")
                return None
                
            self.logger.info(f"頻率設置成功: {target_freq} GHz")
            
            # 4. 載入校準檔案
            try:
                cali_ver = self.service.queryCaliTableVer(sn)
                if hasattr(cali_ver, 'RetData'):
                    self.logger.info(f"校準版本: {cali_ver.RetData}")
                else:
                    self.logger.warning("無法獲取校準版本")
            except Exception as e:
                self.logger.warning(f"校準版本查詢失敗: {e}")
            
            # 5. 獲取增益範圍
            rng_ret = self.service.getDR(sn, mode)
            if rng_ret.RetCode != RetCode.OK:
                self.logger.error(f"獲取增益範圍失敗: {rng_ret.RetMsg}")
                return None
                
            rng = rng_ret.RetData
            self.logger.info(f"增益範圍: {rng}")
            
            # 6. 選擇AAKit
            aakit_selected = False
            try:
                aakit_ret = self.service.getAAKitList(sn)
                if hasattr(aakit_ret, 'RetData') and aakit_ret.RetData:
                    aakit_list = aakit_ret.RetData
                    for aakit in aakit_list:
                        if '4x4' in aakit:
                            aakit_result = self.service.selectAAKit(sn, aakit)
                            if hasattr(aakit_result, 'name'):
                                self.logger.info(f"選擇AAKit: {aakit}")
                                aakit_selected = True
                                break
                                
                if not aakit_selected:
                    self.logger.warning("使用PhiA模式")
                    
            except Exception as e:
                self.logger.warning(f"AAKit選擇失敗: {e}")
            
            # 7. 返回最大增益
            gain_max = rng[1] if len(rng) > 1 else self.config.default_gain
            self.logger.info(f"BBox設備 {sn} 設置完成，最大增益: {gain_max}")
            
            # 更新設備狀態
            self.device_status[sn] = {
                'type': 'BBox',
                'mode': mode.name,
                'frequency': target_freq,
                'gain_max': gain_max,
                'aakit_selected': aakit_selected,
                'status': 'ready'
            }
            
            return gain_max
            
        except Exception as e:
            self.logger.error(f"設置BBox設備失敗: {e}")
            return None
    
    def setup_power_detector(self, sn: str) -> bool:
        """設置Power Detector"""
        try:
            self.logger.info(f"設置Power Detector {sn}...")
            
            # 這裡可以添加PD校準邏輯
            # 目前簡化處理
            self.logger.info(f"Power Detector {sn} 設置完成")
            
            # 更新設備狀態
            self.device_status[sn] = {
                'type': 'PowerDetector',
                'status': 'ready'
            }
            
            return True
            
        except Exception as e:
            self.logger.error(f"設置Power Detector失敗: {e}")
            return False

class ISACBeamInterface:
    """ISAC-Beam整合介面 - 主要對外介面"""
    
    def __init__(self, config: Optional[BeamControlConfig] = None):
        self.config = config or BeamControlConfig()
        
        # 初始化日誌系統
        self.log_handler = SmartLogHandler(
            log_dir=self.config.log_dir,
            max_file_size=self.config.max_log_size,
            max_files=self.config.max_log_files
        )
        self.logger = self.log_handler.get_logger("Main")
        
        # 初始化設備管理器
        self.device_manager = BeamDeviceManager(self.config, self.log_handler)
        
        # 狀態變數
        self.current_mode = None  # TX/RX/STANDBY
        self.current_theta = 0
        self.current_phi = 0
        self.gain_max = None
        self.is_initialized = False
        
        # 通信鎖
        self.comm_lock = threading.Lock()
        
        self.logger.info("ISAC-Beam整合介面初始化完成")
        
    def initialize(self) -> bool:
        """初始化整個系統"""
        try:
            self.logger.info("開始初始化ISAC-Beam整合系統...")
            
            # 1. 初始化服務
            if not self.device_manager.init_service():
                self.logger.error("服務初始化失敗")
                return False
                
            # 2. 掃描設備
            devices = self.device_manager.scan_devices()
            if not devices:
                self.logger.error("未發現設備")
                return False
                
            # 3. 設置BBox設備
            if self.device_manager.bbox_sn:
                gain_max = self.device_manager.setup_bbox_device(
                    self.device_manager.bbox_sn, 
                    RFMode.TX
                )
                if gain_max is None:
                    self.logger.error("BBox設備設置失敗")
                    return False
                self.gain_max = gain_max
            else:
                self.logger.warning("未發現BBox設備，將在模擬模式下運行")
                self.gain_max = self.config.default_gain
                
            # 4. 設置Power Detector
            if self.device_manager.pd_sn:
                if not self.device_manager.setup_power_detector(self.device_manager.pd_sn):
                    self.logger.error("Power Detector設置失敗")
                    return False
            else:
                self.logger.warning("未發現Power Detector設備")
                
            # 5. 驗證配置
            if not self._validate_configuration():
                self.logger.error("配置驗證失敗")
                return False
                
            self.is_initialized = True
            self.logger.info("ISAC-Beam整合系統初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"系統初始化失敗: {e}")
            return False
    
    def _validate_configuration(self) -> bool:
        """驗證配置是否正確"""
        try:
            checks = []
            
            # 檢查頻率設定
            if self.device_manager.bbox_sn:
                current_freq = self.device_manager.service.getOperatingFreq(self.device_manager.bbox_sn)
                if hasattr(current_freq, 'RetData'):
                    freq = current_freq.RetData
                    checks.append(abs(freq - self.config.target_freq) < 0.1)
                    self.logger.info(f"頻率驗證: 目標={self.config.target_freq}GHz, 實際={freq}GHz")
            
            # 檢查設備通信
            if self.device_manager.bbox_sn:
                try:
                    mac = self.device_manager.service.queryMAC(self.device_manager.bbox_sn)
                    checks.append(mac is not None)
                    self.logger.info("設備通信驗證通過")
                except:
                    checks.append(False)
                    self.logger.error("設備通信驗證失敗")
            
            # 檢查校準檔案
            if self.device_manager.bbox_sn:
                try:
                    cali_ver = self.device_manager.service.queryCaliTableVer(self.device_manager.bbox_sn)
                    checks.append(cali_ver is not None)
                    self.logger.info("校準檔案驗證通過")
                except:
                    checks.append(False)
                    self.logger.error("校準檔案驗證失敗")
            
            return all(checks) if checks else False
            
        except Exception as e:
            self.logger.error(f"配置驗證過程中發生錯誤: {e}")
            return False
    
    def set_bbox_mode(self, mode: str) -> bool:
        """設置BBox模式 (TX/RX)"""
        if not self.is_initialized or not self.device_manager.bbox_sn:
            self.logger.error("系統未初始化或BBox設備不可用")
            return False
            
        try:
            if mode.upper() == "TX":
                rf_mode = RFMode.TX
            elif mode.upper() == "RX":
                rf_mode = RFMode.RX
            else:
                self.logger.error(f"不支援的模式: {mode}")
                return False
                
            with self.comm_lock:
                ret = self.device_manager.service.setRFMode(self.device_manager.bbox_sn, rf_mode)
                if ret.RetCode != RetCode.OK:
                    self.logger.error(f"設置RF模式失敗: {ret.RetMsg}")
                    return False
                    
                self.current_mode = mode.upper()
                self.logger.info(f"BBox模式設置為: {mode}")
                
                # 更新設備狀態
                if self.device_manager.bbox_sn in self.device_manager.device_status:
                    self.device_manager.device_status[self.device_manager.bbox_sn]['mode'] = mode.upper()
                
                return True
                
        except Exception as e:
            self.logger.error(f"設置BBox模式失敗: {e}")
            return False
    
    def set_beam_angle(self, theta: float, phi: float) -> bool:
        """設定波束角度"""
        if not self.is_initialized or not self.device_manager.bbox_sn:
            self.logger.error("系統未初始化或BBox設備不可用")
            return False
            
        try:
            # 角度範圍檢查
            if not (self.config.scan_range[0] <= theta <= self.config.scan_range[1]):
                self.logger.error(f"角度 {theta} 超出範圍 {self.config.scan_range}")
                return False
                
            if phi not in [0, 180]:
                self.logger.error(f"Phi角度 {phi} 不支援，支援的角度: [0, 180]")
                return False
            
            # 設置波束角度
            with self.comm_lock:
                ret = self.device_manager.service.setBeamAngle(
                    self.device_manager.bbox_sn, 
                    self.gain_max, 
                    theta, phi
                )
                
                if ret.RetCode != RetCode.OK:
                    self.logger.error(f"設置波束角度失敗: {ret.RetMsg}")
                    return False
                    
                self.current_theta = theta
                self.current_phi = phi
                self.logger.info(f"波束角度設置成功: θ={theta}°, φ={phi}°")
                return True
                
        except Exception as e:
            self.logger.error(f"設置波束角度時發生錯誤: {e}")
            return False
    
    def measure_power(self, theta: float, phi: float) -> Optional[float]:
        """測量功率"""
        if not self.is_initialized or not self.device_manager.pd_sn:
            self.logger.error("系統未初始化或Power Detector設備不可用")
            return None
            
        try:
            # 先設置波束角度
            if not self.set_beam_angle(theta, phi):
                return None
                
            # 等待角度設置生效
            time.sleep(0.01)
            
            # 測量功率
            with self.comm_lock:
                power_ret = self.device_manager.service.getPowerValue(
                    self.device_manager.pd_sn, 
                    int(self.config.target_freq)
                )
                
                if not power_ret or power_ret.RetCode != RetCode.OK:
                    self.logger.error(f"功率測量失敗: {power_ret.RetMsg if hasattr(power_ret, 'RetMsg') else 'Unknown error'}")
                    return None
                    
                if not hasattr(power_ret, 'RetData'):
                    self.logger.error("功率返回值無效")
                    return None
                    
                power = power_ret.RetData
                self.logger.debug(f"功率測量: θ={theta}°, φ={phi}°, Power={power} dBm")
                return power
                
        except Exception as e:
            self.logger.error(f"功率測量時發生錯誤: {e}")
            return None
    
    def get_status(self) -> Dict:
        """獲取系統狀態"""
        status = {
            'initialized': self.is_initialized,
            'current_mode': self.current_mode,
            'current_theta': self.current_theta,
            'current_phi': self.current_phi,
            'bbox_available': self.device_manager.bbox_sn is not None,
            'pd_available': self.device_manager.pd_sn is not None,
            'ris_available': self.device_manager.ris_sn is not None,
            'device_status': self.device_manager.device_status,
            'gain_max': self.gain_max
        }
        return status
    
    def emergency_stop(self) -> bool:
        """緊急停止 - 將波束設為安全角度"""
        try:
            self.logger.warning("執行緊急停止程序")
            return self.set_beam_angle(0, 0)  # 設為0度
        except Exception as e:
            self.logger.error(f"緊急停止失敗: {e}")
            return False
    
    def cleanup(self):
        """清理資源"""
        try:
            if self.is_initialized:
                self.emergency_stop()
                
            # 清理日誌
            self.log_handler.cleanup_old_logs()
            
            self.is_initialized = False
            self.logger.info("ISAC-Beam整合系統已清理")
            
        except Exception as e:
            self.logger.error(f"清理過程中發生錯誤: {e}")

# 便捷函數
def create_isac_beam_interface(config: Optional[BeamControlConfig] = None) -> ISACBeamInterface:
    """創建ISAC-Beam整合介面"""
    return ISACBeamInterface(config)

def test_beam_control():
    """測試Beam控制功能"""
    print("🧪 測試Beam控制功能...")
    
    # 創建介面
    interface = create_isac_beam_interface()
    
    try:
        # 初始化
        if interface.initialize():
            print("✅ 系統初始化成功")
            
            # 獲取狀態
            status = interface.get_status()
            print(f"📊 系統狀態: {status}")
            
            # 測試基本功能
            if interface.set_bbox_mode("TX"):
                print("✅ BBox模式設置成功")
                
                if interface.set_beam_angle(0, 0):
                    print("✅ 波束角度設置成功")
                    
                    power = interface.measure_power(0, 0)
                    if power is not None:
                        print(f"✅ 功率測量成功: {power} dBm")
                    else:
                        print("⚠️ 功率測量失敗")
                else:
                    print("❌ 波束角度設置失敗")
            else:
                print("❌ BBox模式設置失敗")
                
        else:
            print("❌ 系統初始化失敗")
            
    except Exception as e:
        print(f"💥 測試過程中發生錯誤: {e}")
        
    finally:
        interface.cleanup()
        print("🧹 測試完成，資源已清理")

if __name__ == "__main__":
    test_beam_control()
