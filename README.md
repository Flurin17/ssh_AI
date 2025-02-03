# SSH Command Assistant with Claude

A Python tool that uses Claude AI to help execute and troubleshoot SSH commands on remote systems.

## Features

- Interactive command generation using Claude AI
- Automatic error detection and recovery
- Intelligent sudo privilege handling
- Continuous command processing until task completion
- Safe command execution with user confirmation

## Prerequisites

- Python 3.x
- Anthropic API key
- SSH access to target system

## Installation

1. Clone the repository:
```bash
git clone [your-repo-url]
```

2. Install required packages:
```bash
pip install paramiko anthropic python-dotenv
```

3. Create a `.env` file with your credentials:
```
SSH_HOST=your_host
SSH_USER=your_username
SSH_PASSWORD=your_password
ANTHROPIC_API_KEY=your_claude_api_key
```

## Usage

1. Run the script:
```bash
python main.py
```

2. Enter your goal in plain English (e.g., "list all running processes")
3. Review the suggested commands
4. Confirm execution
5. Claude will automatically handle any errors and suggest corrections

## Supported Commands

The tool automatically handles sudo privileges for common system administration commands:
- systemctl
- service
- mount/umount
- fdisk
- apt/apt-get
- dpkg
- User management (useradd, usermod, userdel)

## Error Handling

- Automatic error detection
- AI-powered error analysis
- Suggested corrective actions
- Continuous feedback loop until task completion

## Security Notes

- Stores credentials in .env file
- Automatically handles sudo privileges when needed
- Requires user confirmation before executing commands
- Uses SSH for secure remote execution

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Your chosen license]
