# SQL Expert AI Assistant

An AI-powered SQL assistant that helps users understand database structures and write SQL queries. The tool combines multiple AI models to provide expert advice and code review capabilities.

## Features

- **AI-Powered SQL Assistance**: Get help understanding your database and writing SQL queries
- **Multiple AI Models**: Uses separate models for expert advice and code review
- **Interactive UI**: Web interface with chat functionality and query execution
- **Multi-Database Support**: Works with PostgreSQL, MySQL, MSSQL, and SQLite
- **Real-time Query Execution**: Execute and view query results instantly
- **Code Review**: Automatic review of generated SQL queries for best practices and performance
- **Customizable System Prompts**: Tailor the AI behavior for different use cases

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/sql-expert.git
cd sql-expert
```

2. Install Pipenv if you haven't already:
```bash
pip install pipenv
```

3. Create virtual environment and install dependencies:
```bash
pipenv install

# Activate the virtual environment
pipenv shell
```

The following packages will be installed:
- sqlalchemy[asyncio] - Database ORM with async support
- gradio - Web UI framework
- openai - OpenAI API client
- anthropic - Anthropic API client
- python-dotenv - Environment variable management
- asyncpg - PostgreSQL async driver
- aiomysql - MySQL async driver
- aiosqlite - SQLite async driver
- pymssql - MSSQL driver

4. Create a `.env` file with your configuration:
```env


# AI Configuration
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Comma-separated list of provider:model pairs
AI_MODELS=OpenAI:gpt-4,Anthropic:claude-3-sonnet
```

## Usage

1. Start the application:
```bash
python -m expert.ui
```

2. Open your web browser and navigate to `http://localhost:7860`

3. Connect to your database using the connection panel

4. Start chatting with the AI to get help with SQL queries

## Features in Detail

### Database Connection
- Support for multiple database types
- Secure connection handling
- Automatic DDL extraction

### AI Assistance
- Expert model for query generation and explanation
- Reviewer model for code quality and performance checks
- Customizable system prompts
- Context-aware responses based on database structure

### Query Execution
- Real-time query execution
- Results displayed in tabular format
- Automatic error handling
- Support for large result sets

## Project Structure

```
sql-expert/
├── expert/
│   ├── ai/
│   │   ├── config.py       # AI configuration management
│   │   ├── factory.py      # AI model factory
│   │   ├── protocol.py     # AI interface definitions
│   │   ├── openai_expert.py
│   │   └── anthropic_expert.py
│   ├── tool/
│   │   ├── connection.py   # Database connection management
│   │   ├── query.py       # Synchronous query execution
│   │   └── async_query.py # Asynchronous query execution
│   ├── ddl/               # DDL generation for different databases
│   └── ui.py             # Gradio web interface
├── .env                  # Configuration file
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI GPT-4 for expert SQL assistance
- Anthropic Claude for code review
- Gradio for the web interface
- SQLAlchemy for database interactions

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.