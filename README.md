# Shelby 

A custom firmware for the [Sprig Console](https://sprig.hackclub.com) by Hack Club that 
turns it into a always-on desk companion. Because why let it collect dust when it can 
actually be useful?

## What is this?

Shelby transforms your Sprig from a game console into a small but mighty desk companion. 
It sits on your desk, shows you the time with a dynamic background that changes throughout 
the day, pings you when something needs your attention, and keeps your tasks in check — 
all on that tiny screen.

## Features

- **Clock with dynamic backgrounds** — morning, afternoon and night themes that shift 
  automatically based on time of day
- **GitHub notifications** — get alerted when there's a PR, issue or mention waiting 
  for you
- **Gmail alerts** — shows unread count and previews new emails as they come in
- **Task list** — add, check off and manage a simple to-do list right from the console
- **More coming** — this is actively being built, suggestions welcome

## Hardware

You just need a Sprig. That's it. No extra components, no soldering, nothing fancy.

If you don't have one, [apply for one here](https://sprig.hackclub.com) — Hack Club 
sends them out for free.

## Setup

1. Clone the repo
   ```bash
   git clone https://github.com/Swamstick911/Shelby
   cd Shelby
   ```

2. Copy the example env file and fill in your credentials
   ```bash
   cp .env.example .env
   ```

3. Add your GitHub token, Gmail API credentials and timezone to `.env`

4. Flash the firmware to your Sprig following the instructions in `/docs/flashing.md`

5. That's it, it should boot right up

6. Controls

| Button        | Action                             |
| ------------- | ---------------------------------- |
| W / S         | Scroll through menu                |
| A             | Go back                            |
| D             | Select / confirm                   |
| I / J / K / L | Context actions (varies by screen) |
