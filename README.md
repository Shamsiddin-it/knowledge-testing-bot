## Telegram Knowlegde testing Bot

This is a Telegram bot that can test your knowledge. You can add the test and pass the test. Other functionalities like dividing actions to roles will be soon⏳.

### Getting Started

To run this bot on your machine:

1. **Create a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Create a `config.py` file** in the root directory and add the following:

   ```python
   BOT_TOKEN = 'your_bot_token_here'
   DATABASE_URL = 'your_database_url_here'
   ```

That's it! Now you can run the bot and start getting reminders.
