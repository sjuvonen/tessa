from os import mkdir, path
from shutil import copyfile
import subprocess

def send_snapshot(snapshot, remote_profile, parent=None):
    methods = {
        remote_profile.TYPE_LOCAL: send_snapshot_local,
        remote_profile.TYPE_SSH: send_snapshot_ssh
    }

    func = methods[remote_profile.type]
    func(snapshot, remote_profile, parent)

def send_snapshot_local(snapshot, remote_profile, parent=None):
    """Send/receive a snapshot to a another disk on the same machine.

    Keyword arguments:
    snapshot -- the Snapshot instance to transfer
    remote_profile -- the RemoteProfile entry to process
    parent -- provide parent Snapshot for incremental updates (optional)
    """

    snap_dir = path.join(remote_profile.path, snapshot.id)

    subprocess.run(["btrfs", "subvolume", "create", remote_profile.path])
    mkdir(snap_dir)

    for dir in snapshot.dirs:
        send_args = ["btrfs", "send", path.join(snapshot.path, path.basename(dir))]

        if parent is not None and dir in parent.dirs:
            send_args.insert(len(send_args)-1, "-p")
            send_args.insert(len(send_args)-1, path.join(parent.path, path.basename(dir)))

        # https://stackoverflow.com/questions/7353054/running-a-command-line-containing-pipes-and-displaying-result-to-stdout
        send = subprocess.Popen(send_args, stdout=subprocess.PIPE)
        recv = subprocess.Popen(["btrfs", "receive", snap_dir], stdin=send.stdout, stdout=subprocess.PIPE)

        send.stdout.close()
        output, err = recv.communicate()

    # Do this last to mark that the snapshot succeeded.
    copyfile(path.join(snapshot.path, "snapshot.ini"), path.join(snap_dir, "snapshot.ini"))
    remote_profile.last_sent = snapshot.id

def send_snapshot_ssh(snapshot, remote_profile, parent=None):
    """Send/receive a snapshot to a another machine over SSH. Root access is required.

    Keyword arguments:
    snapshot -- the Snapshot instance to transfer
    remote_profile -- the RemoteProfile entry to process
    parent -- provide parent Snapshot for incremental updates (optional)
    """

    login = "root@%s" % remote_profile.host
    snap_dir = path.join(remote_profile.path, snapshot.id)

    # NOTE: Run these separately so that "sub create" can fail without affecting the latter command.
    subprocess.run(["ssh", login, "btrfs subvolume create %s" % remote_profile.path])
    subprocess.run(["ssh", login, "mkdir %s" % snap_dir])

    for dir in snapshot.dirs:
        send_args = ["btrfs", "send", path.join(snapshot.path, path.basename(dir))]

        if parent is not None and dir in parent.dirs:
            send_args.insert(len(send_args)-1, "-p")
            send_args.insert(len(send_args)-1, path.join(parent.path, path.basename(dir)))

        send = subprocess.Popen(send_args, stdout=subprocess.PIPE)
        recv = subprocess.Popen(["ssh", login, "btrfs receive %s" % snap_dir], stdin=send.stdout, stdout=subprocess.PIPE)

        send.stdout.close()
        output, err = recv.communicate()

    # Do this last to mark that the snapshot succeeded.
    subprocess.run(["scp", path.join(snapshot.path, "snapshot.ini"), "%s:%s" % (login, snap_dir)])
    remote_profile.last_sent = snapshot.id
