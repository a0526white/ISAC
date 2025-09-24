#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chirp信號產生器模組
支援多種Chirp調變方式，針對B210 ISAC系統優化
兼容Linux/Windows環境
作者: TMYTEK ISAC Lab
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import json
import time

# 添加config路徑以便導入
import sys
sys.path.append(str(Path(__file__).parent.parent / "config"))

try:
    from hardware_verified_config import get_config
    CONFIG = get_config()
except ImportError:
    # 如果無法導入新配置，嘗試舊配置
    try:
        from b210_config import get_config
        CONFIG = get_config()
    except ImportError:
        # 如果都無法導入，使用預設值
        class DefaultConfig:
            def __init__(self):
                self.sample_rate = 30e6
                self.chirp_duration = 100e-6
                self.chirp_bandwidth = 20e6
        
        CONFIG = DefaultConfig()

class ChirpGenerator:
    """Chirp信號產生器類別"""
    
    def __init__(self, config=None):
        self.config = config or CONFIG
        self.signal_cache = {}  # 信號快取
        
    def generate_linear_chirp(self, duration=None, bandwidth=None, 
                            start_freq=0, sample_rate=None, direction="up"):
        """
        產生線性調頻Chirp信號
        
        Parameters:
        -----------
        duration : float
            Chirp持續時間 (秒)
        bandwidth : float  
            掃頻頻寬 (Hz)
        start_freq : float
            起始頻率 (Hz, 相對於載波)
        sample_rate : float
            取樣率 (Hz)
        direction : str
            "up" 為上行chirp, "down" 為下行chirp
            
        Returns:
        --------
        dict : 包含信號和參數的字典
        """
        # 使用預設值
        duration = duration or self.config.chirp_duration
        bandwidth = bandwidth or self.config.chirp_bandwidth
        sample_rate = sample_rate or self.config.sample_rate
        
        # 產生時間軸
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples, endpoint=False)
        
        # 計算頻率參數
        if direction == "up":
            stop_freq = start_freq + bandwidth
            k = bandwidth / duration  # 正斜率
        else:  # down
            stop_freq = start_freq - bandwidth
            k = -bandwidth / duration  # 負斜率
        
        # 瞬時頻率: f(t) = start_freq + k*t
        instantaneous_freq = start_freq + k * t
        
        # 相位積分: φ(t) = 2π∫f(t)dt = 2π(start_freq*t + 0.5*k*t²)
        phase = 2 * np.pi * (start_freq * t + 0.5 * k * t**2)
        
        # 複數信號
        signal = np.exp(1j * phase)
        
        # 添加窗函數以減少頻譜洩漏
        window = np.hanning(samples)
        windowed_signal = signal * window
        
        return {
            'signal': signal,
            'windowed_signal': windowed_signal,
            'time': t,
            'instantaneous_freq': instantaneous_freq,
            'parameters': {
                'duration': duration,
                'bandwidth': bandwidth,
                'start_freq': start_freq,
                'stop_freq': stop_freq,
                'sample_rate': sample_rate,
                'samples': samples,
                'chirp_rate': k,
                'direction': direction
            }
        }
    
    def generate_nonlinear_chirp(self, duration=None, bandwidth=None,
                                chirp_type="quadratic", alpha=2.0):
        """
        產生非線性調頻Chirp信號
        
        Parameters:
        -----------
        chirp_type : str
            "quadratic", "logarithmic", "exponential"
        alpha : float
            非線性參數
        """
        duration = duration or self.config.chirp_duration
        bandwidth = bandwidth or self.config.chirp_bandwidth
        sample_rate = self.config.sample_rate
        
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples, endpoint=False)
        
        if chirp_type == "quadratic":
            # 二次chirp: f(t) = f0 + k*t²
            k = bandwidth / (duration ** alpha)
            instantaneous_freq = k * (t ** alpha)
            phase = 2 * np.pi * k * (t ** (alpha + 1)) / (alpha + 1)
            
        elif chirp_type == "logarithmic":
            # 對數chirp: f(t) = f0 + k*log(1 + α*t)
            k = bandwidth / np.log(1 + alpha * duration)
            instantaneous_freq = k * np.log(1 + alpha * t)
            phase = 2 * np.pi * k * ((1 + alpha * t) * np.log(1 + alpha * t) - alpha * t) / alpha
            
        elif chirp_type == "exponential":
            # 指數chirp: f(t) = f0 + k*(e^(α*t) - 1)
            k = bandwidth / (np.exp(alpha * duration) - 1)
            instantaneous_freq = k * (np.exp(alpha * t) - 1)
            phase = 2 * np.pi * k * (np.exp(alpha * t) / alpha - t)
            
        else:
            raise ValueError(f"不支援的chirp類型: {chirp_type}")
        
        signal = np.exp(1j * phase)
        
        return {
            'signal': signal,
            'time': t,
            'instantaneous_freq': instantaneous_freq,
            'parameters': {
                'type': chirp_type,
                'duration': duration,
                'bandwidth': bandwidth,
                'alpha': alpha,
                'samples': samples
            }
        }
    
    def generate_multi_chirp(self, num_chirps=4, spacing="equal"):
        """
        產生多重Chirp信號組合
        
        Parameters:
        -----------
        num_chirps : int
            Chirp數量
        spacing : str
            "equal" 等間距, "random" 隨機間距
        """
        total_bandwidth = self.config.chirp_bandwidth
        chirp_bandwidth = total_bandwidth / num_chirps
        
        signals = []
        for i in range(num_chirps):
            if spacing == "equal":
                start_freq = i * chirp_bandwidth - total_bandwidth/2
            else:  # random
                start_freq = np.random.uniform(-total_bandwidth/2, total_bandwidth/2)
            
            chirp = self.generate_linear_chirp(
                start_freq=start_freq,
                bandwidth=chirp_bandwidth,
                direction="up" if i % 2 == 0 else "down"
            )
            signals.append(chirp)
        
        # 組合信號
        combined_signal = np.zeros_like(signals[0]['signal'])
        for sig in signals:
            combined_signal += sig['signal']
        
        return {
            'combined_signal': combined_signal,
            'individual_signals': signals,
            'parameters': {
                'num_chirps': num_chirps,
                'individual_bandwidth': chirp_bandwidth,
                'total_bandwidth': total_bandwidth,
                'spacing': spacing
            }
        }
    
    def encode_data_in_chirp(self, data_bits, encoding="direction"):
        """
        將數據編碼到Chirp參數中
        
        Parameters:
        -----------
        data_bits : list or np.array
            要編碼的數據位元 (0或1)
        encoding : str
            編碼方式: "direction", "frequency", "phase", "duration"
        """
        encoded_signals = []
        
        for bit in data_bits:
            if encoding == "direction":
                # 方向編碼: 0=上行, 1=下行
                direction = "up" if bit == 0 else "down"
                chirp = self.generate_linear_chirp(direction=direction)
                
            elif encoding == "frequency":
                # 頻率編碼: 0=低頻, 1=高頻
                start_freq = 0 if bit == 0 else self.config.chirp_bandwidth/2
                chirp = self.generate_linear_chirp(start_freq=start_freq)
                
            elif encoding == "phase":
                # 相位編碼: 0=0°, 1=180°
                chirp = self.generate_linear_chirp()
                phase_shift = 0 if bit == 0 else np.pi
                chirp['signal'] *= np.exp(1j * phase_shift)
                
            elif encoding == "duration":
                # 持續時間編碼: 0=短, 1=長
                duration = self.config.chirp_duration if bit == 0 else self.config.chirp_duration * 1.5
                chirp = self.generate_linear_chirp(duration=duration)
                
            else:
                raise ValueError(f"不支援的編碼方式: {encoding}")
            
            encoded_signals.append(chirp)
        
        return {
            'encoded_signals': encoded_signals,
            'data_bits': data_bits,
            'encoding_type': encoding,
            'bit_rate': len(data_bits) / (len(data_bits) * self.config.chirp_duration)
        }
    
    def add_noise(self, signal, snr_db=20):
        """
        添加高斯白雜訊
        
        Parameters:
        -----------
        signal : np.array
            原始信號
        snr_db : float
            信號雜訊比 (dB)
        """
        signal_power = np.mean(np.abs(signal) ** 2)
        noise_power = signal_power / (10 ** (snr_db / 10))
        
        # 產生複數高斯雜訊
        noise_real = np.random.normal(0, np.sqrt(noise_power/2), len(signal))
        noise_imag = np.random.normal(0, np.sqrt(noise_power/2), len(signal))
        noise = noise_real + 1j * noise_imag
        
        noisy_signal = signal + noise
        
        return {
            'noisy_signal': noisy_signal,
            'noise': noise,
            'snr_db': snr_db,
            'signal_power': signal_power,
            'noise_power': noise_power
        }
    
    def analyze_chirp(self, chirp_data, plot=False):
        """
        分析Chirp信號特性
        
        Parameters:
        -----------
        chirp_data : dict
            generate_*_chirp()的回傳值
        plot : bool
            是否繪製分析圖
        """
        signal = chirp_data['signal']
        time = chirp_data['time']
        params = chirp_data['parameters']
        
        # 時域分析
        time_analysis = {
            'duration': time[-1] - time[0],
            'samples': len(signal),
            'amplitude_max': np.max(np.abs(signal)),
            'amplitude_mean': np.mean(np.abs(signal)),
            'power': np.mean(np.abs(signal) ** 2)
        }
        
        # 頻域分析
        fft_signal = np.fft.fft(signal)
        freqs = np.fft.fftfreq(len(signal), 1/params['sample_rate'])
        
        freq_analysis = {
            'peak_freq': freqs[np.argmax(np.abs(fft_signal))],
            'bandwidth_3db': self._measure_bandwidth(freqs, np.abs(fft_signal)),
            'spectral_centroid': np.sum(freqs * np.abs(fft_signal)) / np.sum(np.abs(fft_signal))
        }
        
        # 時頻分析 (簡化版)
        spectrogram = self._compute_spectrogram(signal, params['sample_rate'])
        
        analysis = {
            'time_domain': time_analysis,
            'frequency_domain': freq_analysis,
            'spectrogram': spectrogram,
            'parameters': params
        }
        
        if plot:
            self._plot_chirp_analysis(chirp_data, analysis)
        
        return analysis
    
    def _measure_bandwidth(self, freqs, spectrum):
        """測量3dB頻寬"""
        peak_power = np.max(spectrum)
        half_power = peak_power / np.sqrt(2)  # -3dB
        
        # 找到半功率點
        indices = np.where(spectrum >= half_power)[0]
        if len(indices) > 0:
            return freqs[indices[-1]] - freqs[indices[0]]
        else:
            return 0
    
    def _compute_spectrogram(self, signal, sample_rate, nperseg=256):
        """計算頻譜圖"""
        from scipy import signal as scipy_signal
        
        try:
            f, t, Sxx = scipy_signal.spectrogram(signal, sample_rate, nperseg=nperseg)
            return {'frequencies': f, 'times': t, 'spectrogram': Sxx}
        except ImportError:
            # 如果沒有scipy，使用簡化版本
            return {'frequencies': [], 'times': [], 'spectrogram': []}
    
    def _plot_chirp_analysis(self, chirp_data, analysis):
        """繪製Chirp分析圖"""
        signal = chirp_data['signal']
        time = chirp_data['time']
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        
        # 時域波形
        axes[0, 0].plot(time * 1e6, np.real(signal), label='Real')
        axes[0, 0].plot(time * 1e6, np.imag(signal), label='Imag')
        axes[0, 0].set_xlabel('時間 (μs)')
        axes[0, 0].set_ylabel('振幅')
        axes[0, 0].set_title('時域波形')
        axes[0, 0].legend()
        axes[0, 0].grid(True)
        
        # 振幅頻譜
        fft_signal = np.fft.fft(signal)
        freqs = np.fft.fftfreq(len(signal), 1/chirp_data['parameters']['sample_rate'])
        axes[0, 1].plot(freqs/1e6, 20*np.log10(np.abs(fft_signal)))
        axes[0, 1].set_xlabel('頻率 (MHz)')
        axes[0, 1].set_ylabel('幅度 (dB)')
        axes[0, 1].set_title('頻域頻譜')
        axes[0, 1].grid(True)
        
        # 瞬時頻率
        if 'instantaneous_freq' in chirp_data:
            axes[1, 0].plot(time * 1e6, chirp_data['instantaneous_freq']/1e6)
            axes[1, 0].set_xlabel('時間 (μs)')
            axes[1, 0].set_ylabel('頻率 (MHz)')
            axes[1, 0].set_title('瞬時頻率')
            axes[1, 0].grid(True)
        
        # 相位
        phase = np.angle(signal)
        axes[1, 1].plot(time * 1e6, np.unwrap(phase))
        axes[1, 1].set_xlabel('時間 (μs)')
        axes[1, 1].set_ylabel('相位 (rad)')
        axes[1, 1].set_title('瞬時相位')
        axes[1, 1].grid(True)
        
        plt.tight_layout()
        plt.show()
    
    def save_signal(self, signal_data, filename=None, format="npy"):
        """
        儲存信號到檔案
        
        Parameters:
        -----------
        signal_data : dict
            信號數據
        filename : str
            檔案名稱
        format : str
            "npy", "wav", "mat", "json"
        """
        if filename is None:
            timestamp = int(time.time())
            filename = f"chirp_signal_{timestamp}"
        
        # 確保data目錄存在
        data_dir = Path(__file__).parent.parent / "data"
        data_dir.mkdir(exist_ok=True)
        
        filepath = data_dir / f"{filename}.{format}"
        
        if format == "npy":
            np.save(filepath, signal_data['signal'])
            
        elif format == "json":
            # 轉換為可序列化的格式
            serializable_data = {}
            for key, value in signal_data.items():
                if isinstance(value, np.ndarray):
                    serializable_data[key] = {
                        'real': value.real.tolist(),
                        'imag': value.imag.tolist() if np.iscomplexobj(value) else None
                    }
                else:
                    serializable_data[key] = value
            
            with open(filepath, 'w') as f:
                json.dump(serializable_data, f, indent=2)
        
        elif format == "mat":
            try:
                from scipy.io import savemat
                savemat(filepath, signal_data)
            except ImportError:
                print("需要scipy來儲存.mat檔案")
                return None
        
        print(f"信號已儲存至: {filepath}")
        return filepath

