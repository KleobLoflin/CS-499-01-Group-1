# Class input

# Maps keyboard/mouse state to a normalized Intent for the local player
# (move vector, aim vector, buttons)

# intent meaning, what the player wants to do.
# DungeonScene uses this to build client-to-server_input packets and will
# end up using the local entity's intent component for client prediction.

# client prediction is necessary to cover up latency caused from having to
# wait for the server to validate everthing and send back snapshots
