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
    print(xml_str)
    
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

def get_command_from_claude(goal, previous_output=None):
    """Get SSH commands from Claude based on the given goal and optional previous output"""
    client = anthropic.Anthropic()
    
    if previous_output:
        prompt = f"""Previous command output:\n{previous_output}\n\nContinue with goal: {goal}"""
    else:
        prompt = goal
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=6000,
        temperature=0,
        system="You are a Linux system administration expert. You specialize in reverse engineering. Use <thinking> tag to first think about the goal and how to achieve it. Then use <commands> <command> nested tag to provide the commands that will be executed directly on the VM. <status>: Use this tag to indicate whether you have finished providing commands (FINISHED) or if you need to see the output of the commands to continue (PROCESSING). ",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return str(message.content)

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
        
        # Set up sudo session
        print("Setting up sudo session...")
        channel = ssh.get_transport().open_session()
        channel.get_pty()
        channel.exec_command('sudo -S -i')
        channel.send(password + '\n')
        # Wait for sudo session to be ready
        channel.recv_exit_status()
        
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
                        all_outputs = []
                        has_errors = False
                        
                        for cmd in parsed['commands']:
                            print(f"\nExecuting: {cmd}")
                            # Execute command in sudo shell
                            channel = ssh_session.get_transport().open_session()
                            channel.get_pty()
                            channel.exec_command(cmd)
                            output = channel.makefile().read().decode()
                            stderr_output = channel.makefile_stderr().read().decode()
                            channel.close()
                            
                            print("Output:")
                            print(output)
                            if stderr_output:
                                print("Errors:")
                                print(stderr_output)
                                has_errors = True
                            
                            all_outputs.append(f"Command: {cmd}\nOutput: {output}\nErrors: {stderr_output}")
                            
                            # If there's an error, immediately consult Claude
                            if stderr_output:
                                print("\nEncountered an error. Consulting Claude for assistance...")
                                combined_output = "\n---\n".join(all_outputs)
                                new_response = get_command_from_claude(goal, combined_output)
                                new_parsed = parse_claude_response(new_response)
                                
                                if new_parsed:
                                    print(f"\nNew thinking process: {new_parsed['thinking']}")
                                    if new_parsed['commands']:
                                        print("\nNew commands suggested:")
                                        for i, cmd in enumerate(new_parsed['commands'], 1):
                                            print(f"{i}. {cmd}")
                                        
                                        confirm = input("\nDo you want to execute these new commands? (y/n): ")
                                        if confirm.lower() == 'y':
                                            for new_cmd in new_parsed['commands']:
                                                print(f"\nExecuting: {new_cmd}")
                                                # Execute command in sudo shell
                                                new_channel = ssh_session.get_transport().open_session()
                                                new_channel.get_pty()
                                                new_channel.exec_command(new_cmd)
                                                print("Output:")
                                                new_output = new_channel.makefile().read().decode()
                                                print(new_output)
                                                new_stderr = new_channel.makefile_stderr().read().decode()
                                                new_channel.close()
                                                if new_stderr:
                                                    print("Errors:")
                                                    print(new_stderr)
                                                    # If there's still an error, continue consulting Claude
                                                    all_outputs.append(f"Command: {new_cmd}\nOutput: {new_output}\nErrors: {new_stderr}")
                                                    break
                                has_errors = True
                                break
                        
                        # Only check processing status if no errors occurred
                        if not has_errors and parsed['status'] == 'PROCESSING':
                            print("\nClaude requested to see the output. Sending results for further analysis...")
                            combined_output = "\n---\n".join(all_outputs)
                            
                            # Get new commands based on the output
                            print("\nAnalyzing output and generating new commands...")
                            new_response = get_command_from_claude(goal, combined_output)
                            new_parsed = parse_claude_response(new_response)
                            
                            if new_parsed:
                                print(f"\nNew thinking process: {new_parsed['thinking']}")
                                if new_parsed['commands']:
                                    print("\nAdditional commands suggested:")
                                    for i, cmd in enumerate(new_parsed['commands'], 1):
                                        print(f"{i}. {cmd}")
                                    
                                    confirm = input("\nDo you want to execute these additional commands? (y/n): ")
                                    if confirm.lower() == 'y':
                                        for cmd in new_parsed['commands']:
                                            print(f"\nExecuting: {cmd}")
                                            # Execute command in sudo shell
                                            channel = ssh_session.get_transport().open_session()
                                            channel.get_pty()
                                            channel.exec_command(cmd)
                                            print("Output:")
                                            output = channel.makefile().read().decode()
                                            print(output)
                                            stderr_output = channel.makefile_stderr().read().decode()
                                            channel.close()
                                            if stderr_output:
                                                print("Errors:")
                                                print(stderr_output)
                
                print("\n" + "="*50)
        finally:
            ssh_session.close()
