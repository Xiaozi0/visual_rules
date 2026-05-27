# Abalone Rule Snapshot

Source: Invent with Python, Abalone clone.

Rules abstracted for VQA generation:
- Hexagonal board.
- Players (Black/White) move 1, 2, or 3 adjacent marbles of their color.
- A broadside move moves marbles in a direction not along the line of marbles.
- An in-line move (Sumito) can push opponent marbles if the player has more marbles in the line and there is an empty space or edge behind the opponent.

VQA Questions:
- Can the highlighted group of marbles move in the indicated direction?
- How many opponent marbles will be pushed by this move?
