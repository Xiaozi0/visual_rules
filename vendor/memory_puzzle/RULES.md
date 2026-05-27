# Memory Puzzle Rule Snapshot

Source: Invent with Python, Memory Puzzle clone.

Vendor artifact:
- `memorypuzzle.py` downloaded from `https://inventwithpython.com/memorypuzzle.py`

Rules abstracted for VQA generation:
- The board is a grid of face-down cards.
- Each hidden icon appears exactly twice on the full board.
- Revealed cards show a shape and a color.
- A pair is matched only when both revealed cards have the same shape and the same color.
- Static VQA frames show a partial game state with some cards revealed and the rest covered.
- Generated questions ask whether selected revealed cards match, or how many matching pairs are visible among revealed cards.

