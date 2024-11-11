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
roms_path = '/home/pi/RetroPie/roms/'
local_backup_path = '/data'

logging.info(f'Reading environment variables from {os.environ}')

# Read environment variables
if 'RETROPIE_HOST' in os.environ:
    hostname = os.environ['RETROPIE_HOST']
    logging.info(f'Using hostname from environment variable: {hostname}')
if 'RETROPIE_USER' in os.environ:
    username = os.environ['RETROPIE_USER']
    logging.info(f'Using username from environment variable: {username}')
if 'RETROPIE_PASS' in os.environ:
    password = os.environ['RETROPIE_PASS']
    logging.info('Using password from environment variable')
if 'RETROPIE_PORT' in os.environ:
    port = int(os.environ['RETROPIE_PORT'])
    logging.info(f'Using port from environment variable: {port}')
if 'RETROPIE_ROMS_PATH' in os.environ:
    roms_path = os.environ['RETROPIE_ROMS_PATH']
    logging.info(f'Using roms path from environment variable: {roms_path}')

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

# Check if path is a directory or not
def isdir(path, sftp):
    try:
        return S_ISDIR(sftp.stat(path).st_mode)
    except IOError:
        #Path does not exist, so by definition not a directory
        return False

# Recursively search for files with the given extensions
# Returns a list of files with the given extensions
# Files are returned with their full path
def recursive_search(sftp, path, list_search_extentions):
    # no sftp.walk functionality in paramiko
    # so we need to recursively search for files
    # with the given extensions
    try:
        total_file_size = 0
        files = []
        for file in sftp.listdir(path):
            fullpath = os.path.join(path, file)
            if isdir(fullpath, sftp):
                #logging.info(f'Found directory: {fullpath}, recursing')
                files += recursive_search(sftp, fullpath, list_search_extentions)
            else: 
                for ext in list_search_extentions:
                    # file extensions have regex-like syntax (.state.*) so we need to check for the extension variations
                    file_ext = file.split('.')[-1]
                    file_ext = f'.{file_ext}'
                    #logging.info(f'Checking file {file} with extension {file_ext} against {ext}')
                    if file_ext == ext or file_ext.startswith(ext):
                        #logging.info(f'Found file: {fullpath}')
                        files.append(fullpath)
                        total_file_size += sftp.stat(fullpath).st_size
        logging.info(f'Found {len(files)} files with total size {total_file_size} bytes on RetroPie at {hostname}')  
        return files
    
    except Exception as e:
        logging.error(f'Failed to search files: {e}')
        return []

# Download files from the list of files
# Returns a list of downloaded files
# Files are downloaded to the local_backup_path
def download_files(sftp, files):
    downloaded_files = []
    for file in files:
        try:
            #strip /home/pi/RetroPi/roms/ from the file path
            filename = file.replace(roms_path, '')
            local_file = os.path.join(local_backup_path, filename)
            local_file_dir = os.path.dirname(local_file)

            # Check if existing file is the same size as remote file
            # If not, new saves have been made since last check and we need to archive the old file
            if os.path.exists(local_file):
                #logging.info(f'Local file {local_file} already exists, checking size')
                remote_file_size = sftp.stat(file).st_size
                local_file_size = os.path.getsize(local_file)
                if remote_file_size == local_file_size:
                    #logging.info(f'Local file {local_file} is the same size as remote file, skipping')
                    continue
                else:
                    logging.info(f'Local file {local_file} is different size than remote file, archiving')
                    os.rename(local_file, f'{local_file}.bak.{datetime.now().strftime("%Y%m%d%H%M%S")}')
            else: 
                logging.info(f'Local file {local_file} does not exist, creating directory')
                os.makedirs(os.path.dirname(local_file), exist_ok=True)

            # Download the file
            logging.info(f'Downloading remote save file {file} to {local_file_dir}')
            sftp.get(file, local_file)
            downloaded_files.append(local_file)

        except Exception as e:
            logging.error(f'Failed to download files: {e}')
    return downloaded_files             

# Report the number and size of files stored locally
# Returns a list of tuples by game system with the number of files and total size
# Example: gba: (2, 1024), snes: (5, 2048)
# /data/gba/game1.state, /data/gba/game1.srm, /data/gba/game2.state.bak.20210101120000
# don't report /data as a system
def report_local_files():
    try:
        total_file_size = 0
        save_files_by_system = [] # list of tuples by system with number of files and total size
        for root, dirs, files in os.walk(local_backup_path):
            if root == local_backup_path:
                continue
            system = root.split('/')[-1]
            system_files = len(files)
            system_size = sum(os.path.getsize(os.path.join(root, name)) for name in files)
            total_file_size += system_size
            save_files_by_system.append((system, system_files, system_size))
            logging.info(f'{save_files_by_system}')
        for system, files, size in save_files_by_system:
            file_size_readable = sizeof_fmt(size)
            logging.info(f'{system}: {files} files, {file_size_readable}')
        total_file_size = sizeof_fmt(total_file_size)
        logging.info(f'Found {len(save_files_by_system)} systems with {len(files)} files and total size {total_file_size} stored locally')
    
    except Exception as e:
        logging.error(f'Failed to report local files: {e}')

# format file size in human readable format
# This function takes an integer representing the file size in bytes
# and returns a human readable string with the size in KB, MB, GB, etc.
def sizeof_fmt(num, suffix='B'): 
    for unit in ['','K','M','G','T','P','E','Z']: 
        if abs(num) < 1024.0: 
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Y', suffix)

def main():
    while True:
        client = ssh_connect()
        if client:
            sftp = client.open_sftp()
            files = recursive_search(sftp, roms_path, ['.state', '.srm'])
            logging.info(f'Found {len(files)} save files')
            downloaded_files = download_files(sftp, files)
            logging.info(f'Downloaded {len(downloaded_files)} new or updated save files')
            client.close()
            report_local_files()
            logging.info('Sleeping for 1 hour')
        else:
            logging.error('Failed to establish SSH connection, sleeping for 1 hour')
        
        time.sleep(3600)  # Check for new files every hour

if __name__ == '__main__':
    main()