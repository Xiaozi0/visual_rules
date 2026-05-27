# Tetris Rule Snapshot

Source: Invent with Python, Tetris clone.

Rules abstracted for VQA generation:
- Played on a grid (e.g., 10x10).
- Seven types of tetrominoes (I, O, T, S, Z, J, L).
- Pieces fall from the top.
- A row is cleared if it is completely filled with blocks.
- Static VQA frames show a snapshot with one "currently falling" piece (highlighted or floating) and a stack of existing blocks.

VQA Questions:
- Identify the shape of the falling piece.
- Determine if a full line would be cleared if the piece lands in its current column.
