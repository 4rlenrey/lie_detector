import glob
import os
from lie_detector.data_preprocessing.process_signals import process_signal


def process_directory(root_dir: str, output_dir: str, plot_dir: str):
    csv_files = glob.glob(os.path.join(root_dir, "**/*.csv"), recursive=True)

    for csv_file in csv_files:
        try:
            process_signal(csv_file, output_dir, plot_dir)
            print(f"Processed {csv_file}")
        except Exception as e:
            print(f"Error processing {csv_file}: {e}")

