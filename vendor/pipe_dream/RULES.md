# Pipe Dream Rule Snapshot

Source: Invent with Python, Pipe Dream clone.

Rules abstracted for VQA generation:
- Played on a grid (e.g., 10x10).
- The grid is filled with various pipe pieces: straight (horizontal, vertical) and corners (4 orientations).
- There is a designated Start pipe and an End pipe.
- Water flows from the Start pipe through connected pipes. Two pipes are connected if their adjacent ports face each other.
- Static VQA frames show a snapshot of the grid. The pipes are laid out, but no water is flowing yet.

VQA Questions:
- Determine if the water flowing from the Start will successfully reach the End through the current pipe configuration.
- Determine if a specific highlighted pipe is part of the connected network starting from the Start pipe.
