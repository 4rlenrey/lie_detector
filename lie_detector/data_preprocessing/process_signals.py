import glob
import os

import numpy as np
import pandas as pd
from scipy.signal import find_peaks, medfilt

from lie_detector.data_preprocessing.constants import CUTOFF_FREQ, END_TIME, START_TIME
from lie_detector.data_preprocessing.plot_signals import plot_signals
from lie_detector.data_preprocessing.utils import (
    baseline_correction,
    bjs_filter,
    butter_lowpass_filter,
    calculate_ac_dc,
    calculate_bpm,
    calculate_ppg,
    calculate_ratio_of_ratios,
    clip_values,
    convert_ratio_to_spo2,
    fix_timestamps,
    kalman_filter,
)


def process_signal(data_path: str, output_dir: str, plot_dir: str):
    # Read CSV data
    data = pd.read_csv(data_path, header=None)

    # Extract columns and fix timestamps
    timestamps, red_data, ir_data, gsr_data = fix_timestamps(
        data.iloc[:, 0].to_numpy(), data.iloc[:, 1].to_numpy(), data.iloc[:, 2].to_numpy(), data.iloc[:, 3].to_numpy()
    )

    # Calculate sampling frequency
    sampling_frequency = 1 / np.mean(np.diff(timestamps))

    # Normalize GSR data
    gsr_data = (gsr_data - np.min(gsr_data)) / (np.max(gsr_data) - np.min(gsr_data))

    # Calculate and process PPG from red and IR data
    ppg_data = calculate_ppg(red_data, ir_data)
    ppg_data = baseline_correction(ppg_data, timestamps)
    ppg_data = medfilt(ppg_data, kernel_size=3)
    # ppg_data = notch_filter(ppg_data, freq=50, fs=sampling_frequency)
    ppg_data = kalman_filter(ppg_data)
    ppg_data = butter_lowpass_filter(ppg_data, CUTOFF_FREQ, sampling_frequency)
    ppg_data = clip_values(ppg_data)

    gsr_data = bjs_filter(gsr_data, cutoff_freq=CUTOFF_FREQ, sampling_freq=sampling_frequency)

    # Find peaks in PPG signal
    peaks, _ = find_peaks(ppg_data, height=0.5 * np.max(ppg_data))

    # Calculate SpO2
    ac_red, dc_red = calculate_ac_dc(red_data)
    ac_ir, dc_ir = calculate_ac_dc(ir_data)
    ratio_of_ratios = calculate_ratio_of_ratios(ac_red, dc_red, ac_ir, dc_ir)
    spo2 = convert_ratio_to_spo2(ratio_of_ratios)
    spo2 = butter_lowpass_filter(spo2, CUTOFF_FREQ, sampling_frequency)  # Smooth SpO2 signal

    # Calculate BPM
    bpm, bpm_timestamps = calculate_bpm(peaks, timestamps)

    # Interpolate BPM values over the entire timestamp range
    if len(bpm_timestamps) > 1:
        bpm = np.interp(timestamps, bpm_timestamps, bpm)
        bpm = butter_lowpass_filter(bpm, CUTOFF_FREQ, sampling_frequency)  # Smooth BPM signal
    else:
        bpm = np.zeros_like(timestamps)  # Handle cases where there are not enough peaks for BPM calculation

    num_samples = 90
    if len(timestamps) >= num_samples:
        indices = np.linspace(0, len(timestamps) - 1, num=num_samples, dtype=int)
    else:
        # If there are fewer than 90 samples, repeat or extend the last available sample
        indices = np.arange(len(timestamps))
        last_index = len(indices) - 1
        while len(indices) < num_samples:
            indices = np.append(indices, last_index)

    selected_timestamps = timestamps[indices]
    selected_gsr_data = gsr_data[indices]
    selected_red_data = red_data[indices]
    selected_ir_data = ir_data[indices]
    selected_ppg_data = ppg_data[indices]
    selected_peaks = peaks[np.where((peaks >= 0) & (peaks < len(indices)))]
    selected_spo2 = spo2[indices]
    selected_bpm = bpm[indices]

    # Create a DataFrame
    df = pd.DataFrame(
        {
            "Timestamps": selected_timestamps,
            "GSR_Data": selected_gsr_data,
            "Red_PPG_Data": selected_red_data,
            "IR_PPG_Data": selected_ir_data,
            "Processed_PPG_Data": selected_ppg_data,
            "SpO2": selected_spo2,
            "BPM": selected_bpm,
        }
    )

    output_csv_filename = os.path.splitext(os.path.basename(data_path))[0] + "_output.csv"
    output_csv_path = os.path.join(output_dir, output_csv_filename)

    plot_filename = os.path.splitext(os.path.basename(data_path))[0] + "_plot.png"
    plot_path = os.path.join(plot_dir, plot_filename)

    df.to_csv(output_csv_path, index=False)
    print(f"Saved selected data to {output_csv_path}")

    plot_signals(timestamps, gsr_data, red_data, ir_data, ppg_data, peaks, spo2, bpm, path=plot_path)
    print(f"Saved plot to {plot_path}")

    return output_csv_path
