# Mancala Rule Snapshot

Source: Invent with Python, Mancala clone.

Rules abstracted for VQA generation:
- Two rows of 6 pits and two large stores (Mancalas).
- Sowing: Pick all seeds from a pit and drop them one by one in subsequent pits counter-clockwise, including your own store.
- Extra turn: If the last seed is dropped in the player's store, they get another turn.
- Capture: If the last seed drops in an empty pit on the player's side and the opposite pit is not empty, capture all seeds from both pits.

VQA Questions:
- Count the number of seeds in a specific pit.
- Determine if sowing from a specific pit results in an extra turn.
