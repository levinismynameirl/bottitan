# Titan One OS - Discord Bot

Titan One OS is a custom Discord bot designed for the **Titan One SCP Faction Server**. The bot provides various moderation and utility commands to help manage the server efficiently. Below is a detailed guide on how to use the bot, including its commands and functionality.

## NOTE: EVERYTHING BELOW MAY BE OUTDATED. ASK DEV FOR OFFICIAL COMMANDS

---

## **How to Run the Bot**
To start the bot, use the following command in the terminal:

```
python [botrun.py](http://_vscodecontentref_/1)
```

## Bot Prefix

The bot uses the prefix:
```
!
```
All commands must be prefixed with **"!"**.


----------------------------------------------------




# Commands
## Moderation Commands

Below is a list of all commands related to moderation. 
*Note that you need specific permission to run each command*

-----------------------------------------------------------

```
!slowmode <seconds>
```
**Sets the slowmode for the current channel.**
*Example: !slowmode 10 (sets slowmode to 10 seconds).*

-----------------------------------------------------------

```
!lock
```
**Locks the current channel, preventing members from sending messages.**
*Example: !lock*

-----------------------------------------------------------

```
!unlock
```
**Unlocks the current channel, restoring the default permissions.**
*Example: !unlock*

-----------------------------------------------------------

```
!clear <number>
```
**Clears a specified number of messages in the current channel (up to 100).**
**If the number is greater than 10, the bot will ask for confirmation with buttons.**
*Example: !clear 5 (clears 5 messages).*

-----------------------------------------------------------

```
!rank entree @user
```
**Assigns the Recruit and Official Member roles to a user and removes the Awaiting Tryout and Unofficial Personnel roles.*
*Example: !rank entree @JohnDoe*

-----------------------------------------------------------

```
!loa <reason> <time_in_days>
```
Allows a user with the Official Member role to request a Leave of Absence (LOA).
Sends the request to a random administrator for approval or denial.
Example: !loa Vacation 7 (requests a 7-day LOA for vacation).

## THE LOA COMMAND IS CURRENTLY WIP

#
