from configparser import ConfigParser
from datetime import datetime
from os import mkdir, path
from subprocess import run

class Profile:
    def __init__(self, name, dirs=[], dst=None):
        # Human-readable name of this profile.
        self.name = name

        # List of btrfs subvolumes to snapshot.
        self.dirs = dirs

        # Root directory for a "snapshot environment".
        self.destination = dst

        # Name of the latest snapshot
        self.last_snapshot = None

class RemoteProfile:
    TYPE_LOCAL = 1
    TYPE_SSH = 2

    def __init__(self, path, type=None):
        # Root directory for snaps on the RECEIVE end.
        self.path = path

        # Type of remote target.
        self.type = self.TYPE_LOCAL if type is None else type

        # Host name / domain for SSH.
        self.host = None

        # Name of last snapshot that was sent.
        self.last_sent = None

        # True := Sending snapshot was completed; False := Transfer was interrupted.
        self.was_completed = False

class Snapshot:
    def __init__(self, path, time, dirs):
        # Containing folder of the snapshot.
        self.path = path

        # Time and date when this snapshot was taken.
        self.time = time

        # List of btrfs subvolumes that this snapshot contains.
        # Store dirs per snapshot so that new directories can be added after initial snapshot.
        self.dirs = dirs

def write_profile_meta(profile):
    config = ConfigParser()
    config["DEFAULT"]["name"] = profile.name
    config["DEFAULT"]["destination"] = profile.destination

    for i, dir in enumerate(profile.dirs):
        config["DEFAULT"]["dirs\\{}".format(i)] = dir

    if profile.last_snapshot is not None:
        config["SNAPSHOT"] = {}
        config["SNAPSHOT"]["last_snapshot"] = profile.last_snapshot

    with open("{}/profile.ini".format(profile.destination), "w") as file:
        config.write(file)

def write_snapshot_meta(snapshot):
    config = ConfigParser()
    config["DEFAULT"]["path"] = snapshot.path
    config["DEFAULT"]["time"] = snapshot.time.strftime("%Y-%m-%dT%H:%M:%S")

    for i, dir in enumerate(snapshot.dirs):
        config["DEFAULT"]["dirs\\{}".format(i)] = dir

    with open("{}/snapshot.ini".format(snapshot.path), "w") as file:
        config.write(file)

def init_profile(profile):
    run(["btrfs", "subvolume", "create", profile.destination])
    write_profile_meta(profile)

def create_snapshot(profile):
    snap_time = datetime.now()
    snap_id = snap_time.strftime("%Y%m%d-%H%M%S")
    snap_dir = "{}/{}".format(profile.destination, snap_id)

    # Safe to make read-only as root can still write anyways.
    mkdir(snap_dir, 0o550)

    for src in profile.dirs:
        dst = "{}/{}".format(snap_dir, path.basename(src))
        run(["btrfs", "subvolume", "snapshot", "-r", src, dst])

    snapshot = Snapshot(snap_dir, snap_time, profile.dirs)
    profile.last_snapshot = snap_id
    write_snapshot_meta(snapshot)
    write_profile_meta(profile)

    return snapshot
