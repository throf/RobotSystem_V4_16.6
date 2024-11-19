import os
import tkinter as tk
from tkinter import messagebox, simpledialog
import shutil
import datetime
from PIL import Image, ImageTk  # You need to install Pillow for this
import threading  # Import threading module

# Folder paths
folder_path = f"C:/Users/TTS/PycharmProjects/RobotSystem_V4_16.6/running_system/racklog_dummy"
archive_folder = f"C:/Users/TTS/PycharmProjects/RobotSystem_V4_16.6/running_system/racklog_archive"
protocol_templates_path = f"C:/Users/TTS/PycharmProjects/RobotSystem_V4_16.6/running_system/ProtokollTemplates"
id_file_path = f"C:/Users/TTS/PycharmProjects/RobotSystem_V4_16.6/running_system/WorkingDocs/last_id.txt"

def get_last_sample_id():
    if os.path.exists(id_file_path):
        with open(id_file_path, "r", encoding="latin-1") as file:
            return int(file.read().strip())
    else:
        return 0

def update_last_sample_id(sample_id):
    with open(id_file_path, "w", encoding="latin-1") as file:
        file.write(str(sample_id))

def get_available_locations(action):
    all_locations = set(range(1, 7))  # 2x3 grid
    occupied_locations = get_occupied_locations()

    if action == "register":
        return all_locations - occupied_locations
    elif action == "remove":
        return occupied_locations
    else:
        return set()

def manage_samples(action, selected_location=None, selected_protocol=None):
    register_button.config(state="disabled")
    remove_button.config(state="disabled")

    if action == "register":
        available_locations = get_available_locations(action)
        if not available_locations:
            messagebox.showinfo("No available locations", "All locations are occupied.")
            register_button.config(state="normal")
            remove_button.config(state="normal")
            return None

        if selected_location is None:
            selected_location = select_location(available_locations, action)

        if selected_location is None:
            register_button.config(state="normal")
            remove_button.config(state="normal")
            return None

        if selected_protocol is None:
            register_button.config(state="normal")
            remove_button.config(state="normal")
            return None

        staining_solution_position = None
        if selected_protocol != "Individual Protocol" and protocol_requires_colorpos(selected_protocol):
            staining_solution_position = ask_for_staining_solution_position()
            if staining_solution_position is None:
                register_button.config(state="normal")
                remove_button.config(state="normal")
                return None
        sample_id = get_last_sample_id() + 1
        if selected_protocol != "Individual Protocol":
            create_sample_file(sample_id, selected_location, staining_solution_position, selected_protocol)
            update_last_sample_id(sample_id)
            messagebox.showinfo("Sample Registered", f"Sample registered with ID {sample_id} at position {selected_location}.")
            register_button.config(state="normal")
            remove_button.config(state="normal")

        return sample_id

    elif action == "remove":
        if selected_location is None:
            selected_location = select_location(get_available_locations(action), action)
            if selected_location is None:
                register_button.config(state="normal")
                remove_button.config(state="normal")
                return None
        try:
            remove_sample(selected_location)
        except:
            messagebox.showerror("Error", f"Please try again when the robot has stopped moving.")

        register_button.config(state="normal")
        remove_button.config(state="normal")

        return None

    return None


def create_sample_file(sample_id, location, staining_solution_position, protocol):
    if protocol == "Individual Protocol":
        template_content = ""  # No template content for individual protocol
    else:
        protocol_template_path = os.path.join(protocol_templates_path, f"{protocol}.txt")
        try:
            with open(protocol_template_path, "r", encoding="latin-1") as template_file:
                template_content = template_file.read()
        except FileNotFoundError:
            messagebox.showerror("Template Not Found", f"Template for protocol '{protocol}' not found.")
            return



    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sample_content = template_content.replace("SampleID: ", f"SampleID: {sample_id}")
    sample_content = sample_content.replace("Position: ", f"Position: {location}")
    if staining_solution_position is not None:
        sample_content = sample_content.replace("ColorPos: ", f"ColorPos: {staining_solution_position}")
    sample_content = sample_content.replace("Created: ", f"Created: {current_datetime}")

    filename = f"{sample_id}.txt"
    filepath = os.path.join(folder_path, filename)
    with open(filepath, "w", encoding="latin-1") as file:
        file.write(sample_content)

