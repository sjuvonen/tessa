TESSA
=====

Experimental tool for snapshotting, made fit for my personal needs.

## Requirements
- Python 3
- Use btrfs on relevant partitions

## Installation
No installer yet.

## Commands
Commands have to be executed as root.

### Setup a profile for snapshots
tessa new --name <profile> --dest <snapshot root> path1 path2...

### List existing profiles
tessa list

### Take a snapshot (executes btrfs sub snap)
tessa snap <profile>
