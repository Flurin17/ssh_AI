import os
import paramiko
import anthropic
import xml.etree.ElementTree as ET
from io import StringIO
from dotenv import load_dotenv

def parse_claude_response(response):
    """Parse XML tags from Claude's response"""
    # Wrap response in root element to make it valid XML
    xml_str = f"<root>{response}</root>"
    
    try:
        root = ET.fromstring(xml_str)
        thinking = root.find('thinking').text if root.find('thinking') is not None else ""
        commands = [cmd.text for cmd in root.findall('.//command')]
        status = root.find('status').text if root.find('status') is not None else "FINISHED"
        
        return {
            'thinking': thinking,
            'commands': commands,
            'status': status
        }
    except ET.ParseError:
        print("Failed to parse Claude's response as XML")
        return None

def get_command_from_claude(goal):
    """Get SSH commands from Claude based on the given goal"""
    client = anthropic.Anthropic()
    
    prompt = f"""Given the following goal for a Linux system, provide your response with XML tags:
    Goal: {goal}
    Use <thinking> to explain your approach, <commands> with nested <command> for each command, and <status> for execution status."""
    
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
            while True:
                # Get goal from user
                goal = input("\nEnter your goal (e.g., 'list all running processes') or 'exit' to quit: ")
                
                if goal.lower() == 'exit':
                    break
                
                # Get response from Claude
                response = get_command_from_claude(goal)
                parsed = parse_claude_response(response)
                
                if parsed:
                    print(f"\nThinking process: {parsed['thinking']}")
                    print("\nGenerated commands:")
                    for i, cmd in enumerate(parsed['commands'], 1):
                        print(f"{i}. {cmd}")
                    
                    # Execute commands if user confirms
                    confirm = input("\nDo you want to execute these commands? (y/n): ")
                    if confirm.lower() == 'y':
                        for cmd in parsed['commands']:
                            print(f"\nExecuting: {cmd}")
                            stdin, stdout, stderr = ssh_session.exec_command(cmd)
                            print("Output:")
                            print(stdout.read().decode())
                            stderr_output = stderr.read().decode()
                            if stderr_output:
                                print("Errors:")
                                print(stderr_output)
                        
                        # Check if Claude wants to see the output
                        if parsed['status'] == 'WORKING':
                            print("\nClaude requested to see the output. Sending results for further analysis...")
                            # Here you could implement logic to send results back to Claude
                            # for additional command generation if needed
                
                print("\n" + "="*50)
        finally:
            ssh_session.close()
