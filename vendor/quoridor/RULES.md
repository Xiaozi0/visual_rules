# Quoridor Rule Snapshot

Source: Invent with Python, Quoridor clone.

Rules abstracted for VQA generation:
- 9x9 grid of squares.
- Players move their pawns one square at a time or place a wall (2 units long).
- Walls must be placed between squares and cannot completely block all paths to a player's goal side.

VQA Questions:
- Is the proposed wall placement legal (does it block all paths)?
- What is the shortest path distance to the goal side for the current player?
