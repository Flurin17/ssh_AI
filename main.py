import os
import paramiko
from dotenv import load_dotenv

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
            # Example command execution
            stdin, stdout, stderr = ssh_session.exec_command('ls -la')
            print("\nCommand output:")
            print(stdout.read().decode())
        finally:
            ssh_session.close()