def ask_for_staining_solution_position():
    while True:
        staining_solution_position = simpledialog.askinteger("Staining Solution Position", "Enter the position of the staining solution (1 to 6):")

        if staining_solution_position is None:  # User canceled the dialog
            return None

        if isinstance(staining_solution_position, int) and 1 <= staining_solution_position <= 6:
            print(f"{staining_solution_position}")
            return staining_solution_position
        else:
            messagebox.showwarning("Wrong Colorpos", "Please choose Position 1 to 6.")

def get_occupied_locations():
    occupied_locations = set()
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt")and not filename.startswith("."):
            filepath = os.path.join(folder_path, filename)
            with open(filepath, "r", encoding="latin-1") as file:
                content = file.readlines()
                for line in content:
                    if line.startswith("Position:"):
                        pos = int(line.split(":")[1].strip())
                        occupied_locations.add(pos)
                        break  # Assuming each file has only one "Position" entry
    return occupied_locations

def remove_sample(location):
    sample_found = False
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt") and not filename.startswith("."):
            filepath = os.path.join(folder_path, filename)
            with open(filepath, "r", encoding="latin-1") as file:
                content = file.readlines()
                for line in content:
                    if line.startswith("Position:"):
                        pos = int(line.split(":")[1].strip())
                        if pos == location:
                            sample_found = True
                            if not os.path.exists(archive_folder):
                                os.makedirs(archive_folder)
                            file.close()
                            shutil.move(filepath, os.path.join(archive_folder, filename))
                            messagebox.showinfo("Sample Moved", f"Sample moved to archive from position {location}.")
                            break
    if not sample_found:
        messagebox.showinfo("Sample Not Found", f"No sample found at position {location}.")

def select_location(locations, action):
    selection = None
    location_frame = tk.Frame(root)
    location_frame.pack()

    def select(location):
        nonlocal selection
        selection = location
        location_frame.destroy()
        if action == "register":
            select_protocol(selection)  # Pass selected location to select_protocol

    def abort():
        nonlocal selection
        selection = None
        location_frame.destroy()

    action_label = tk.Label(location_frame, text=action.capitalize(), font=("Helvetica", 14, "bold"))
    action_label.grid(row=0, columnspan=4, padx=5, pady=5)

    # Create a 2x3 grid for locations
    for row in range(2):
        for col in range(3):
            if row == 0:
                location = col * 2 + 1
            else:
                location = col * 2 + 2
            if location in locations: # Check if a location is available
                btn = tk.Button(location_frame, text=f"Position {location}", command=lambda l=location: select(l))
                btn.grid(row=row + 1, column=col, padx=5, pady=5)  # Adjust row index
            else:
                btn = tk.Button(location_frame, text=f"Position {location}", state="disabled")
                btn.grid(row=row + 1, column=col, padx=5, pady=5)  # Adjust row index

    abort_button = tk.Button(location_frame, text="Abort", command=abort)
    abort_button.grid(row=3, columnspan=4, padx=5, pady=5)

    location_frame.wait_window()

    return selection

def select_protocol(selected_location):
    if selected_location is None:
        selected_location = select_location(get_available_locations("register"), "register")
        if selected_location is None:
            return  # Abort if no location is selected

    # Initialize selected_protocol variable
    selected_protocol = None

    # Get the list of protocols
    protocols = [os.path.splitext(f)[0] for f in os.listdir(protocol_templates_path) if f.endswith(".txt") and not f.startswith(".")]

    # Create a new window for protocol selection
    protocol_window = tk.Toplevel(root)
    protocol_window.title("Select Protocol")
    protocol_window.geometry("250x300")

    # Function to handle protocol selection
    def select_protocol_handler(protocol):
        nonlocal selected_protocol
        selected_protocol = protocol
        protocol_window.destroy()

        if selected_protocol == "Individual Protocol":
            # Get the sample_id from manage_samples
            sample_id = manage_samples("register", selected_location, selected_protocol)
            if sample_id is not None:
                create_individual_protocol(sample_id, selected_location)
        else:
            # Proceed with the selected protocol
            manage_samples("register", selected_location, selected_protocol)  # Pass selected location and protocol

    # Function to handle abort button
    def abort_selection():
        protocol_window.destroy()

    # Create buttons for each protocol
    for protocol in protocols:
        protocol_button = tk.Button(protocol_window, text=protocol, command=lambda p=protocol: select_protocol_handler(p))
        protocol_button.pack(pady=(5, 0))

    # Add an "Individual Protocol" button
    individual_button = tk.Button(protocol_window, text="Individual Protocol", command=lambda: select_protocol_handler("Individual Protocol"))
    individual_button.pack(pady=(5, 0))

    # Add an "Abort" button
    abort_button = tk.Button(protocol_window, text="Abort", command=abort_selection)
    abort_button.pack(side=tk.BOTTOM, pady=10)

    protocol_window.wait_window()

    return selected_protocol

