# Dodger Rule Snapshot

Source: Invent with Python, Dodger clone.

Vendor artifact:
- `dodger.zip` downloaded from `https://inventwithpython.com/dodger.zip?27f655`
- extracted files include `dodger.py`, `player.png`, `baddie.png`, `gameover.wav`, and `background.mid`

Rules abstracted for VQA generation:
- The VQA abstraction uses a 10 x 10 grid inside the original 600 x 600 square playfield.
- The player and enemies are square sprites centered inside grid cells.
- Enemies move straight downward by one or more whole grid cells per time step.
- A collision occurs when the player's axis-aligned rectangle intersects any enemy rectangle.
- Static VQA frames encode each enemy's next-step square with a colored outline and a downward arrow.
- The generated questions ask for collision, threat timing, or safe movement under this deterministic one-step or multi-step update.
