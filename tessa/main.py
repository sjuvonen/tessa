from os import listdir, path
from .core import create_snapshot, read_snapshot_meta, PROFILES_DIR
from .remote import send_snapshot


def read_profile(name):
    from .core import read_profile_meta
    return read_profile_meta(path.join(PROFILES_DIR, name))


def _write_profile(profile):
    from .core import write_profile_meta
    write_profile_meta(profile, path.join(PROFILES_DIR, profile.name))


def create_profile(name, directory, destination):
    from .core import Profile
    profile = Profile(name, directory, destination)
    _write_profile(profile)


def add_remote(pname, type, path, host=None):
    from .core import RemoteProfile
    profile = read_profile(pname)
    remote = RemoteProfile(type, path, host)
    profile.remotes.append(remote)
    _write_profile(profile)


def list_profiles():
    return tuple(listdir(PROFILES_DIR))


def execute_profiles():
    for name in list_profiles():
        profile = read_profile(name)
        snapshot = create_snapshot(profile)

        for remote_profile in profile.remotes:
            parent = read_snapshot_meta(profile, remote_profile.last_sent) if remote_profile.last_sent else None
            send_snapshot(snapshot, remote_profile, parent)
