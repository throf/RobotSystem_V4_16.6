import os
import re
import time
import logging


def update_status_line(line):
    """
    Update the status line if it matches the pattern 'Status: <step_name>,<min_num>min'.
    """
    match = re.search(r"Status: (\w+),(\d+)min", line)
    if match:
        step_name = match.group(1)
        min_num = int(match.group(2))
        if min_num > 0:
            return f"Status: {step_name},{min_num - 1}min\n"
    return line


def process_file(filepath):
    """
    Process a single file to update its status lines.
    """
    try:
        with open(filepath, "r") as file:
            lines = file.readlines()

        updated_lines = []
        for line in lines:
            # Update the Status line in the [Sample] section
            if line.startswith("Status:"):
                updated_lines.append(update_status_line(line))
            else:
                updated_lines.append(line)

        # Write the updated lines back to the file
        with open(filepath, "w") as file:
            file.writelines(updated_lines)
    except FileNotFoundError:
        logging.error(f"File not found: {filepath}")
    except Exception as e:
        logging.error(f"An error occurred while processing {filepath}: {e}")


def process_files(folder_path):
    """
    Continuously process files in the specified folder to update their status lines.
    """
    iteration = 0
    while True:
        for filename in os.listdir(folder_path):
            if filename.endswith(".txt") and not filename.startswith("."):
                filepath = os.path.join(folder_path, filename)
                process_file(filepath)
        logging.info("Cycle completed")
        iteration = iteration + 1
        print(f"{iteration}")
        time.sleep(
            60)  # [1] Second is for accelerated testing; put in [60] Seconds to use the program in a real scenario


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Change the folder path to the directory containing your txt files
    folder_path = "C:/Users/TTS/Desktop/RobotSystem_V4/racklog_dummy"
    process_files(folder_path)
