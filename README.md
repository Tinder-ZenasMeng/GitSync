# Git Sync

## Overview
A script that syncs over files and directories to specified repositories. 

This currently has hardcoded support for mkdocs.

## Usage
1. Define an `external.json` where the main script is located.
2. Populate `external.json` with git repositories that you'd like to sync. The script will look look at these directories in search of an `external-sync.json` for syncing.
3. Define an `external-sync.json` in the external repo you've defined that you'd like to sync.
4. Populate `external-sync.json` with files or directories that you'd like to sync, along with the yaml path where you'd like mkdocs to point to.
5. Run the script with `python3 gitSync.py`.

## Development

### Dependencies
Dependencies can be installed via `pip install -r requirements.txt`.

### Environment variables
This repo uses `python-dotenv` to retrieve environment variables.
The most notable environment variable that must be supplied by the user is the `GH_TOKEN`, which will provide Github access.

## Known Issues
* Speed
    * There are many locations where speed can be optimized, either through parallel processing or caching.
* Non-conventional yaml 1.2 spec notation support
    * Mkdocs sometimes has the `!!` notation, which does not properly read/write.
* Mkdocs support is currently hard coded and needs to be split out.