#!/usr/bin/python3

import argparse
import sys

from tessa import core, main

class Command:
    def run(self):
        pass

class ProfileWizardCommand(Command):
    def __init__(self):
        self.cmdparser = argparse.ArgumentParser(description="Setup a new profile")

        self.cmdparser.add_argument("--name", metavar="name", type=str, required=True, help="Informative name for the profile")
        self.cmdparser.add_argument("--dest", metavar="destination", type=str, required=True, help="Destination for snapshots")
        self.cmdparser.add_argument("paths", metavar="dir", type=str, nargs="+", help="Subvolume(s) (directories) to make snapshots of")

    def run(self, argv):
        parsed = self.cmdparser.parse_args(argv)
        main.create_profile(parsed.name, parsed.paths, parsed.dest)

class ListProfilesCommand(Command):
    def __init__(self):
        self.cmdparser = argparse.ArgumentParser(description="List existing profiles")

    def run(self, argv):
        parsed = self.cmdparser.parse_args(argv)
        print(main.list_profiles())

class CreateSnapshotCommand(Command):
    def __init__(self):
        profiles = main.list_profiles()
        self.cmdparser = argparse.ArgumentParser(description="Create a new snapshot")
        self.cmdparser.add_argument("profile", help="Name of the profile to execute", choices=profiles)

    def run(self, argv):
        parsed = self.cmdparser.parse_args(argv)
        profile = main.read_profile(parsed.profile)
        snapshot = core.create_snapshot(profile)

        print(f"Snapshot {profile.name} completed")

        for remote in profile.remotes:
            if remote.last_sent:
                parent = core.read_snapshot_meta(profile, remote.last_sent)
                print(f"Send snapshot diff since {remote.last_sent} to remote {remote.path}")
                core.send_snapshot(snapshot, remote, parent=parent)
            else:
                print(f"Send base snapshot to remote {remote.path}")
                core.send_snapshot(snapshot, remote)

class Catalog:
    def __init__(self):
        self.commands = dict()

    def list(self):
        return self.commands.keys()

    def add(self, name, command):
        self.commands[name] = command

    def get(self, name):
        return self.commands[name]

    def run(self, name, argv):
        self.get(name).run(argv)


commands = Catalog()
commands.add("new", ProfileWizardCommand())
commands.add("list", ListProfilesCommand())
commands.add("snap", CreateSnapshotCommand())

cmdparser = argparse.ArgumentParser(description="Tessa (for incremental btrfs snapshots)")

cmdparser.add_argument("command", type=str, choices=commands.list())

parsed, others = cmdparser.parse_known_args()

commands.run(parsed.command, others)
