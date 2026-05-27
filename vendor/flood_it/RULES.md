# Flood It Rule Snapshot

Source: Invent with Python, Flood It clone.

Rules abstracted for VQA generation:
- Played on a grid (e.g., 14x14) filled with 6 random colors.
- The player controls the top-left connected region.
- When the player chooses a color, the connected region changes to that color and absorbs any adjacent blocks of the newly chosen color.
- Static VQA frames show a grid of colors, with the top-left connected region visually distinguished (e.g., with a border).

VQA Questions:
- Determine which color choice would add the most new blocks to the connected region.
- Count how many new blocks would be added if a specific color is chosen.
