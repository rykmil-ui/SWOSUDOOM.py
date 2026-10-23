# DOOM assignment project — feature branch history

This branch pack reconstructs the available version progression from the Python files available in this session. Each feature branch is cumulative: it contains the game version for that step, prior version snapshots, and the changelog.

## Branch map

| Branch | Snapshot | Main change represented |
|---|---:|---|
| `feature/v3-enemies-and-effects` | v3 | Enemy roster/count expansion, brute enemy, animation/effects, gameplay polish |
| `feature/v4-gameplay-and-world` | v4 | Further gameplay/world refinements |
| `feature/v5-assignment-baseline` | v5 | Assignment baseline before later structured enhancements |
| `feature/v6-fuel-strategy` | v6 | Fuel-based strategy selection and different gameplay outcomes |
| `feature/v7-state-and-enemy-loop` | v7 | Variable/sentinel-driven enemy/event loop and state/accumulator work |
| `feature/v8-enemy-spawn-validation` | v8 | Enemy spawn validation |
| `feature/v9-graphics-overhaul` | v9 | Retro pseudo-3D graphics/effects overhaul |
| `feature/v10-hellwave-loop` | v10 | Hellwave gameplay/audio iteration |
| `feature/v11-strategy-function` | v11 | `configure_strategy()` refactor with parameters and return values |
| `feature/v12-four-weapons` | v12 | Four selectable weapons |
| `feature/v13-enemies-and-visuals` | v13 | Additional enemy types and visual improvements |
| `feature/v14-chaingun-auto-fire` | v14 | Chaingun automatic fire while left mouse is held |
| `feature/v15-procedural-guitar-music` | v15 | Procedurally generated guitar-tab soundtrack |
| `feature/v16-music-tempo-125` | v16 | First soundtrack tempo adjustment to 125 BPM |
| `feature/v17-tab-timing-correction` | v17 | Guitar tab timing/pitch interpretation refinement |
| `feature/v19-gun-sounds-and-tempo` | v19 | Synthesized weapon sounds; soundtrack at 105 BPM |
| `feature/v20-slower-soundtrack` | v20 | Soundtrack slowed to 62.5 BPM |
| `feature/v21-selectable-soundtracks` | v21 | Pre-game choice between original track and new tone sequence |
| `feature/v22-faster-second-track` | v22 | Second track increased to 140 BPM; first track unchanged |

**Important:** v18 was not present among the available source files, so no v18 branch is fabricated. The supplied version snapshots are kept under `versions/`. The active game in each branch is `python_doom_enhanced_assignment.py`.

## Gameplay requirements carried forward in later versions

- Pre-game prompts before the Pygame window opens.
- Fuel-sensitive Assault / Tactical / Escape strategy choices.
- Different enemy counts/ammo/health based on strategy.
- Red key and red exit door, with exit unlocked only after all enemies are defeated.
- `#1 victory royale` victory text.
- Number-key weapon switching, Space to jump, left mouse to shoot.
- Chaingun automatic fire only while left mouse is held.
- Procedural looping soundtrack and synthesized weapon sound effects.
- Two soundtrack choices in v21 onward.

## Using these branches with GitHub

This pack is a standalone reconstructed Git history, not a direct edit to your existing GitHub repository. It has its own local Git history, so do not merge its branches into your existing `main` blindly. You can push the reconstructed branches to a new repository, or use the version snapshots as references when recreating the feature commits on your existing repository's history.

To push all branches to a new GitHub remote after creating an empty repository:

```powershell
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin --all
```

To inspect branches:

```powershell
git branch --list
git log --oneline --graph --decorate --all
```
