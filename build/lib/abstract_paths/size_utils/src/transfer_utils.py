import os, shlex, sys
from .cmd_utils import *
from .dir_utils import *
from .size_utils import *

def safe_exit(message: str, code: int = 1):
    """Print error and exit safely."""
    print(f"❌ ERROR: {message}")
    sys.exit(code)

def rsync_with_sudo(src_path: str, dst_path: str, host: str = None, password: str = None) -> str:
    """
    Rsync with sudo on source (and optionally target).
    """
    dest = f"{host+':' if host else ''}{dst_path}/"
    cmd = (
        f'echo {shlex.quote(password or "1")} | '
        f'sudo -S -p "" rsync -aAXvz --super --numeric-ids "{src_path}/" "{dest}"'
    )
    print(f"⚡ Running: {cmd}")
    return run_local_cmd(cmd)

def transfer_missing(src_directory, dst_directory, local=True, host=None, src_password=None):
    """
    Compare local vs backup and transfer missing/different files to backup.
    If target missing → copy whole tree.
    Otherwise, sync only what differs.
    """
    try:
        # Extract dicts safely
        src_path = src_directory["directory"] if isinstance(src_directory, dict) else src_directory
        dst_path = dst_directory["directory"] if isinstance(dst_directory, dict) else dst_directory

        # Check if destination exists
        if local:
            dst_exists = os.path.exists(dst_path)
        else:
            resp = run_remote_cmd(user_at_host=host, cmd=f"test -d {shlex.quote(dst_path)} && echo EXISTS || echo MISSING")
            dst_exists = "EXISTS" in str(resp)

        if not dst_exists:
            print(f"📂 Target missing. Copying {src_path} → {host+':' if host else ''}{dst_path}")
            run_remote_cmd(user_at_host=host, cmd=f"mkdir -p {shlex.quote(dst_path)}")
            result = rsync_with_sudo(src_path, dst_path, host=host, password=src_password)
            if "Permission denied" in result or "rsync error" in result:
                safe_exit(f"Failed to copy {src_path} → {dst_path}")
            print("✅ Transfer complete.")
            return

        # Do diff sync
        diffs = get_sizes(src_directory, dst_directory, local=local, host=host)
        if not diffs or not diffs.get("needs"):
            print("✅ Backup is already up to date.")
            return

        skipped = {}
        for directory in diffs["needs"]:
            sub_src = os.path.join(src_path, directory)
            sub_dst = os.path.join(dst_path, directory)

            run_remote_cmd(user_at_host=host, cmd=f"mkdir -p {shlex.quote(sub_dst)}")

            print(f"🔄 Syncing {sub_src} → {host+':' if host else ''}{sub_dst}")
            result = rsync_with_sudo(sub_src, sub_dst, host=host, password=src_password)

            if "Permission denied" in result or "rsync error" in result:
                print(f"❌ Failed to copy {sub_src}")
                skipped[sub_src] = result

        if skipped:
            safe_exit(f"Some paths could not be copied: {list(skipped.keys())}")
        else:
            print("✅ Transfer complete. Backup updated.")

    except Exception as e:
        safe_exit(str(e))
