import subprocess, shlex
from typing import Optional
from abstract_apis import *

def execute_cmd(cmd: str, outfile: Optional[str] = None,
                workdir: str = None, shell: bool = True, **kwargs) -> str:
    """
    Run command, capture stdout+stderr, decode safely as UTF-8.
    """
    proc = subprocess.run(cmd,
                          shell=shell,
                          cwd=workdir,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,
                          text=False)  # capture raw bytes
    output = proc.stdout.decode("utf-8", errors="ignore")

    if outfile:
        try:
            with open(outfile, "w", encoding="utf-8", errors="ignore") as f:
                f.write(output)
        except Exception:
            pass
    return output

def run_local_cmd(cmd: str, password: str=None, workdir: str = None,
                   outfile: Optional[str] = None, **kwargs) -> str:
    """
    Run local command with sudo, suppressing the password prompt output.
    """
    cmd = f"cd {shlex.quote(workdir)} && {cmd}" if workdir else cmd
    # -p "" prevents `[sudo] password for user:` in output
    if password:
        cmd = f"echo {shlex.quote(password)} | sudo -S -p \"\" bash -c {shlex.quote(cmd)}"
    return execute_cmd(cmd, outfile=outfile)

def run_remote_cmd(user_at_host: str, cmd: str, password: str=None,
                    workdir: str = None, outfile: Optional[str] = None, **kwargs) -> str:
    remote_cmd = f"cd {shlex.quote(workdir)} && {cmd}" if workdir else cmd
    if password:
        remote_cmd = f"echo {shlex.quote(password)} | sudo -S -p \"\" bash -c {shlex.quote(remote_cmd)}"
    ssh_cmd = f"ssh {shlex.quote(user_at_host)} {shlex.quote(remote_cmd)}"
    return execute_cmd(ssh_cmd, outfile=outfile)
run_remote_sudo = run_remote_cmd
run_local_sudo = run_local_cmd
