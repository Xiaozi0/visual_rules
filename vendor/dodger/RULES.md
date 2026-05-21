# Dodger Rule Snapshot

Source: Invent with Python, Dodger clone.

Vendor artifact:
- `dodger.zip` downloaded from `https://inventwithpython.com/dodger.zip?27f655`
- extracted files include `dodger.py`, `player.png`, `baddie.png`, `gameover.wav`, and `background.mid`

Rules abstracted for VQA generation:
- The playfield is a 600 x 600 square.
- The player is a 40 x 40 sprite.
- Enemies are square baddies with variable size.
- Enemies move straight downward at a fixed per-instance speed.
- A collision occurs when the player's axis-aligned rectangle intersects any enemy rectangle.
- Static VQA frames encode each enemy's next-step vertical displacement with a downward arrow.
- The generated questions ask for collision, threat timing, or safe movement under this deterministic one-step or multi-step update.

