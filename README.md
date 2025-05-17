# Titan One OS - Discord Bot

O.R.A.C.L.E. is a custom Discord bot for the **Titan One SCP Faction Server**. It provides moderation, tryout management, ranking, utility, anti-raid, automod, verification, and statistics features.

---

## Features

- **Moderation:** Lock/unlock/slowmode channels, clear messages, kick/ban/mute/unmute/timeout users, LOA requests, and audit logging.
- **Tryout System:** Host tryouts, manage participants, assign co-hosts, score participants, approve/deny codenames, and automate tryout management.
- **Ranking:** Points system, shift tracking, rank updates, and LOA management.
- **Utility:** Ping, dice roll, coin flip, reminders, trivia, guessing games, dice duels, and word scramble.
- **Anti-Raid & Security:** Automatic and manual raid detection, soft/hard raid protection, and anti-nuke features.
- **Automod:** Bad word filtering and admin action prompts.
- **Verification:** CAPTCHA-based verification for new members.
- **Statistics:** Live member/boost stats in channel names.
- **Rich Presence:** Custom Discord rich presence (see `richpresence.py`).

---

## Command Prefix

All commands use the prefix: `!`

---

## Commands Overview

### Moderation

- `!lock` / `!unlock` — Lock or unlock the current channel.
- `!slowmode <seconds>` — Set slowmode for the current channel.
- `!clear <number>` — Clear messages (confirmation for >10).
- `!kick <member> [reason]` — Kick a user.
- `!ban <member> [reason]` — Ban a user.
- `!unban <username>` — Unban a user.
- `!timeout <member> <minutes> [reason]` — Timeout a user.
- `!mute <member> [reason]` / `!unmute <member>` — Mute or unmute a user.
- `!loa <reason> <days>` — Request a Leave of Absence (LOA).

### Tryout System

- `!tryoutstart` — Start a tryout session.
- `!setcohost <tryout_id> <member>` — Assign a co-host.
- `!endtryout <tryout_id>` — End the tryout.
- `!addscore <tryout_id> <member> <points>` — Add points to a participant.
- `!removescore <tryout_id> <member> <points>` — Remove points from a participant.
- `!addscoreall <tryout_id> <points>` — Add points to all participants.
- `!removescoreall <tryout_id> <points>` — Remove points from all participants.
- `!showpoints <tryout_id>` — Show participant points.
- `!approve <member_id>` — Approve a codename.
- `!deny <member_id> <reason>` — Deny a codename.
- `!helptt` — Show tryout commands (in tryout management channels).

### Ranking

- `!startshift` — Start a shift (with DM controls).
- `!points [member]` — Show points for a user.
- `!addpoints <member> <amount>` — Add points (admin).
- `!removepoints <member> <amount>` — Remove points (admin).
- `!rankupd` — Update your rank roles based on points.

### Utility

- `!ping` — Show bot latency.
- `!roll [NdN]` — Roll dice.
- `!flip` — Flip a coin.
- `!reminder <time> <reminder>` — Set a reminder.
- `!trivia` — Play trivia.
- `!guess` — Number guessing game.
- `!dice_duel <opponent>` — Dice duel.
- `!scramble` — Word scramble game.

### Anti-Raid & Security

- `!manualraid` — Manually activate raid protection (admin).
- `!testraid` — Test raid protection (admin).

### Automod

- Automatic bad word filtering and admin action prompts.

### Verification

- CAPTCHA verification for new members.
- `!testcaptcha <member>` — Manually test CAPTCHA (admin).

### Statistics

- `!forceupdate` — Force update stats channels (admin).

---

## Help System

Use `!help` to see all commands you have access to, grouped by category.  
Use `!help <category>` to see all commands in a category.  

---

## Database

See [`database/README.md`](database/README.md) for setup and connection details.

---

## Notes

- Some commands require specific Discord permissions or roles.
- For advanced features (anti-nuke, activity reports, embed sending), see the `scraps/` directory.

---

## License

This project is for private use by the Titan One SCP Faction Server.
