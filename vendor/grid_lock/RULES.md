# Grid Lock / Traffic Jam Rule Snapshot

Source: Invent with Python, Grid Lock clone.

Rules abstracted for VQA generation:
- Played on a 6x6 grid.
- Vehicles are either Cars (2x1 or 1x2) or Trucks (3x1 or 1x3).
- Vehicles can only move along their orientation (horizontal or vertical).
- Target Car (Red) is horizontal on the 3rd row (index 2).
- The exit is at (2, 5).

VQA Questions:
- Which color vehicle is directly blocking the Red car's path to the exit?
- If the blocking vehicle moves, is the Red car's path clear?
