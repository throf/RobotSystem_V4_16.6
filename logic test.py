# Scenario 1: sample_id = "", position = "Position"
sample_id = ""
position = "Position"

if sample_id and position:
    print("A1")
else:
    print("B1 declined")

if sample_id is not None and position is not None:
    print("A2")
else:
    print("B2 declined")

# Scenario 2: sample_id = None, position = "Position"
sample_id = None
position = "Position"

if sample_id and position:
    print("A3")
else:
    print("B3 declined")

if sample_id is not None and position is not None:
    print("A4")
else:
    print("B4 declined")