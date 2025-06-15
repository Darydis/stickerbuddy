# Pizza Choice Bot

Telegram bot to select pizzas based on group ratings.

## Features
- Upload a photo of a menu. The bot sends it to ChatGPT to extract pizza names and prices.
- Participants rate pizzas from 0 to 10 or use `/veto` to strongly reject.
- The bot aggregates scores with veto logic: veto equals score 0, and a pizza is excluded if more than half the participants use veto.
- Use `/result K` to see the top `K` pizzas with highest sum score.

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and set your `BOT_TOKEN` and optional `OPENAI_API_KEY`.
3. Run the bot:
   ```bash
   python -m pizzabot.bot
   ```

The source code is split into modules under the `pizzabot` package for easier maintenance.
