# Quarto Rule Snapshot

Source: Invent with Python, Quarto clone.

Rules abstracted for VQA generation:
- 4x4 board.
- Pieces have 4 binary attributes: (Tall/Short, Round/Square, Hollow/Solid, White/Black).
- A player wins by completing a row, column, or diagonal where all 4 pieces share at least one common attribute.

VQA Questions:
- Do the pieces in a highlighted row share a common attribute?
- Which attribute is shared by the pieces in a highlighted line?
