import os
import tkinter as tk

# Folder paths
folder_path = f"C:/Users/TTS/PycharmProjects/RobotSystem_V4_16.6/running_system/racklog_dummy"
colormemory_file = f"C:/Users/TTS/PycharmProjects/RobotSystem_V4_16.6/running_system/WorkingDocs/colormemory.txt"

# Global variable to track active color positions
active_color_positions = set()

def get_color_positions_status_from_dummy():
    global active_color_positions
    color_positions = {}

    for filename in os.listdir(folder_path):
        if filename.endswith(".txt") and not filename.startswith("."):
            filepath = os.path.join(folder_path, filename)
            with open(filepath, "r", encoding="latin-1") as file:
                content = file.readlines()
                colorpos = None
                orangepos = None
                current_step = None
                steps = {}

                for line in content:
                    line = line.strip()
                    if line.startswith("ColorPos:"):
                        colorpos = line.split(":")[1].strip()
                        if colorpos.startswith("was"):
                            colorpos = None  # If it's marked as "was", ignore it
                        if colorpos and colorpos not in color_positions:
                            color_positions[colorpos] = {
                                "statuses": [],
                                "steps": {}
                            }
                            if colorpos not in active_color_positions:
                                active_color_positions.add(colorpos)
                    elif line.startswith("OrangePos:"):
                        orangepos = line.split(":")[1].strip()
                        if orangepos.startswith("was"):
                            orangepos = None  # If it's marked as "was", ignore it
                        if orangepos and orangepos not in color_positions:
                            color_positions[orangepos] = {
                                "statuses": [],
                                "steps": {}
                            }
                            if orangepos not in active_color_positions:
                                active_color_positions.add(orangepos)
                    elif line.startswith("Status:") and (colorpos or orangepos):
                        current_step = line.split(":")[1].strip().split(",")[0]
                    elif line.startswith("Step") and (colorpos or orangepos):
                        step, info = line.split(":")
                        step_name, _ = info.strip().split(",")
                        steps[step] = step_name.strip()

                if colorpos or orangepos:
                    # Calculate the indices
                    current_step_index = int(current_step.replace("Step", "")) if current_step else -1
                    step_indices = [int(step.replace("Step", "")) for step in steps if step.startswith("Step")]
                    last_step_index = max(step_indices) if step_indices else -1

                    if colorpos and current_step and steps:
                        color_steps = [int(step.replace("Step", "")) for step, name in steps.items() if name == "Color"]
                        last_color_step_index = max(color_steps) if color_steps else -1

                        if current_step_index >= last_color_step_index:
                            color_positions[colorpos]["statuses"].append("inactive")
                        else:
                            color_positions[colorpos]["statuses"].append("active")
                        color_positions[colorpos]["steps"] = steps

                    if orangepos and current_step and steps:
                        orange_steps = [int(step.replace("Step", "")) for step, name in steps.items() if name == "Orange"]
                        last_orange_step_index = max(orange_steps) if orange_steps else -1

                        if current_step_index > last_orange_step_index:
                            color_positions[orangepos]["statuses"].append("inactive")
                        elif current_step_index == last_orange_step_index and last_orange_step_index == last_step_index:
                            color_positions[orangepos]["statuses"].append("inactive")
                        else:
                            color_positions[orangepos]["statuses"].append("active")
                        color_positions[orangepos]["steps"] = steps

    # Determine overall status based on aggregation rules
    for pos, data in color_positions.items():
        statuses = data["statuses"]

        if "active" in statuses:
            overall_status = "active"
        else:
            overall_status = "inactive"

        color_positions[pos]["overall_status"] = overall_status

    return color_positions

def get_color_positions_status_from_colormemory():
    color_positions = {}
    if os.path.getsize(colormemory_file) > 0:
        with open(colormemory_file, "r", encoding="latin-1") as f:
            color_memory = f.readlines()

        if color_memory:
            for line in color_memory:
                if not line.startswith("#"):  # Skip commented lines
                    colorpos, status_message = line.strip().split("; ")
                    colorpos = colorpos.split(": ")[1]
                    if colorpos not in color_positions:
                        color_positions[colorpos] = []
                    color_positions[colorpos].append(status_message)
    return color_positions

