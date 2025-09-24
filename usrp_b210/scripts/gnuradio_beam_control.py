#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GNU Radio整合版Beam Control模組
專門設計用於在GNU Radio flowgraph中使用
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

class GNURadioBeamController:
    """GNU Radio專用Beam控制器 - 簡化版本，專注於實時控制"""
    
    def __init__(self, log_level=logging.WARNING):
        """
        初始化GNU Radio Beam控制器
        
        Args:
            log_level: 日誌級別，預設為WARNING以減少輸出
        """
        # 簡化日誌系統
        self.logger = self._setup_logger(log_level)
        
        # 硬體控制
        self.service = None
        self.bbox_sn = None
        self.pd_sn = None
        
        # 狀態變數
        self.current_mode = None
        self.current_theta = 0
        self.current_phi = 0
        self.gain_max = 15.0
        self.is_initialized = False
        
        # 掃描參數
        self.scan_range = (-45, 45)  # 水平掃描左右各45度
        self.scan_step = 5  # 掃描步長(度)
        self.scan_enabled = False
        self.scan_thread = None
        self.scan_stop_event = threading.Event()
        
        # 通信鎖
        self.comm_lock = threading.Lock()
        
        self.logger.info("GNU Radio Beam控制器初始化完成")
    
    def _setup_logger(self, log_level):
        """設置簡化日誌系統"""
        logger = logging.getLogger('GNURadioBeam')
        logger.setLevel(log_level)
        
        # 只添加控制台輸出，不寫檔案
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(levelname)s: %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        logger.propagate = False
        return logger