def demo_chirp_generator():
    """演示Chirp產生器功能"""
    print("=== Chirp信號產生器演示 ===")
    
    generator = ChirpGenerator()
    
    # 1. 基本線性Chirp
    print("\n1. 產生線性Chirp信號...")
    linear_chirp = generator.generate_linear_chirp()
    print(f"   信號長度: {len(linear_chirp['signal'])} 樣本")
    print(f"   持續時間: {linear_chirp['parameters']['duration']*1e6:.1f} μs")
    print(f"   頻寬: {linear_chirp['parameters']['bandwidth']/1e6:.1f} MHz")
    
    # 2. 數據編碼
    print("\n2. 數據編碼演示...")
    data_bits = [1, 0, 1, 1, 0]
    encoded = generator.encode_data_in_chirp(data_bits, encoding="direction")
    print(f"   編碼位元: {data_bits}")
    print(f"   信號數量: {len(encoded['encoded_signals'])}")
    print(f"   位元率: {encoded['bit_rate']/1e3:.1f} kbps")
    
    # 3. 信號分析
    print("\n3. 信號分析...")
    analysis = generator.analyze_chirp(linear_chirp)
    print(f"   信號功率: {analysis['time_domain']['power']:.3f}")
    print(f"   峰值頻率: {analysis['frequency_domain']['peak_freq']/1e6:.1f} MHz")
    
    # 4. 儲存信號
    print("\n4. 儲存信號...")
    filepath = generator.save_signal(linear_chirp, "demo_chirp", "json")
    print(f"   檔案路徑: {filepath}")
    
    print("\n演示完成！")

if __name__ == "__main__":
    demo_chirp_generator()

