import os
import paramiko
import anthropic
from dotenv import load_dotenv

def get_command_from_claude(goal):
    """Get SSH command from Claude based on the given goal"""
    client = anthropic.Anthropic()
    
    prompt = f"""Given the following goal for a Linux system, provide only the exact shell command needed (no explanations):
    Goal: {goal}
    Return only the command, nothing else."""
    
    message = client.messages.create(
        model="claude-3-sonnet-20241022",
        max_tokens=100,
        temperature=0,
        system="You are a Linux system administration expert. You specialize in reverse engineering. Use <thinking> tag to first think about the goal then use <commands><command> tag to provide the commands that will be executed. Use <status> tag to say either you are FINISHED or WORKING want to execute the commands and see the output. ",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return message.content

def create_ssh_session():
    """Create and return a paramiko SSH session using .env credentials"""
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials from .env
    host = os.getenv('SSH_HOST')
    username = os.getenv('SSH_USER')
    password = os.getenv('SSH_PASSWORD')
    
    if not all([host, username, password]):
        raise ValueError("Missing required SSH credentials in .env file")
    
    # Create SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect to remote host
        ssh.connect(
            hostname=host,
            username=username,
            password=password
        )
        print(f"Successfully connected to {host}")
        return ssh
    except Exception as e:
        print(f"Failed to connect: {str(e)}")
        return None

if __name__ == "__main__":
    # Create SSH session
    ssh_session = create_ssh_session()
    
    if ssh_session:
        try:
            # Get goal from user
            goal = input("Enter your goal (e.g., 'list all running processes'): ")
            
            # Get command from Claude
            command = get_command_from_claude(goal)
            print(f"\nGenerated command: {command}")
            
            # Execute the command
            confirm = input("\nDo you want to execute this command? (y/n): ")
            if confirm.lower() == 'y':
                stdin, stdout, stderr = ssh_session.exec_command(command)
                print("\nCommand output:")
                print(stdout.read().decode())
                if stderr.read():
                    print("\nErrors:")
                    print(stderr.read().decode())
        finally:
            ssh_session.close()
