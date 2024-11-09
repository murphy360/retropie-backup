import os
import paramiko
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(filename='/data/retropie_backup.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# SSH configuration
hostname = 'your_retropie_ip'
port = 22
username = 'pi'
password = 'raspberry'
remote_path = '/home/pi/RetroPie/roms/'
local_backup_path = '/data/'

# Read environment variables
if 'RETROPIE_HOST' in os.environ:
    hostname = os.environ['RETROPIE_HOST']
if 'RETROPIE_USER' in os.environ:
    username = os.environ['RETROPIE_USER']
if 'RETROPIE_PASS' in os.environ:
    password = os.environ['RETROPIE_PASS']

def ssh_connect():
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, port, username, password)
        logging.info('SSH connection established')
        return client
    except Exception as e:
        logging.error(f'Failed to establish SSH connection: {e}')
        return None
    
def recursive_search(client, path, list_search_extentions):
    # no sftp.walk functionality in paramiko
    # so we need to recursively search for files
    # with the given extensions
    try:
        sftp = client.open_sftp()
        files = []
        for file in sftp.listdir(path):
            if sftp.isdir(os.path.join(path, file)):
                files += recursive_search(client, os.path.join(path, file), list_search_extentions)
            else:
                for ext in list_search_extentions:
                    if file.endswith(ext):
                        files.append(os.path.join(path, file))
                        logging.info(f'Found file: {os.path.join(path, file)}')
        return files
    except Exception as e:
        logging.error(f'Failed to search files: {e}')
        return []

def download_files(client):
    try:
        sftp = client.open_sftp()
        for dirpath, dirnames, filenames in sftp.walk(remote_path):
            for filename in filenames:
                remote_file = os.path.join(dirpath, filename)
                local_file = os.path.join(local_backup_path, datetime.now().strftime('%Y%m%d_%H%M%S_') + filename)
                sftp.get(remote_file, local_file)
                logging.info(f'Downloaded {remote_file} to {local_file}')
        sftp.close()
    except Exception as e:
        logging.error(f'Failed to download files: {e}')

def main():
    while True:
        client = ssh_connect()
        if client:
            #download_files(client)
            files = recursive_search(client, remote_path, ['.state', '.srm'])
            logging.info(f'Found {len(files)} files')
            client.close()
        time.sleep(3600)  # Check for new files every hour

if __name__ == '__main__':
    main()