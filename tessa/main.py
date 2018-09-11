from configparser import ConfigParser
from datetime import datetime
from os import mkdir, path
from subprocess import run

class Profile:
    def __init__(self, name, dirs=[], destination=None):
        # Human-readable name of this profile.
        self.name = name

        # List of btrfs subvolumes to snapshot.
        self.dirs = dirs

        # Root directory for a "snapshot environment".
        self.destination = destination

        # Name of the latest snapshot.
        self.last_snapshot = None

        # List of RemoteProfile instances.
        self.remotes = None

class RemoteProfile:
    TYPE_LOCAL = "local"
    TYPE_SSH = "ssh"

    def __init__(self, path=None, type=None, host=None):
        # Root directory for snaps on the RECEIVE end.
        self.path = path

        # Type of remote target.
        self.type = self.TYPE_LOCAL if type is None else type

        # Host name / domain for SSH.
        self.host = host

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

def read_profile_meta(base_dir):
    config = ConfigParser()
    config.read("%s/profile.ini" % base_dir)

    try:
        data = dict(config["SETTINGS"])
        data["dirs"] = tuple(config["DIRS"].values())

        profile = Profile(**data)

        if "REMOTES" in config:
            remotes = []
            for path, value in config["REMOTES"].items():
                _, i, key = path.split("\\")

                if len(remotes) <= int(i):
                    remotes.append({})

                remotes[-1][key] = value

            profile.remotes = tuple(RemoteProfile(**data) for data in remotes)


        if "SNAPSHOT" in config:
            profile.last_snapshot = config["SNAPSHOT"]["last_snapshot"]

        return profile
    except KeyError:
        raise ValueError("Could not read profile from %s/profile.ini" % base_dir)

def write_profile_meta(profile):
    config = ConfigParser()
    config["SETTINGS"] = {}
    config["SETTINGS"]["name"] = profile.name
    config["SETTINGS"]["destination"] = profile.destination
    config["DIRS"] = dict(("dir\\%d" % i, dir) for i, dir in enumerate(profile.dirs))

    if profile.remotes is not None:
        config["REMOTES"] = {}
        for i in range(0, len(profile.remotes)):
            remote = profile.remotes[i]
            prefix = "remote\\%d\\" % i
            config["REMOTES"][prefix + "type"] = remote.type
            config["REMOTES"][prefix + "path"] = remote.path

            if remote.type == RemoteProfile.TYPE_SSH:
                config["REMOTES"][prefix + "host"] = remote.host

    if profile.last_snapshot is not None:
        config["SNAPSHOT"] = {}
        config["SNAPSHOT"]["last_snapshot"] = profile.last_snapshot

    with open("%s/profile.ini" % profile.destination, "w") as file:
        config.write(file)

def read_snapshot_meta(profile, snap_id):
    config = ConfigParser()
    config.read("%s/%s/snapshot.ini" % (profile.destination, snap_id))

    try:
        data = dict(config["SETTINGS"])
        data["dirs"] = tuple(config["DIRS"].values())
        return Snapshot(**data)
    except KeyError:
        raise ValueError("Could not read snapshot from %s/%s/snapshot.ini" % (profile.destination, snap_id))

def write_snapshot_meta(snapshot):
    config = ConfigParser()
    config["SETTINGS"] = {}
    config["SETTINGS"]["path"] = snapshot.path
    config["SETTINGS"]["time"] = snapshot.time
    config["DIRS"] = dict(("dir\\%d" % i, dir) for i, dir in enumerate(snapshot.dirs))

    with open("%s/snapshot.ini" % snapshot.path, "w") as file:
        config.write(file)

def init_profile(profile):
    run(["btrfs", "subvolume", "create", profile.destination])
    write_profile_meta(profile)

def create_snapshot(profile):
    snap_time = datetime.now()
    snap_id = snap_time.strftime("%Y%m%d-%H%M%S")
    snap_dir = path.join(profile.destination, snap_id)
    log_time = snap_time.isoformat().split(".")[0]

    # Safe to make read-only as root can still write anyways.
    mkdir(snap_dir, 0o550)

    for src in profile.dirs:
        dst = path.join(snap_dir, path.basename(src))
        run(["btrfs", "subvolume", "snapshot", "-r", src, dst])

    snapshot = Snapshot(snap_dir, log_time, tuple(profile.dirs))
    profile.last_snapshot = snap_id

    write_snapshot_meta(snapshot)
    write_profile_meta(profile)

    return snapshot
