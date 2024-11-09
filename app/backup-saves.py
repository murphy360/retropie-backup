import os
import paramiko
import time
import logging
from stat import S_ISDIR
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
local_backup_path = '/data'

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


def isdir(path, sftp):
    try:
        return S_ISDIR(sftp.stat(path).st_mode)
    except IOError:
        #Path does not exist, so by definition not a directory
        return False

def recursive_search(sftp, path, list_search_extentions):
    # no sftp.walk functionality in paramiko
    # so we need to recursively search for files
    # with the given extensions
    try:
        
        files = []
        for file in sftp.listdir(path):
            fullpath = os.path.join(path, file)
            if isdir(fullpath, sftp):
                logging.info(f'Found directory: {fullpath}, recursing')
                files += recursive_search(sftp, fullpath, list_search_extentions)
            else: 
                for ext in list_search_extentions:
                    if file.endswith(ext):
                        files.append(fullpath)
                        logging.info(f'Found save file: {fullpath}')
        return files
    
    except Exception as e:
        logging.error(f'Failed to search files: {e}')
        return []

def download_files(sftp, files):
    for file in files:
        try:
            logging.info(f'Downloading remote save {file} to {local_backup_path}')
            #strip /home/pi/RetroPi/roms/ from the file path
            filename = file.replace(remote_path, '')
            local_file = os.path.join(local_backup_path, filename)
            
            local_file_dir = os.path.dirname(local_file)
            logging.info(f'Creating local directory {local_file_dir}')
            os.makedirs(os.path.dirname(local_file), exist_ok=True)
            logging.info(f'Downloading remote save file {file} to {local_file_dir}')
            sftp.get(file, local_file)
            
        except Exception as e:
            logging.error(f'Failed to download files: {e}')
            
    

def main():
    while True:
        client = ssh_connect()
        if client:
            #download_files(client)
            sftp = client.open_sftp()
            files = recursive_search(sftp, remote_path, ['.state', '.srm'])
            logging.info(f'Found {len(files)} files')
            download_files(sftp, files)
            client.close()
        logging.info('Sleeping for 1 hour')
        time.sleep(3600)  # Check for new files every hour


if __name__ == '__main__':
    main()