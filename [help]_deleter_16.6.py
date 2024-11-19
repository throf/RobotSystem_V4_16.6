import os
import time


def clear_file_contents(file_path):
    with open(file_path, 'w'):  # Opening the file in 'w' mode truncates it to zero length
        pass


def main(file_path):
    iteration = 0
    while True:
        iteration += 1
        print(f"Iteration {iteration}: Clearing contents of {file_path}")
        clear_file_contents(file_path)
        time.sleep(1)  # Optional delay between iterations


if __name__ == "__main__":
    file_path = f"C:/Users/TTS/Desktop/RobotSystem_V4/WorkingDocs/ProtoV4.txt"  # Replace with your file path

    try:
        main(file_path)
    except KeyboardInterrupt:
        print("\nProgram interrupted. Exiting...")
