# Game state diagram

```mermaid
stateDiagram-v2
    [*] --> HOME
    HOME --> READY: start_game()
    READY --> COUNTDOWN: start_round()
    COUNTDOWN --> CAPTURE: 3 seconds elapsed
    CAPTURE --> SCORE_UPDATE: stable valid move
    CAPTURE --> SCORE_UPDATE: no clear move after 5 seconds
    SCORE_UPDATE --> RESULT: record score and history
    RESULT --> COUNTDOWN: 3 seconds elapsed and match not over (auto_next)
    RESULT --> READY: new_game() after match over

    note right of RESULT
        A match is over when either player's score
        reaches the target score of 3.
        After a match, a new game is user-started.
    end note
```

The controller enters `SCORE_UPDATE` while recording the completed round, then immediately enters `RESULT`. If the target has not been reached, automatic play starts the next round after the three-second result interval; a new match resets the scores and returns to `READY`.