def create_individual_protocol(sample_id, selected_location):
    global chemical_dropdowns, chemical_vars  # Define chemical_dropdowns and chemical_vars as global variables

    def update_steps_layout(num_steps):
        num_steps = int(num_steps)
        for i in range(10):  # Maximum of 10 steps
            if i < num_steps:
                chemical_dropdowns[i].grid(row=i+6, column=0)
                time_labels[i].grid(row=i+6, column=1)
                time_entries[i].grid(row=i+6, column=2)
                min_labels[i].grid(row=i+6, column=3)
            else:
                chemical_dropdowns[i].grid_forget()
                time_labels[i].grid_forget()
                time_entries[i].grid_forget()
                min_labels[i].grid_forget()

    individual_protocol_window = tk.Toplevel(root)
    individual_protocol_window.title("Generate Individual Protocol")

    # Function to handle closing the window
    def on_window_close():
        individual_protocol_window.destroy()
        register_button.config(state="normal")
        remove_button.config(state="normal")

    # Function to handle abort
    def abort_generation():
        on_window_close()

    # Function to handle saving the protocol
    def save_protocol():
        # Get values from entry fields and dropdown menus
        orange = orange_var.get()
        staining_solution = staining_solution_var.get()
        colorpos = colorpos_var.get()  # Use the StringVar directly
        num_steps = int(num_steps_var.get())

        # Check if any step is incomplete
        incomplete_step = False
        invalid_time_entry = False
        for i in range(num_steps):
            if not chemical_vars[i].get() or not time_entries[i].get() or "-empty-" in chemical_vars[i].get():
                incomplete_step = True
                break
            try:
                int(time_entries[i].get())  # Check if time entry is a real number
            except ValueError:
                invalid_time_entry = True
                break

        if incomplete_step:
            messagebox.showwarning("Incomplete Steps", "Please fill out all fields for each step before saving.")
            return

        if invalid_time_entry:
            messagebox.showwarning("Invalid Time Entry", "Please enter a valid number for the time in each step.")
            return

        # Set colorpos false for case that colorpos is not needed
        colorpos_outofbounds = False
        if staining_solution_var.get(): # Check if colorpos is needed
            colorpos_outofbounds = True
            try:
                colorpos_int = int(colorpos_var.get())  # Try converting the string to an integer
            finally:
                if isinstance(colorpos_int, int) and 1 <= colorpos_int <= 6:
                    colorpos_outofbounds = False

        if colorpos_outofbounds:
            messagebox.showwarning("Wrong Colorpos", "Please choose Position 1 to 6.")
            return

        # Generate starting lines of protocol content
        protocol_content = f"[Sample]\nSampleID: {sample_id}\nPosition: {selected_location}\n"
        if orange:
            protocol_content += f"OrangePos: 7\n"
        if staining_solution and colorpos:
            protocol_content += f"ColorPos: {colorpos}\n"
        protocol_content += "Created: {}\nStatus: Step0,0min\n\n[Steps]\nStep0: Fix,0min\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # Append chemical vars and time entries based on the actual number of steps selected
        steps_info = []
        for i in range(num_steps):
            steps_info.append((chemical_vars[i].get(), time_entries[i].get()))

        # Append protocol steps to protocol content
        for i, (chemical, time) in enumerate(steps_info):
            if time.startswith(" "):
                protocol_content += f"Step{i + 1}: {chemical},{time.lstrip()}min\n"
            else:
                protocol_content += f"Step{i+1}: {chemical},{time}min\n"


        # Save protocol content to file
        filename = f"{sample_id}.txt"
        filepath = os.path.join(folder_path, filename)
        try:
            with open(filepath, "w") as file:
                file.write(protocol_content)
            # Update last sample ID
            update_last_sample_id(sample_id)
            messagebox.showinfo("Protocol Saved", f"Protocol saved successfully for Sample ID {sample_id}.")
            # Close the window
            on_window_close()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while saving the protocol:\n{str(e)}")



    def set_chemical_var_value(var, value):
        var.set(value)

    def handle_colorpos_change(*args):
        # Get the current value of colorpos_var
        colorpos_value = colorpos_var.get()
        # Check if the value is a valid string (non-empty)
        if colorpos_value.strip() and staining_solution_var.get():
            for dropdown in chemical_dropdowns:
                menu = dropdown['menu']
                menu_items = [menu.entrycget(index, 'label') for index in range(menu.index('end') + 1)]
                if "Color" not in menu_items:
                    menu.add_command(
                        label="Color",
                        command=lambda var=chemical_vars[chemical_dropdowns.index(dropdown)],
                                       value="Color": set_chemical_var_value(var, value)
                    )
        else:
            # Remove "Color" from all dropdown menus if present
            for dropdown, var in zip(chemical_dropdowns, chemical_vars):
                menu = dropdown['menu']
                menu_items = [menu.entrycget(index, 'label') for index in range(menu.index('end') + 1)]
                if "Color" in menu_items:
                    color_index = menu_items.index("Color")
                    menu.delete(color_index)
                    # Reset the selection if "Color" was selected
                    if var.get() == "Color":
                        var.set("-empty-")  # Clear the variable
                        dropdown.configure(text="Select Chemical")

    def handle_orange_change(*args):
        # Check if the value is a valid string (non-empty)
        if orange_var.get():
            for dropdown in chemical_dropdowns:
                menu = dropdown['menu']
                menu_items = [menu.entrycget(index, 'label') for index in range(menu.index('end') + 1)]
                if "Orange" not in menu_items:
                    menu.add_command(
                        label="Orange",
                        command=lambda var=chemical_vars[chemical_dropdowns.index(dropdown)],
                                       value="Orange": set_chemical_var_value(var, value)
                    )
        else:
            # Remove "Orange" from all dropdown menus if present
            for dropdown, var in zip(chemical_dropdowns, chemical_vars):
                menu = dropdown['menu']
                menu_items = [menu.entrycget(index, 'label') for index in range(menu.index('end') + 1)]
                if "Orange" in menu_items:
                    orange_index = menu_items.index("Orange")
                    menu.delete(orange_index)
                    # Reset the selection if "Orange" was selected
                    if var.get() == "Orange":
                        var.set("-empty-")  # Clear the variable
                        dropdown.configure(text="Select Chemical")

    # Sample ID and Sample Position labels
    sample_id_label = tk.Label(individual_protocol_window, text=f"Sample ID: {sample_id}")
    sample_id_label.grid(row=0, column=0, columnspan=4, pady=(10, 5))
    position_label = tk.Label(individual_protocol_window, text=f"Sample Position: {selected_location}")
    position_label.grid(row=1, column=0, columnspan=4, pady=5)

    # Orange checkbox
    orange_var = tk.BooleanVar()

    # Staining Solution checkbox
    staining_solution_var = tk.BooleanVar()

    def toggle_colorpos_entry():
        if staining_solution_var.get():
            colorpos_entry.config(state="normal")
        else:
            colorpos_entry.delete(0, 'end')
            colorpos_entry.config(state="disabled")
            individual_protocol_window.focus()  # Reset focus to the main window or another widget

    staining_solution_check = tk.Checkbutton(individual_protocol_window, text="Staining Solution", variable=staining_solution_var, command=toggle_colorpos_entry)
    staining_solution_check.grid(row=2, column=0, columnspan=4, pady=5)
    # ColorPos entry
    colorpos_var = tk.StringVar()
    colorpos_label = tk.Label(individual_protocol_window, text="ColorPos:")
    colorpos_label.grid(row=3, column=0, pady=5)
    colorpos_entry = tk.Entry(individual_protocol_window, textvariable=colorpos_var)
    colorpos_entry.grid(row=3, column=1, pady=5)
    colorpos_entry.config(state="disabled")  # Initially disabled

    orange_check = tk.Checkbutton(individual_protocol_window, text="Eq Orange Eosin Y", variable=orange_var)
    orange_check.grid(row=4, column=0, columnspan=4, pady=5)

    # Add trace to monitor changes in colorpos_var, so handle_colorpos_change can add or remove "Color"
    colorpos_var.trace_add("write", handle_colorpos_change)

    # Add trace to monitor changes in orange_var, so handle_orange_change can add or remove "Orange"
    orange_var.trace_add("write", handle_orange_change)

    # Number of Steps dropdown
    num_steps_label = tk.Label(individual_protocol_window, text="Number of Steps:")
    num_steps_label.grid(row=5, column=0, pady=5)
    num_steps_var = tk.StringVar()
    num_steps_dropdown = tk.OptionMenu(individual_protocol_window, num_steps_var, *range(1, 11), command=update_steps_layout)
    num_steps_var.set(10)  # Default to 10 steps
    num_steps_dropdown.grid(row=5, column=1, pady=5)

    # Chemical dropdowns and Time entries for each step
    chemical_dropdowns = []
    chemical_vars = []  # Define chemical_vars list
    time_entries = []
    time_labels = []
    min_labels = []
    for i in range(10):  # Maximum of 10 steps
        chemical_var = tk.StringVar()
        chemical_dropdown = tk.OptionMenu(individual_protocol_window, chemical_var, "PBS", "Perm", "Permblock","MeOH25", "MeOH50", "MeOH70", "MeOH95", "MeOH100", "MeOHBaBB", "BaBB")
        chemical_dropdowns.append(chemical_dropdown)
        chemical_dropdowns[i].grid(row=i+6, column=0, pady=5)
        chemical_vars.append(chemical_var)

        time_label = tk.Label(individual_protocol_window, text="Time:")
        time_labels.append(time_label)
        time_labels[i].grid(row=i+6, column=1, pady=5)

        time_entry = tk.Entry(individual_protocol_window)
        time_entries.append(time_entry)
        time_entries[i].grid(row=i+6, column=2, pady=5)

        min_label = tk.Label(individual_protocol_window, text="min")
        min_labels.append(min_label)
        min_labels[i].grid(row=i+6, column=3, pady=5)

    # Save and Cancel buttons
    save_button = tk.Button(individual_protocol_window, text="Save", command=save_protocol)
    save_button.grid(row=16, column=0, columnspan=2, pady=(10, 5))
    cancel_button = tk.Button(individual_protocol_window, text="Cancel", command=abort_generation)
    cancel_button.grid(row=16, column=2, columnspan=2, pady=5)

    # Bind window closing event to on_window_close function
    individual_protocol_window.protocol("WM_DELETE_WINDOW", on_window_close)

    individual_protocol_window.mainloop()

