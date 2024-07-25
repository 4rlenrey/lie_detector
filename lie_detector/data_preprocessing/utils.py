import numpy as np
from pykalman import KalmanFilter
from scipy.signal import butter, filtfilt

from lie_detector.data_preprocessing.constants import A, B, END_TIME, START_TIME


def bjs_filter(signal, cutoff_freq, sampling_freq, filter_order=2):
    nyquist_freq = 0.5 * sampling_freq
    normalized_cutoff = cutoff_freq / nyquist_freq
    b, a = butter(filter_order, normalized_cutoff, btype="low")
    filtered_signal = filtfilt(b, a, signal)
    return filtered_signal


def calculate_SpO2(red_count, ir_count):
    red_ac = red_count.max() - red_count.min()
    ir_ac = ir_count.max() - ir_count.min()

    # red_dc is red_count.min()? I guess it's the lowland of the signal
    R = np.mean(red_ac / red_count.min()) / np.mean(ir_ac / ir_count.min())
    SpO2 = 110 - R * 25
    return SpO2, R


def butter_lowpass_filter(data, cutoff_freq, fs, order=4):
    nyquist = 0.5 * fs
    normal_cutoff = cutoff_freq / nyquist
    b, a = butter(order, normal_cutoff, btype="low", analog=False)
    y = filtfilt(b, a, data)
    return y


def calculate_ppg(red_data, ir_data):
    ppg_data = red_data - ir_data
    b, a = butter(4, 0.5, "low")
    ppg_data_filtered = filtfilt(b, a, ppg_data)
    return ppg_data_filtered


def baseline_correction(signal, timestamps, degree=3):
    p = np.polyfit(timestamps, signal, degree)
    baseline = np.polyval(p, timestamps)
    corrected_signal = signal - baseline
    return corrected_signal


def notch_filter(signal, freq, fs, Q=30):
    # Notch filter to remove power line interference at freq Hz
    nyquist = 0.5 * fs
    normal_freq = freq / nyquist
    b, a = butter(4, [normal_freq - 1 / (2 * Q), normal_freq + 1 / (2 * Q)], btype="bandstop", analog=False)
    filtered_signal = filtfilt(b, a, signal)
    return filtered_signal


def kalman_filter(signal):
    # Apply Kalman filter to the signal
    kf = KalmanFilter(initial_state_mean=0, n_dim_obs=1)
    filtered_state_means, _ = kf.filter(signal)
    return filtered_state_means.flatten()


def find_first_consistent_idx(timestamps):
    # Find the index where timestamps become consistent
    for i in range(len(timestamps) - 1):
        if timestamps[i + 1] <= timestamps[i]:
            return i + 1
    return 0  # If all timestamps are consistently increasing


def clip_values(ppg_data):
    Q1 = np.percentile(ppg_data, 25)
    Q3 = np.percentile(ppg_data, 75)

    # Calculate IQR (Interquartile Range)
    IQR = Q3 - Q1

    # Determine thresholds based on IQR
    lower_threshold = Q1 - 1.5 * IQR
    upper_threshold = Q3 + 1.5 * IQR

    # Clip PPG data to determined thresholds
    ppg_data = np.clip(ppg_data, lower_threshold, upper_threshold)
    return ppg_data


def calculate_ac_dc(signal):
    dc_component = np.mean(signal)
    ac_component = signal - dc_component
    return ac_component, dc_component


def calculate_ratio_of_ratios(ac_red, dc_red, ac_ir, dc_ir):
    ratio = (ac_red / dc_red) / (ac_ir / dc_ir)
    return ratio


def convert_ratio_to_spo2(ratio):
    spo2 = A - B * ratio
    return spo2


def calculate_bpm(peaks, timestamps):
    peak_intervals = np.diff(timestamps[peaks])
    bpm = 60 / peak_intervals
    bpm_timestamps = timestamps[peaks][1:]  # Skip the first timestamp for diff
    return bpm, bpm_timestamps


def fix_timestamps(timestamps, red_data, ir_data, gsr_data):
    timestamps = timestamps / 1000  # In milis

    first_consistent_idx = find_first_consistent_idx(timestamps)

    timestamps = timestamps[first_consistent_idx:]
    red_data = red_data[first_consistent_idx:]
    ir_data = ir_data[first_consistent_idx:]
    gsr_data = gsr_data[first_consistent_idx:]

    timestamps = timestamps - timestamps[0]

    start_idx = np.argmin(np.abs(timestamps - START_TIME))
    end_idx = np.argmin(np.abs(timestamps - END_TIME))

    if start_idx > end_idx:
        start_idx, end_idx = end_idx, start_idx

    return (
        timestamps[start_idx:end_idx],
        red_data[start_idx:end_idx],
        ir_data[start_idx:end_idx],
        gsr_data[start_idx:end_idx],
    )

