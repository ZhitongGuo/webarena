from convert_html import convert
import argparse
import os
import glob
from tqdm import tqdm
from playwright._impl._api_types import TimeoutError


def clean_and_convert_directory(trace_file, log_file='failed_files.log'):
    try:
        path_out_no_ext = os.path.splitext(trace_file)[0]
        convert(f"file://{trace_file}", path_out_no_ext)
    except TimeoutError as e:
        print(f"Timeout occurred: {e}")
        print(f"Timeout occurred for file: {trace_file}")
        log_failed_file(trace_file, log_file)

def log_failed_file(file_path, log_file='failed_files.log'):
    with open(log_file, 'a') as f:
        f.write(file_path + '\n')

def process_failed_files(log_file='failed_files.log'):
    with open(log_file, 'r') as f:
        failed_files = f.read().splitlines()
    for trace_file in failed_files:
        try:
            path_out_no_ext = os.path.splitext(trace_file)[0]
            convert(f"file://{trace_file}", path_out_no_ext)
            print(f"Processed failed file: {trace_file}")
        except TimeoutError:
            print(f"Timeout occurred again for file: {trace_file}")
            continue

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=str, required=True, help="Directory containing .trace.html files")
    parser.add_argument("--process_failed", action='store_true', help="Process files from failed_files.log instead of the directory")
    args = parser.parse_args()

    if args.process_failed:
        process_failed_files()
    else:
        print("start processing")
        clean_and_convert_directory(args.directory)