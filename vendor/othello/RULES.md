# Othello Rule Snapshot

Source: Invent with Python, Othello clone.

Rules abstracted for VQA generation:
- Played on an 8x8 grid.
- Players take turns placing a disc of their color (Black or White).
- A legal move must bracket at least one opponent disc between the newly placed disc and an existing disc of the player's color, in a straight line (horizontal, vertical, or diagonal).
- All bracketed opponent discs are flipped to the player's color.
- Static VQA frames show a board state with some placed discs.

VQA Questions:
- Determine whether a highlighted square is a legal move for a specific color.
- Count the number of opponent discs that would be flipped if a player placed a disc on a highlighted square.
