from os import path
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

    subprocess.run(["btrfs", "subvolume", "create", remote_profile.path])

    send_args = ["btrfs", "send", snapshot.path]

    if parent is not None:
        send_args.insert(len(send_args)-1, "-p")
        send_args.insert(len(send_args)-1, parent.path)

    # https://stackoverflow.com/questions/7353054/running-a-command-line-containing-pipes-and-displaying-result-to-stdout
    send = subprocess.Popen(send_args, stdout=subprocess.PIPE)
    recv = subprocess.Popen(["btrfs", "receive", remote_profile.path], stdin=send.stdout, stdout=subprocess.PIPE)

    send.stdout.close()
    output, err = recv.communicate()

    # Do this last to mark that the snapshot succeeded.
    remote_profile.last_sent = snapshot.id

##
# Thos method has not been tested since refactoring the code and changing storage
# logic!!!
def send_snapshot_ssh(snapshot, remote_profile, parent=None):
    """Send/receive a snapshot to a another machine over SSH. Root access is required.

    Keyword arguments:
    snapshot -- the Snapshot instance to transfer
    remote_profile -- the RemoteProfile entry to process
    parent -- provide parent Snapshot for incremental updates (optional)
    """

    login = "root@%s" % remote_profile.host

    # NOTE: Run these separately so that "sub create" can fail without affecting the latter command.
    subprocess.run(["ssh", login, "btrfs subvolume create %s" % remote_profile.path])

    send_args = ["btrfs", "send", snapshot.path]

    if parent is not None:
        send_args.insert(len(send_args)-1, "-p")
        send_args.insert(len(send_args)-1, parent.path)

    send = subprocess.Popen(send_args, stdout=subprocess.PIPE)
    recv = subprocess.Popen(["ssh", login, "btrfs receive %s" % remote_profile.path], stdin=send.stdout, stdout=subprocess.PIPE)

    send.stdout.close()
    output, err = recv.communicate()

    # Do this last to mark that the snapshot succeeded.
    remote_profile.last_sent = snapshot.id
