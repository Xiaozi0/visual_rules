# Grid Lock / Traffic Jam Rule Snapshot

Source: Invent with Python, Grid Lock clone.

Rules abstracted for VQA generation:
- Played on a grid (e.g., 6x6).
- Cars (2 units long) and trucks (3 units long) are placed horizontally or vertically.
- Vehicles can only move forward or backward along their length.
- The goal is to get the "target car" (e.g., Red) to the exit square on the right edge.

VQA Questions:
- Which color vehicle is directly blocking the Red car from exiting?
- How many moves (forward/backward) would the blocking vehicle need to make to clear the path?