def update_colormemory():
    global active_color_positions
    color_positions_status = get_color_positions_status_from_colormemory()
    dummy_positions_status = get_color_positions_status_from_dummy()
    updated_color_memory = {}

    # Update color memory from dummy files
    for colorpos, data in dummy_positions_status.items():
        overall_status = data.get("overall_status", "unknown")
        updated_color_memory[colorpos] = overall_status

        # Update active_color_positions based on overall status
        if overall_status == "active" and colorpos not in active_color_positions:
            active_color_positions.add(colorpos)
        elif overall_status == "inactive" and colorpos in active_color_positions:
            active_color_positions.remove(colorpos)

    # Check for ColorPos entries in color_positions_status that are not in dummy_positions_status
    existing_color_positions = set(color_positions_status.keys())
    for colorpos in existing_color_positions:
        if colorpos not in updated_color_memory:
            # Check if any sample file exists for this ColorPos
            sample_file_exists = any(
                os.path.isfile(os.path.join(folder_path, f"{colorpos}.txt")) for filename in os.listdir(folder_path)
            )
            if not sample_file_exists:
                updated_color_memory[colorpos] = "inactive"

    # Write updated color memory to file
    with open(colormemory_file, "w", encoding="latin-1") as f:
        for colorpos, status_message in updated_color_memory.items():
            f.write(f"Colorpos: {colorpos}; {status_message}\n")

def show_color_positions():
    global color_positions_frame
    for widget in color_positions_frame.winfo_children():
        widget.destroy()

    color_positions_status = get_color_positions_status_from_colormemory()
    print(f"{color_positions_status}")

    displayed_positions = set()  # Track displayed positions to avoid duplicates

    if color_positions_status:
        for pos, statuses in color_positions_status.items():
            status_message = statuses[0] if statuses else "unknown"

            # Initialize button_text
            button_text = None

            # Determine the type of position and set button_text accordingly
            if pos == "7":
                if "inactive" in status_message:
                    button_text = f"Remove Orange Position {pos} (not in use anymore)"
                else:
                    button_text = f"Orange Position {pos} currently in use"
            elif pos != "7":
                if "inactive" in status_message:
                    button_text = f"Remove Color Position {pos} (not in use anymore)"
                else:
                    button_text = f"Color Position {pos} currently in use"

            # Check if this position has already been displayed
            if pos not in displayed_positions:
                displayed_positions.add(pos)
                if button_text:  # Ensure button_text is not None
                    if "inactive" in status_message:
                        unused_button = tk.Button(color_positions_frame, text=button_text,
                                                 command=lambda p=pos: delete_color_position(p))
                        unused_button.pack(padx=10, pady=5)
                    else:
                        tk.Label(color_positions_frame, text=button_text).pack(padx=10, pady=5)
    else:
        tk.Label(color_positions_frame, text="No Color or Orange registered.").pack(padx=10, pady=5)




def delete_color_position(colorpos):
    global active_color_positions
    # Remove color position from colormemory file
    if os.path.exists(colormemory_file):
        with open(colormemory_file, "r", encoding="latin-1") as f:
            lines = f.readlines()
        with open(colormemory_file, "w", encoding="latin-1") as f:
            for line in lines:
                if f"Colorpos: {colorpos}" not in line:
                    f.write(line)

    # Update racklog dummy files
    if colorpos != "7":
        for filename in os.listdir(folder_path):
            if filename.endswith(".txt") and not filename.startswith("."):
                filepath = os.path.join(folder_path, filename)
                with open(filepath, "r", encoding="latin-1") as file:
                    content = file.readlines()
                with open(filepath, "w", encoding="latin-1") as file:
                    for line in content:
                        if line.startswith(f"ColorPos: {colorpos}"):
                            file.write(line.replace(f"ColorPos: {colorpos}", f"ColorPos: was{colorpos}"))
                        else:
                            file.write(line)
    else:
        for filename in os.listdir(folder_path):
            if filename.endswith(".txt") and not filename.startswith("."):
                filepath = os.path.join(folder_path, filename)
                with open(filepath, "r", encoding="latin-1") as file:
                    content = file.readlines()
                with open(filepath, "w", encoding="latin-1") as file:
                    for line in content:
                        if line.startswith(f"OrangePos: {colorpos}"):
                            file.write(line.replace(f"OrangePos: {colorpos}", f"OrangePos: was{colorpos}"))
                        else:
                            file.write(line)

    # Update active_color_positions
    if colorpos in active_color_positions:
        active_color_positions.remove(colorpos)

    show_color_positions()

def main():
    global root, color_positions_frame, runtime_counter
    root = tk.Tk()
    root.title("Color Positions in Use")
    root.geometry("400x300")

    color_positions_frame = tk.Frame(root)
    color_positions_frame.pack(fill="both", expand=True, padx=10, pady=10)

    runtime_counter = 0
    print(f"{runtime_counter}")

    # Function to update and refresh
    def update_and_refresh():
        global runtime_counter
        update_colormemory()
        show_color_positions()
        runtime_counter += 1
        print(f"{runtime_counter}")
        # Schedule next update after 1 second (1000 milliseconds)
        root.after(1000, update_and_refresh)

    # Start the initial update and refresh
    update_and_refresh()

    root.mainloop()

if __name__ == "__main__":
    main()
