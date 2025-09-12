from abstract_apis import *
SIZE_DIFFS = {
    "K": {"K": 1, "M": 1/1000, "G": 1/1000**2, "T": 1/1000**3},
    "M": {"K": 1000, "M": 1, "G": 1/1000, "T": 1/1000**2},
    "G": {"K": 1000**2, "M": 1000, "G": 1, "T": 1/1000},
    "T": {"K": 1000**3, "M": 1000**2, "G": 1000, "T": 1}
}
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
    """Return dict of {filename: size_in_bytes} for all files in a directory."""
    cmd = f"find {directory} -type f -exec du -b {{}} +"
    if local:
        output = run_local_cmd(cmd=cmd, workdir=directory,outfile=None, shell=True, text=True, capture_output=True)
    else:
        output = run_remote_cmd(user_at_host=host, cmd=cmd,outfile=None, workdir=directory, shell=True, text=True, capture_output=True)
    file_sizes = {}
    for line in output.splitlines():
        if line.strip():
            size, path = line.split(maxsplit=1)
            try:
                file_sizes[os.path.basename(path)] = int(size)
            except:
                input(line)
    return file_sizes
def parse_size(size_str: str) -> int:
    """Convert human-readable du output into bytes."""
    size_str = size_str.strip().upper()
    multipliers = {"K": 1000, "M": 1000**2, "G": 1000**3, "T": 1000**4}
    if size_str[-1].isdigit():  # plain number, assume bytes
        return int(size_str)
    unit = size_str[-1]
    num = float(size_str[:-1])
    return int(num * multipliers.get(unit, 1))

class directoryHist:
    def __init__(self):
        self.history = {}
        self.abs_dir = os.path.dirname(os.path.abspath(__name__))
    def get_filepath(self,directory,local=True,outfile=False):
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
def run_size_cmd(directory,local=True,host=None,outfile=False):
    if local:
        is_exists = os.path.exists(directory)
        is_dir = os.path.isdir(directory)
    else:
        is_exists = is_dir = get_is_ssh_dir(directory,host=host)
    if is_exists and local and is_dir:
        outfile = dir_mgr.get_filepath(directory,local=local,outfile=outfile)
        cmd = get_size_cmd(directory)
        resp = run_local_cmd(cmd=cmd, workdir=directory, outfile=outfile,shell=True, text=True, capture_output=True)
        return resp 
    if not local and is_exists and is_dir:
        outfile = dir_mgr.get_filepath(directory,local=local,outfile=outfile)
        cmd = get_size_cmd(directory)
        resp = run_remote_cmd(user_at_host=host, cmd=cmd, workdir=directory, outfile=outfile,shell=True, text=True, capture_output=True)
        return resp        
    
    
def break_size_lines(size_output):
    size_lines = size_output.replace('\t',' ').split('\n')
    return [size_line for size_line in size_lines if size_line]
def get_directory_vars(directory,local=True,host=None,outfile=False):
    if isinstance(directory,dict):
        host = directory.get('host')
        dir_ = directory.get('directory')
        outfile = directory.get('outfile',outfile)
        local = directory.get('local', False if host else os.path.exists(dir_))
        directory = dir_
    src_dir = is_src_dir(directory)
    ssh_dir= get_is_ssh_dir(directory,host)
    outfile = dir_mgr.get_filepath(directory,local=local,outfile=outfile)
    if (local and src_dir) or (not local and ssh_dir):
        return directory,local,host,outfile
    return None,None,None,None
def get_sizes(src_directory, dst_directory,local=True,host=None):
    src_directory,src_local,src_host,src_outfile = get_directory_vars(src_directory,local=local,host=host)
    dst_directory,dst_local,dst_host,dst_outfile = get_directory_vars(src_directory,local=local,host=host)
    src_size_output = run_size_cmd(src_directory, local=src_local, host=src_host)
    if src_directory and dst_directory:
        dst_size_output = run_size_cmd(directory=dst_directory, local=dst_local, host=dst_host)

        srcs = break_size_lines(src_size_output)
        dsts = break_size_lines(dst_size_output)

        sizes = {"src": {}, "dst": {}, "needs": {}}

        for src in srcs:
            size, name = src.split()[0], src.split('/')[-1]
            sizes["src"][name] = parse_size(size)
        for dst in dsts:
            size, name = dst.split()[0], dst.split('/')[-1]
           
            sizes["dst"][name] = parse_size(size)

        for src_dir, src_size in sizes["src"].items():
            dst_size = sizes["dst"].get(src_dir)
            if dst_size is None or dst_size != src_size:
                diff_entry = {"src": src_size, "dst": dst_size}
                # Drill down at file level
                diff_entry["files"] = {
                    "src": get_file_sizes(os.path.join(src_directory, src_dir), local=src_local, host=src_host),
                    "dst": get_file_sizes(os.path.join(dst_directory, src_dir), local=dst_local, host=dst_host),
                }
                sizes["needs"][src_dir] = diff_entry
        return sizes
    return False
def get_size_cmd(directory):
    return f"du -h --max-depth=1  {directory}"
def transfer_missing(src_directory, dst_directory,local=True, host=None):
    """
    Compare local vs backup and transfer missing/different files to backup.
    """
    diffs = get_sizes(src_directory, dst_directory,local=local, host=host)
    if not diffs["needs"]:
        print("✅ Backup is already up to date.")
        return

    for directory, diff in diffs["needs"].items():
        src_path = os.path.join(src_directory, directory)
        dst_path = os.path.join(dst_directory, directory)

        # Ensure remote directory exists
        run_remote_cmd(
            user_at_host=host,
            cmd=f"mkdir -p {dst_path}",
            workdir=dst_directory,
            shell=True,
            text=True,
            capture_output=True,
        )

        # Sync only missing/different files using rsync
        cmd = f'rsync -avz --ignore-existing "{src_path}/" "{host}:{dst_path}/"'
        print(f"🔄 Syncing {src_path} → {host} {dst_path}")
        run_local_cmd(cmd=cmd, workdir=src_directory, shell=True, text=True, capture_output=True)

    print("✅ Transfer complete. Backup updated.")


