# Nibbles Rule Snapshot

Source: Invent with Python, Wormy / Nibbles clone.

Vendor artifact:
- `wormy.py` downloaded from `https://inventwithpython.com/wormy.py`

Rules abstracted for VQA generation:
- The snake occupies a list of grid cells; the head is visually distinguished.
- At each step, the head moves one grid cell in the current direction.
- A collision occurs if the next head cell is outside the board or overlaps the snake body.
- Apples are target cells; relative direction questions compare the apple with the snake head.

