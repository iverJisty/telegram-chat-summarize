# Telegram Chat Summarize

This project is a Python application that helps users to summarize their Telegram group chats and create daily summarizations. The application uses the Telegram Bot API to access the chat history and the Claude or GPT model to generate summaries.

## Installation

1. Clone the repository to your local machine.
2. Install Python 3.x and pip.
3. Install the required dependencies by running `pip install -r requirements.txt`.

## Environment Variables

The following environment variables are required to run the application:

- `CLAUDE_API_KEY`: The API key for the Claude Service API.
- `OPENAI_API_KEY`: The API key for the OpenAI API.
- `TELEGRAM_BOT_API_TOKEN`: The API token for the Telegram Bot API.
- `TELEGRAM_APP_API_ID`: The API ID for the Telegram app.
- `TELEGRAM_APP_API_HASH`: The API hash for the Telegram app.
- `DEVELOPER_CHAT_ID`: The telegram channel ID for the developer to get the message

## Usage

1. Run the application by executing `python main.py`.
2. Use the following commands to interact with the application:
   - `/start`: Start the application.
   - `/summary`: Summarize the current chat.
   - `/set_chat_name`: Set the name of the current chat.
   - `/show_chats`: Show a list of all available chats.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue if you encounter any problems.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more information.