def protocol_requires_colorpos(protocol):
    if protocol == "Individual Protocol":
        return False
    protocol_template_path = os.path.join(protocol_templates_path, f"{protocol}.txt")
    with open(protocol_template_path, "r", encoding="latin-1") as template_file:
        content = template_file.read()
        return "ColorPos:" in content

def show_all_samples():
    finished_samples = []
    ongoing_samples = []

    for filename in os.listdir(folder_path):
        if filename.endswith(".txt") and not filename.startswith("."):
            filepath = os.path.join(folder_path, filename)
            with open(filepath, "r", encoding="latin-1") as file:
                content = file.read().strip().split("\n")
                steps = []

                id_check = False
                position_check = False

                for line in content:
                    if ":" in line:
                        key, value = line.split(":", 1)
                        if key.strip() == "SampleID":
                            sample_id = value.strip()
                            id_check = True
                        elif key.strip() == "Position":
                            position = value.strip()
                            position_check = True
                        elif key.strip().startswith("Step"):
                            steps.append(value.strip())

                if id_check == True and position_check == True:
                    status_line = [line for line in content if line.startswith("Status:")]
                    if status_line:
                        status_info = status_line[0].split(":")[1].strip().split(",")
                        if len(status_info) == 2:
                            step = int(status_info[0].split("Step")[1])
                            remaining_time = int(status_info[1].split("min")[0].strip())
                            if step < len(steps):
                                step_chemical = steps[step].split(",")[0].strip()  # Extract step chemical
                                total_time_remaining = calculate_total_time_remaining(step, remaining_time, steps)
                                if total_time_remaining > 0:
                                    ongoing_samples.append(f"Sample {sample_id} Position {position} Step {step} {step_chemical} {remaining_time}min (Total Time left: {total_time_remaining}min)")
                                else:
                                    finished_samples.append(f"Sample {sample_id} Position {position} finished")
                            else:
                                print(f"Step {step} exceeds the number of steps in the sample file for sample {sample_id}")
                        else:
                            print(f"Invalid status line format for sample {sample_id}")
                    else:
                        print(f"Status line not found for sample {sample_id}")
                else:
                    print(f"Sample information incomplete or missing for file {filename}")
                    ongoing_samples.append(
                        f"error while reading sample, should fix on its own")
    return finished_samples, ongoing_samples

