from __future__ import annotations
from abstract_apis import *
from abstract_utilities.cmd_utils import get_env_value,get_sudo_password,get_sudo_password,get_env_value,cmd_run_sudo
SIZE_DIFFS = {
    "K": {"K": 1, "M": 1/1000, "G": 1/1000**2, "T": 1/1000**3},
    "M": {"K": 1000, "M": 1, "G": 1/1000, "T": 1/1000**2},
    "G": {"K": 1000**2, "M": 1000, "G": 1, "T": 1/1000},
    "T": {"K": 1000**3, "M": 1000**2, "G": 1000, "T": 1}
}
import pexpect

import subprocess, shlex, os
from typing import Optional
import subprocess, shlex, os
from typing import Optional
import pexpect
from abstract_utilities import read_from_file
import subprocess, pexpect, os
from abstract_security.envy_it import find_and_read_env_file, get_env_value

def get_sudo_password(key: str = "SUDO_PASSWORD") -> str:
    return find_and_read_env_file(key=key)

def print_cmd(input: str, output: str, **kwargs) -> None:
    print(f"Command: {input}")
    print("Output:")
    print(output)

def cmd_run(cmd: str, print_output: bool = False, **kwargs) -> str:
    """
    Run a shell command, return its combined stdout+stderr.
    """
    proc = subprocess.run(cmd, shell=True, text=True,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    output = proc.stdout or ""
    if print_output:
        print(output.strip())
    return output.strip()

def cmd_run_sudo(cmd: str, password: str = None, key: str = None,
                 print_output: bool = False, **kwargs) -> str:
    """
    Run a sudo command, feeding password automatically.
    """
    if not password:
        if key:
            password = get_env_value(key)
        else:
            password = get_sudo_password()
    full_cmd = f'echo "{password}" | sudo -S -k {cmd}'
    return cmd_run(full_cmd, print_output=print_output)

def pexpect_cmd_with_args(command: str, child_runs: list,
                          print_output: bool = False, **kwargs) -> str:
    """
    Run a command with pexpect, responding to prompts.
    """
    child = pexpect.spawn(command, encoding="utf-8")

    for each in child_runs:
        child.expect(each["prompt"])
        if each.get("pass") is not None:
            child.sendline(each["pass"])
        else:
            args = {}
            if "key" in each and each["key"]:
                args["key"] = each["key"]
            if "env_path" in each and each["env_path"]:
                args["start_path"] = each["env_path"]
            child.sendline(get_env_value(**args))

    child.expect(pexpect.EOF)
    output = child.before or ""
    if print_output:
        print(output.strip())
    return output.strip()
# ---------------- base exec ----------------
def execute_cmd(*args, outfile: Optional[str]=None, **kwargs) -> str:
    proc = subprocess.run(*args, **kwargs)
    output = (proc.stdout or "") + (proc.stderr or "")
    if outfile:
        try:
            with open(outfile, "w", encoding="utf-8", errors="ignore") as f:
                f.write(output)
        except Exception:
            pass
    return output

# ---------------- local/remote run ----------------
def run_local_cmd(cmd: str, workdir: str=None, outfile: Optional[str]=None,
                  shell=True, text=True, capture_output=True, **kwargs) -> str:
    return execute_cmd(cmd, outfile=outfile, shell=shell, cwd=workdir,
                       text=text, capture_output=capture_output)

def run_remote_cmd(user_at_host: str, cmd: str, workdir: str=None,
                   outfile: Optional[str]=None, shell=True, text=True,
                   capture_output=True, **kwargs) -> str:
    remote_cmd = f"cd {shlex.quote(workdir)} && {cmd}" if workdir else cmd
    full = f"ssh {shlex.quote(user_at_host)} {shlex.quote(remote_cmd)}"
    return execute_cmd(full, outfile=outfile, shell=shell, text=text, capture_output=capture_output)

# ---------------- sudo wrappers ----------------
def run_local_sudo(cmd: str, password: str, workdir: str = None,
                   shell=True, text=True, capture_output=True, **kwargs) -> str:
    """
    Run locally with sudo, injecting password via stdin.
    """
    if workdir:
        wrapped = f"cd {shlex.quote(workdir)} && {cmd}"
    else:
        wrapped = cmd
    full = f'echo {shlex.quote(password)} | sudo -S bash -c {shlex.quote(wrapped)}'
    proc = subprocess.run(full, shell=True, text=True,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.stdout.strip()

def run_remote_sudo(user_at_host: str, cmd: str, password: str,
                    workdir: str = None, shell=True, text=True,
                    capture_output=True, **kwargs) -> str:
    """
    Run command on remote host with sudo, injecting password via stdin.
    """
    if workdir:
        wrapped = f"cd {shlex.quote(workdir)} && {cmd}"
    else:
        wrapped = cmd
    remote_cmd = f"echo {shlex.quote(password)} | sudo -S bash -c {shlex.quote(wrapped)}"
    ssh_cmd = f"ssh {shlex.quote(user_at_host)} {shlex.quote(remote_cmd)}"
    proc = subprocess.run(ssh_cmd, shell=True, text=True,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.stdout.strip()

def run_size_cmd(directory: str, local=True, host=None,
                 password: str = None, key: str = None, **kwargs) -> str:
    """
    Run `du -h --max-depth=1` on local or remote, always return stdout text.
    """
    cmd = "du -h --max-depth=1"
    if local:
        if password:
            return run_local_sudo(cmd, password=password, workdir=directory)
        else:
            full = f"cd {shlex.quote(directory)} && {cmd}"
            proc = subprocess.run(full, shell=True, text=True,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)
            return proc.stdout.strip()
    else:
        pw = password or (get_env_value(key) if key else get_sudo_password())
        return run_remote_sudo(user_at_host=host, cmd=cmd,
                               password=pw, workdir=directory)


# Aliases
run_ssh_cmd = run_remote_cmd
run_sudo_cmd = run_local_sudo
run_ssh_sudo_cmd = run_remote_sudo


def get_sudo_cmd(
    cmd: str,
    password: str = None,
    key: str = None,
    host: str = None,
    use_su: bool = False,
    fallback_pexpect: bool = True,
    **kwargs
):
    """
    Build or execute a command string that runs with root privileges.

    Args:
        cmd (str): Command to run.
        password (str, optional): Sudo password. Defaults to None.
        key (str, optional): Env key for sudo password. Defaults to None.
        host (str, optional): Remote host (if provided, wraps with ssh).
        use_su (bool): If True, use 'sudo su -c "<cmd>"' instead of plain sudo.
        fallback_pexpect (bool): If True, will attempt interactive login with pexpect
                                 if piped password is rejected.

    Returns:
        str | tuple: Command string (when host/local) OR (exitcode, output) if fallback triggered.
    """
    # Resolve password
    if password:
        pw = password
    elif key:
        pw = get_env_value(key)
    else:
        pw = get_sudo_password()

    if use_su:
        sudo_cmd = f'sudo -S -k su -c "{cmd}"'
    else:
        sudo_cmd = f'sudo -S -k {cmd}'

    # Remote
    if host:
        # Pipe password with ssh -t (allocate tty)
        piped = f'ssh -t {host} "echo \\"{pw}\\" | {sudo_cmd}"'
        if not fallback_pexpect:
            return piped

        # Fallback: use pexpect to answer prompt
        try:
            child = pexpect.spawn(f"ssh -t {host} {sudo_cmd}")
            child.expect("password for", timeout=5)
            child.sendline(pw)
            child.expect(pexpect.EOF)
            return (child.exitstatus, child.before.decode())
        except Exception as e:
            return (1, f"pexpect error: {e}")

    # Local
    else:
        piped = f'echo "{pw}" | {sudo_cmd}'
        return piped
import pexpect



def convert_size(value: float, from_unit: str, to_unit: str, binary: bool = False) -> float:
    """
    Convert file size between K, M, G, T.
    :param value: numeric size
    :param from_unit: 'K', 'M', 'G', 'T'
    :param to_unit: 'K', 'M', 'G', 'T'
    :param binary: if True, use 1024 instead of 1000
    """
    step = 1024 if binary else 1000
    units = ["K", "M", "G", "T"]
    if from_unit not in units or to_unit not in units:
        raise ValueError(f"Units must be one of {units}")
    power = units.index(from_unit) - units.index(to_unit)
    return value * (step ** power)
def get_file_sizes(directory, local=True, host=None):
    """
    Return dict of {filepath: size_in_bytes} for all files in a directory.
    Handles spaces and special characters safely.
    """
    cmd = f"find {directory} -type f -print0 | xargs -0 du -b 2>/dev/null"
    if local:
        output = run_local_cmd(cmd=cmd, workdir=directory, outfile=None,
                               shell=True, text=True, capture_output=True)
    else:
        output = run_remote_cmd(user_at_host=host, cmd=cmd, workdir=directory,
                                outfile=None, shell=True, text=True, capture_output=True)

    file_sizes = {}
    for line in output.splitlines():
        if not line.strip() or "Permission denied" in line:
            continue
        # du -b always prints: "<size>\t<path>"
        try:
            size, path = line.split("\t", 1)
            file_sizes[path] = int(size)
        except ValueError:
            continue
    return file_sizes
def parse_size(size_str: str) -> int:
    """Convert human-readable du output into bytes."""
    size_str = size_str.strip().upper()
    multipliers = {"K": 1000, "M": 1000**2, "G": 1000**3, "T": 1000**4}
    if not size_str or not size_str[0].isdigit():
        # ignore lines that aren't proper size tokens (like 'DU')
        return 0
    if size_str[-1].isdigit():  # plain number, assume bytes
        return int(size_str)
    unit = size_str[-1]
    try:
        num = float(size_str[:-1])
    except ValueError:
        return 0
    return int(num * multipliers.get(unit, 1))

class directoryHist:
    def __init__(self):
        self.history = {}
        self.abs_dir = os.path.dirname(os.path.abspath(__name__))
    def get_filepath(self,directory,local=True,outfile=None):
        if outfile == False:
            return None
        file_path = outfile
        if not isinstance(outfile,str):
            basename = os.path.basename(directory)
            basepath = os.path.join(self.abs_dir,basename)
            file_path = f"{basepath}.txt"
            key = f"{directory}_local"
            if not local:
                key = f"{directory}_ssh"
                
            if os.path.exists(file_path):
                if self.history.get(key) != file_path:
                    i=0
                    while True:
                        nubasepath=f"{basepath}_{i}"
                        file_path = f"{nubasepath}.txt"
                        if not os.path.exists(file_path):
                            break
                        i+=1
        self.history[key] = file_path
        return file_path
dir_mgr = directoryHist()
def get_outfile(directory):
    return dir_mgr.get_filepath(directory)
def get_is_ssh_dir(directory,host,outfile=False):
    outfile = dir_mgr.get_filepath(directory,local=False,outfile=outfile)
    resp = run_remote_cmd(user_at_host=host, cmd=f"ls {directory}", workdir=directory, outfile=outfile,shell=True, text=True, capture_output=True)
    return not resp.endswith('No such file or directory')
def is_src_dir(directory):
    return directory and os.path.isdir(str(directory))

    
def break_size_lines(size_output):
    size_lines = size_output.replace('\t',' ').split('\n')
    return [size_line for size_line in size_lines if size_line]
def get_directory_vars(directory,local=True,host=None,outfile=False, password: str = None, key: str = None, output_text: str = None,use_su:str=False):
    if isinstance(directory,dict):
        host = directory.get('host')
        dir_ = directory.get('directory')
        password= directory.get('password',password)
        key= directory.get('key',key)
        use_su= directory.get('use_su',use_su)
        output_text= directory.get('output_text',output_text)
        outfile = directory.get('outfile',outfile)
        local = directory.get('local', False if host else os.path.exists(dir_))
        directory = dir_
    src_dir = is_src_dir(directory)
    ssh_dir= get_is_ssh_dir(directory,host)
    outfile = dir_mgr.get_filepath(directory,local=local,outfile=outfile)
    if (local and src_dir) or (not local and ssh_dir):
        return directory,local,host,outfile,password, key, output_text,use_su
    return None,None,None,None,None,None,None,None
def get_sizes(src_directory, dst_directory, local=True, host=None, password: str = None, key: str = None, output_text: str = None,use_su:str=False):
    src_directory,src_local,src_host,src_outfile, src_password, src_key, src_output_text, src_use_su = get_directory_vars(src_directory,local=local,host=host,password=password,key=key,output_text=output_text,use_su=use_su)
    dst_directory,dst_local,dst_host,dst_outfile, dst_password, dst_key, dst_output_text, dst_use_su = get_directory_vars(dst_directory,local=local,host=host,password=password,key=key,output_text=output_text,use_su=use_su)

    src_size_output = run_size_cmd(src_directory, local=src_local, host=src_host,password=src_password,key=src_key,output_text=src_output_text,use_su=src_use_su)
    if src_directory and dst_directory:
        dst_size_output = run_size_cmd(directory=dst_directory, local=dst_local, host=dst_host,password=dst_password,key=dst_key,output_text=dst_output_text,use_su=dst_use_su)

        srcs = break_size_lines(src_size_output)
        dsts = break_size_lines(dst_size_output)

        sizes = {"src": {}, "dst": {}, "needs": {}}

        for src in srcs:
            size, name = src.split()[0], src.split('/')[-1]
            sizes["src"][name] = parse_size(size)

        for dst in dsts:
            size, name = dst.split()[0], dst.split('/')[-1]
            sizes["dst"][name] = parse_size(size)

        # Compare src vs dst
        for src_dir, src_size in sizes["src"].items():
            dst_size = sizes["dst"].get(src_dir)
            if dst_size is None or dst_size != src_size:
                diff_entry = {"src": src_size, "dst": dst_size}
                diff_entry["files"] = {
                    "src": get_file_sizes(os.path.join(src_directory, src_dir), local=src_local, host=src_host),
                    "dst": get_file_sizes(os.path.join(dst_directory, src_dir), local=dst_local, host=dst_host),
                }
                sizes["needs"][src_dir] = diff_entry

        return sizes
    return False

def run_size_cmd(directory, local=True, host=None, outfile=False,
                 password: str = None, key: str = None,
                 output_text: str = None, use_su: bool = False):

    if local:
        is_exists = os.path.exists(directory)
        is_dir = os.path.isdir(directory)
    else:
        is_exists = is_dir = get_is_ssh_dir(directory, host=host)

    if not (is_exists and is_dir):
        return None
    input(directory)
    outfile = dir_mgr.get_filepath(directory, local=local)
    input(outfile)
    cmd = "du -h --max-depth=1"   # <-- only base command, no directory
    resp =cmd_run_sudo(cmd,password=password,output_text=outfile)
    input(resp)
    if local:
        # local: just cd into directory and run

        resp =cmd_run_sudo(cmd,password=password,output_text=outfile)
        input(read_from_file(outfile))
    else:
        # remote with sudo
        resp = run_remote_sudo(
            user_at_host=host,
            cmd=cmd,               # let workdir handle directory
            workdir=directory,
            outfile=outfile,
            shell=True, text=True, capture_output=True,
            password=password, key=key, use_su=use_su
        )
    return resp

def transfer_missing(src_directory, dst_directory, local=True, host=None):
    """
    Compare local vs backup and transfer missing/different files to backup.
    Try normal rsync first, fall back to sudo rsync if permission denied.
    """
    diffs = get_sizes(src_directory, dst_directory, local=local, host=host)
    if not diffs or not diffs.get("needs"):
        print("✅ Backup is already up to date.")
        return

    skipped = {}

    for directory, diff in diffs["needs"].items():
        src_path = os.path.join(src_directory if isinstance(src_directory, str) else src_directory["directory"], directory)
        dst_path = os.path.join(dst_directory if isinstance(dst_directory, str) else dst_directory["directory"], directory)

        # Ensure remote directory exists
        run_remote_cmd(
            user_at_host=host,
            cmd=f"mkdir -p {dst_path}",
            workdir=os.path.dirname(dst_path),
            shell=True,
            text=True,
            capture_output=True,
        )

        # Base rsync command
        cmd = f'rsync -avz --ignore-existing "{src_path}/" "{host}:{dst_path}/"'
        print(f"🔄 Syncing {src_path} → {host}:{dst_path}")

        result = run_local_cmd(cmd=cmd, workdir=os.path.dirname(src_path), shell=True, text=True, capture_output=True)

        if "Permission denied" in str(result):
            print(f"⚠️ Permission denied, retrying with sudo: {src_path}")
            cmd_sudo = f'sudo rsync -avz --ignore-existing "{src_path}/" "{host}:{dst_path}/"'
            result = run_local_cmd(cmd=cmd_sudo, workdir=os.path.dirname(src_path), shell=True, text=True, capture_output=True)

            if "Permission denied" in str(result):
                print(f"❌ Still could not copy {src_path}")
                skipped[src_path] = result

    print("✅ Transfer complete. Backup updated.")
    if skipped:
        print("⚠️ The following paths still could not be copied:")
        for k in skipped:
            print(f"   - {k}")
dst_directory = {
    "directory":"/mnt/24T/consolidated/backups/phones/ubuntu_backups/ubuntu_main/home",
    "local":False, "host":"solcatcher", "password":"ANy1KAn@!23"
}
print("Remote sizes:")
print(run_size_cmd(**dst_directory))
src_directory = {"directory":"/home", "password":"1"}

print("Local sizes:")
print(run_size_cmd(**src_directory))

print("Remote sizes:")
print(run_size_cmd(**dst_directory))

def replicate_directory_structure(src_directory, dst_directory,local=True, host=None):
    src_directory,src_local,src_host,src_outfile = get_directory_vars(src_directory,local=local,host=host)
    dst_directory,dst_local,dst_host,dst_outfile = get_directory_vars(src_directory,local=local,host=host)
