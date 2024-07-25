import matplotlib.pyplot as plt

def plot_signals(timestamps, gsr_data, red_data, ir_data, ppg_data, peaks, spo2, bpm, path="plots/ir_red.png"):
    plt.figure(figsize=(12, 10))

    plt.subplot(6, 1, 1)
    plt.plot(timestamps, gsr_data)
    plt.title('GSR Data')
    
    plt.subplot(6, 1, 2)
    plt.plot(timestamps, ppg_data)
    plt.plot(timestamps[peaks], ppg_data[peaks], "x")
    plt.title('Processed PPG Data with Peaks')
    
    plt.subplot(6, 1, 3)
    plt.plot(timestamps, red_data, label='Red PPG')
    plt.title('Red PPG')

    plt.subplot(6, 1, 4)
    plt.plot(timestamps, ir_data, label='IR PPG')
    plt.title('IR PPG')

    plt.subplot(6, 1, 5)
    plt.plot(timestamps, spo2)
    plt.title('Continuous SpO2 Signal')
    
    plt.subplot(6, 1, 6)
    plt.plot(timestamps, bpm)
    plt.title('Continuous BPM Signal')

    plt.tight_layout()
    plt.savefig(path)
