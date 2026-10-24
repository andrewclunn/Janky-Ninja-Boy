# JANKY Ninja Boy

**Version 0.38 — development build**

JANKY Ninja Boy is an improvement hack of the U.S. release of *Super Ninja Boy*. It makes combat more forgiving, gives exploration and co-op better rewards, adds convenient weapon and spell controls, replaces passwords with battery saving, and revises the dialogue with a story about hackers meddling with the game. The original mix of exploration, platforming, action battles, minigames, and RPG boss fights remains.

This document describes the current changes **compared with the original game**. Version 0.38 includes the latest Counter substitution feature and is still being playtested.

[Cumulative IPS patch](Janky_Ninja_Boy_v0.38.ips) · [ASM source](Build/Janky_Ninja_Boy_v0.38.asm) · [Build script](Build/build.py)

## Controls and menus

Weapons and throwing spells have separate shortcuts. Each player can choose their own weapon and selected spell, even though the party shares equipment progress and spell ownership.

| Button | Action during action combat |
|---|---|
| **Y** | Attack with your fists or weapon, or throw an active throwing spell |
| **B** | Normal jump |
| **A, standing still on the ground** | High jump straight up, at full running-jump height; costs 1 NP |
| **A, moving left or right on the ground** | Miracle Kick; costs 1 NP |
| **A, while airborne** | Spinning Moonsault Kick / airborne roll; costs 1 NP |
| **L** | Cycle fists and unlocked sword/nunchuck types |
| **R** | Cycle owned throwing spells, including NONE |
| **X** | Activate the selected throwing spell at its normal NP cost |

At **zero NP**, A follows the normal B jump behavior during action gameplay. Selecting a spell with R costs nothing; activating it with X spends NP. Pressing Y during the descent of an ordinary jump also lets an unarmed player perform the full spin kick for 1 NP when no active spell overrides the attack.

Outside combat, use the usual movement and interaction controls. Start opens the menu where available. Menus accept **A or Y to confirm** and **B or X to cancel**. Menu confirmation never spends NP.

## Saving and continuing

The game now has **three battery-save slots**, with overwrite confirmation and the saved level shown beside each occupied slot. Use the in-game Save and Load menus instead of entering passwords.

Saves retain story progress, experience, money, medals, equipment, weapon unlocks and selections, and the shared M-point total. Loading resumes at the game's normal checkpoint rather than the exact position where you saved.

When moving an existing hack save to another build:

1. Close the emulator and back up your battery save.
2. Give a copy the same basename as the new ROM, using your emulator's save-file extension and save folder. For the working ROM, this is commonly `Janky Ninja Boy.srm`.
3. Start the new ROM normally and choose **Load** in the game.

Use battery saves for transfers between builds. Emulator save states also restore old code and temporary state, so they are best kept with the build that created them. The current battery-save file is 8 KiB. Older hack save formats 1 and 2 can be loaded; their M total starts at zero and is included when saved in the current format. Older hack releases may not read newer saves.

## Combat and equipment

Punches, swords, and nunchucks have more forgiving reach and alignment checks. You still need to connect with an enemy, but landing a melee hit is less fussy.

Sword and nunchuck pickups permanently unlock that weapon type **for both players**. L switches among your unlocked types without needing another pickup. Both weapons use the party's shared weapon-power level; without a power upgrade, their damage matches fist damage. Weapon-power upgrades also unlock the sword.

Being hit can still knock a held weapon away. When that happens, the affected player switches to **fists**. The unlocked type remains available to select again with L, and the other player's selection is unaffected.

Other combat changes include:

- Weaker or duplicate equipment pickups no longer replace a better tier. This applies to armor, helmets, shields, weapon power, gloves, and LV Counters.
- Each enemy defeat restores **1 NP** to each living, active, unarmed player with no active spell, up to their maximum NP.
- **BOO BOMB consumables deal triple damage**, capped at 255 damage per hit. STAR BOMB throwing magic keeps its existing damage.
- The green flying dragon with gold wings starts with **10 HP**, reduced from 70.
- Ordinary quota battles credit **one defeat every 30 seconds of active combat**, in addition to enemies you defeat yourself. This lets a stalled battle eventually finish. These timed credits give no extra enemy rewards and do not apply to RPG bosses or special scripted fights.

The difficulty selection is removed and the game uses its **Hard** setting, alongside the specific balance changes above.

## LV Counters and smoke substitution

LV Counters keep their information function: they reveal enemy levels and the ordinary encounter's KO quota within the item's supported level range. They now also provide a passive chance to avoid an action-combat hit by disappearing into smoke.

| Item | Reveals enemies through | Substitution chance per eligible hit |
|---|---:|---:|
| **LV Counter 1** | Level 10 | 1 in 128 |
| **LV Counter 2** | Level 20 | 1 in 64 |
| **LV Counter 3** | Level 25 | 1 in 32 |
| **LV Counter 4** | Level 45 | 1 in 16 |