def calculate_total_time_remaining(step, remaining_time, steps):
    total_time = remaining_time
    for i in range(step + 1, len(steps)):
        time_str = steps[i].split(",")[1].strip()
        time_value = int(time_str.split("min")[0])
        total_time += time_value
    return total_time


def update_all_samples():
    global all_samples_label

    finished_samples, ongoing_samples = show_all_samples()

    if 'all_samples_label' in globals() and all_samples_label.winfo_exists() and not (
            finished_samples or ongoing_samples):
        all_samples_label.destroy()
        root.after(1200, update_all_samples)
        return

    all_samples = ongoing_samples + finished_samples
    if all_samples:
        if not 'all_samples_label' in globals() or not all_samples_label.winfo_exists():
            all_samples_label = tk.Label(location_frame, text="All Samples:")
            all_samples_label.pack()

        for widget in location_frame.winfo_children():
            widget.destroy()
        for sample in all_samples:
            all_sample_label = tk.Label(location_frame, text=sample)
            all_sample_label.pack()
    else:
        for widget in location_frame.winfo_children():
            widget.destroy()
        all_sample_label = tk.Label(location_frame, text="empty")
        all_sample_label.pack()

    root.after(1200, update_all_samples)


def toggle_play_pause():
    global is_paused
    is_paused = not is_paused
    play_pause_button.config(text="Play" if is_paused else "Pause")

    file_path = "C:/Users/TTS/PycharmProjects/RobotSystem_V4_16.6/running_system/WorkingDocs/handbreak.txt"

    if is_paused:
        with open(file_path, 'w') as file:
            file.write("Robot is paused.")
    else:
        with open(file_path, 'w') as file:
            file.write("")


