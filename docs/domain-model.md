# Domain model

```mermaid
erDiagram
  USER ||--o{ ORGANIZATION_MEMBERSHIP : joins
  ORGANIZATION ||--o{ ORGANIZATION_MEMBERSHIP : has
  ORGANIZATION ||--o{ LEAGUE : owns
  LEAGUE ||--o{ SEASON : contains
  ORGANIZATION ||--o{ TEAM : owns
  SEASON ||--o{ SEASON_TEAM : includes
  TEAM ||--o{ SEASON_TEAM : appears_in
  ORGANIZATION ||--o{ PLAYER : registers
  SEASON_TEAM ||--o{ ROSTER_ENTRY : has
  PLAYER ||--o{ ROSTER_ENTRY : assigned
  SEASON ||--o{ FIXTURE : schedules
  TEAM ||--o{ FIXTURE : hosts
  TEAM ||--o{ FIXTURE : visits
  FIXTURE ||--|| MATCH : records
  MATCH ||--o{ MATCH_EVENT : contains
```

`SeasonTeam` and `RosterEntry` preserve historical membership: a club and a
player can participate in different seasons without rewriting past data.
`Match` is one-to-one with a fixture, while events are append-only records
validated against the live match and its seasonal rosters.
