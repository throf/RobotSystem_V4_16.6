import os
import time
import re

def calculate_chem_position(color_pos):
    return color_pos + 9

def determine_waste_type(status, previous_chem):
    if status == "Step0":
        return "None"  # No waste to remove for the initial step
    elif "BaBB" in previous_chem or "Color" in previous_chem:
        return "Bad"
    elif "Orange" in previous_chem:
        return "Orange"
    else:
        return "Regular"

def build_task_content(sample_content):
    sample_id_match = re.search(r"SampleID: (\d+)", sample_content)
    position_match = re.search(r"Position: (\d+)", sample_content)
    color_pos_match = re.search(r"ColorPos: (\d+)", sample_content)
    status_match = re.search(r"Status: Step(\d+)", sample_content)
    steps_match = re.findall(r"Step\d+: (\w+)", sample_content)

    sample_id = int(sample_id_match.group(1))
    position = int(position_match.group(1))
    if color_pos_match:
        color_pos = int(color_pos_match.group(1))
    status = int(status_match.group(1))

    # Check if the sample is finished
    if status >= len(steps_match) - 1:
        return None  # No further steps, sample is finished

    next_step = steps_match[status + 1] if len(steps_match) > status + 1 else ""  # Get the next step chemical

    task_content = f"[Task]\nSamplePosition: S{position}\n"

    if "Color" in next_step:
        chem_pos = calculate_chem_position(color_pos)
        task_content += f"ChemPosition: C{chem_pos}\n"
    elif "Orange" in next_step:
        task_content += f"ChemPosition: C16\n"
    else:
        # Map chemicals to their positions
        chem_positions = {
            "PBS": 1, "Perm": 2, "Permblock": 3, "MeOH50": 4, "MeOH70": 5,
            "MeOH95": 6, "MeOH100": 7, "MeOHBaBB": 8, "BaBB": 9, "MeOH25": 17
        }
        chem_pos = chem_positions.get(next_step, 1)
        task_content += f"ChemPosition: C{chem_pos}\n"

    previous_chem = steps_match[status] if len(steps_match) > status else ""  # Get the current step chemical
    waste_type = determine_waste_type(f"Step{status}", previous_chem)
    task_content += f"WasteType: {waste_type}"

    return task_content

def check_and_update_files(folder_path, second_file_path, handbreak_path):
    while True:
        while os.path.getsize(handbreak_path) > 0:
            print("Handbreak pulled")
            time.sleep(3)
        for filename in os.listdir(folder_path):
            filepath = os.path.join(folder_path, filename)

            if filename.endswith(".txt") and not filename.startswith("."):
                with open(filepath, 'r+', encoding="latin-1") as file:
                    sample_content = file.read()

                    # Check if the file contains "Status: StepX,0min"
                    status_match = re.search(r"Status: Step(\d+),0min", sample_content)
                    if status_match:
                        status = int(status_match.group(1))

                        task_content = build_task_content(sample_content)

                        if task_content is None:
                            continue  # Skip this file if there are no further steps

                        while True:
                            try:
                                # Write Proto content to the second file
                                with open(second_file_path, 'w', encoding="latin-1") as destination:
                                    destination.write(task_content)
                                break
                            except Exception as e:
                                time.sleep(1)

                        # Synchronize before writing to the second file
                        while os.path.getsize(second_file_path) > 0:
                            print("waiting on robot")
                            time.sleep(1)

                        # Re-read the sample content to check for any changes
                        with open(filepath, 'r', encoding="latin-1") as file:
                            sample_content = file.read()

                        # Re-check if the file still contains "Status: StepX,0min"
                        status_match = re.search(r"Status: Step(\d+),0min", sample_content)
                        if not status_match:
                            continue

                        status = int(status_match.group(1))

                        # Update status and timing in the sample file
                        new_status = status + 1
                        new_timing_match = re.search(r"Step%d: \w+,(\d+)min" % (new_status), sample_content)
                        if new_timing_match:
                            new_timing = new_timing_match.group(1)
                            new_content = re.sub(r"Status: Step%d,0min" % status, f"Status: Step{new_status},{new_timing}min", sample_content)
                            with open(filepath, 'r+', encoding="latin-1") as file:
                                file.seek(0)
                                file.write(new_content)
                                file.truncate()

                        print(f"Updated {filename}")

        time.sleep(3)  # Adjust the interval as needed
        print("circled")


# Define the folder path
folder_path = f'C:/Users/TTS/PycharmProjects/RobotSystem_V4_16.6/running_system/racklog_dummy'

handbreak_path = "C:/Users/TTS/PycharmProjects/RobotSystem_V4_16.6/running_system/WorkingDocs/handbreak.txt"

# Define the path of the second text file
second_file_path = f"C:/Users/TTS/PycharmProjects/RobotSystem_V4_16.6/running_system/WorkingDocs/ProtoV4.txt"

# Run the check_and_update_files function in a loop
check_and_update_files(folder_path, second_file_path, handbreak_path)
