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
```sh
tessa new --name <profile> --dest <destination> dir
```

### List existing profiles
```sh
tessa list
```

### Take a snapshot (executes btrfs sub snap)
```sh
tessa snap <profile>
```

### Setting up remote backup
Currently there is no interface for configuring send/receive targets.