# Initialize the paused state
is_paused = False

def show_image():
    # Load the image
    image_path = "C:/Users/TTS/PycharmProjects/RobotSystem_V4_16.6/running_system/WorkingDocs/Limaa_logo2.png"  # Replace with your image path
    img = Image.open(image_path)
    img = img.resize((115, 45), Image.LANCZOS)  # Resize the image using Image.LANCZOS
    img = ImageTk.PhotoImage(img)

    # Create a label to display the image
    img_label = tk.Label(root, image=img)
    img_label.image = img  # Keep a reference to avoid garbage collection
    img_label.place(relx=1.0, rely=1.0, anchor='se')  # Place the image in the bottom right corner
    print("image shown")

def main():
    global root
    global play_pause_button, is_paused
    root = tk.Tk()
    root.title("Sample Tracker")
    root.geometry("500x400")

    main_frame = tk.Frame(root)
    main_frame.pack(expand=True, fill="both")

    button_frame = tk.Frame(main_frame)
    button_frame.pack(side="top", pady=10)

    global register_button, remove_button, location_frame
    register_button = tk.Button(button_frame, text="Register Sample", command=lambda: manage_samples("register"))
    register_button.grid(row=0, column=0, padx=(140, 5), pady=5)

    # Show the image using a thread to avoid blocking the function
    threading.Thread(target=show_image).start()

    remove_button = tk.Button(button_frame, text="Remove Sample", command=lambda: manage_samples("remove"))
    remove_button.grid(row=0, column=1, padx=(5, 80), pady=5)

    play_pause_button = tk.Button(button_frame, text="Pause", width=5, command=toggle_play_pause)
    play_pause_button.grid(row=0, column=2, padx=5, pady=5)

    location_frame = tk.Frame(main_frame)
    location_frame.pack(expand=True, fill="both")

    update_all_samples()

    root.mainloop()

if __name__ == "__main__":
    main()