The substitution chance depends on the Counter tier, rather than the enemy-level reveal limit. It works for either player and prevents the triggering hit's damage and reaction. The affected player briefly disappears while smoke appears, then returns. Other hits during that brief protection do not spend additional M points.

A successful substitution removes **1 shared M point if you have any**. It still works at **0 M**, with the same chance. Failed rolls spend nothing. This ability applies to action combat, not the separate RPG boss battles.

## M points and floating orbs

The party can now hold **99 shared M points**, increased from 15. They are preserved by in-game saving and loading.

Floating orbs can still produce M points, money, or a skull. A skull now removes **1 NP from the player who hit the orb**, stopping at zero, instead of removing a shared M point.

## Less grinding and better co-op rewards

Every completed tile that **Player 1 walks on foot without triggering a random encounter** gives the party 1 experience point. This includes town and other safe tiles. Standing still, pushing against a wall, Player 2's movement, and vehicle travel do not give walking experience. Walking experience stops at the maximum level of 50.

Walking can trigger a normal level-up, with a message and fanfare before returning you to exploration. The Status screen also shows **NEXT**, the experience still needed for the next level; at level 50 it shows zero.

Random encounters use a **base chance of 1 in 64 per Player 1 tile step**, subject to the game's location and encounter filters. Player 2's movement, idle time, and blocked movement do not roll encounters.

In two-player play, enemy money awards are **twice the single-player base amount**, including when one player is knocked out. Experience keeps its existing sharing rules. The lower display shows each player's current and maximum HP and NP, with the shared level and M total and separate spell selections.

## Exploration and optional challenges

Swords and nunchucks can break the special **blue barriers** guarding the Soundmaster's side exits, giving you another way to reach the matching minigame and its medal prizes.

There is also a new optional RPG boss in **Yokan, the first town**. A formerly closed house northwest of the convenience shop is now accessible from the plaza through an opening in the fence. Its occupant, **Mr. F Boss**, introduces himself and asks whether you really want to challenge him.

He has a custom portrait, new battle artwork, and his own combat setup. The encounter is optional and supports rematches. Win to hear his explanation for that rather suspicious name.

## Dialogue and presentation

The title now reads **JANKY Ninja Boy**, and the heroes are known as **Jank and Ryeu**. The opening introduces the hack's premise, while revised town, field, battle, story, and ending dialogue carries the joke through the game.

The script includes clearer wording, consistent shared names, spelling corrections, revised service conversations, and new jokes about the game's quirks. Native story choices, progression, quizzes, shops, and rewards remain part of the adventure.

The soundtrack adds **14 tracks from Super Chinese World 3**, with new assignments for towns, dungeons, and training areas. Action arenas draw from five selected themes: **Ninja Combat!**, **They're Getting Stronger!**, **Intense Training**, **Ready for Training!**, and **Super Ninja Boy**. Each arena keeps its assigned music during play.

Selected game, graphics, and audio routines also use **FastROM** to reduce processing overhead. The game retains its SNES presentation and can still slow down in busy scenes.

## Playing or building this version

Apply [Janky_Ninja_Boy_v0.38.ips](Janky_Ninja_Boy_v0.38.ips) to a clean, unheadered U.S. ROM of Super Ninja Boy, then open the patched ROM in your SNES emulator. Original and generated ROMs are kept local and are not included in this repository.

To build from source, supply a **clean, unheadered U.S. ROM of Super Ninja Boy** and run this from the project folder with Python installed:

```powershell
python Build/build.py "PATH_TO_CLEAN_ROM" Build/Janky_Ninja_Boy_v0.38.sfc --source Build/Janky_Ninja_Boy_v0.38.asm
```

The required original ROM is **1,048,576 bytes**, with SHA-256:

```text
40b46bb29785fb431b325f22377faa8b099be4d77aecc1f03000b8a4cb589b63
```

The resulting v0.38 ROM is **4,194,304 bytes**, with SHA-256:

```text
77027fab98242e8782a15fe7cf6889449313405e2837302e4c80292f372793dd
```

Use the original U.S. ROM as the source, rather than another hack or the separate Japanese-game translation patch. The build includes the cumulative changes; no previous hack version needs to be applied first.

## Project status and further reading

Version 0.38 is a development build. Focused checks cover the implemented changes, but a complete playthrough and wider gameplay testing are still ongoing. The latest Counter feature has probability, damage-path, smoke, and save-initialization checks; natural collision playtesting remains pending.

Development continues from the stable **v0.22 lineage**, retaining the later changes described here. The abandoned secret-town experiment is excluded from this build.

The [authoritative ASM](Build/Janky_Ninja_Boy_v0.38.asm) preserves the cumulative implementation, technical notes, and recorded validation evidence.

## Credits and references

*Super Ninja Boy* and the *Super Chinese World* games, their original artwork, and their music are the work of **Culture Brain**. This project adds its own dialogue revisions, controls, gameplay changes, music arrangements, and optional boss content.

The project's reference collection includes the original game manual, a walkthrough, and documentation for the separate *Super Chinese World* translation. That translation is a reference, not an installation requirement for this U.S.-ROM hack.
