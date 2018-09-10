from os import mkdir, path
from shutil import copyfile
import subprocess

def send_snapshot_local(snapshot, destination, parent=None):
    """Send/receive a snapshot to a another disk on the same machine.

    Keyword arguments:
    snapshot -- the Snapshot instance to transfer
    destination -- base directory of the remote end
    parent -- provide parent Snapshot for incremental updates (optional)
    """

    snap_id = path.basename(snapshot.path)
    snap_dir = "{}/{}".format(destination, snap_id)

    subprocess.run(["btrfs", "subvolume", "create", destination])
    mkdir(snap_dir)

    for dir in snapshot.dirs:
        # https://stackoverflow.com/questions/7353054/running-a-command-line-containing-pipes-and-displaying-result-to-stdout
        send = subprocess.Popen(["btrfs", "send", "{}/{}".format(snapshot.path, path.basename(dir))], stdout=subprocess.PIPE)
        recv = subprocess.Popen(["btrfs", "receive", snap_dir], stdin=send.stdout, stdout=subprocess.PIPE)

        send.stdout.close()
        output, err = recv.communicate()

    # Do this last to mark that the snapshot succeeded.
    copyfile("{}/snapshot.ini".format(snapshot.path), "{}/snapshot.ini".format(snap_dir))
