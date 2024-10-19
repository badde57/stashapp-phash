# PHash Plugin for Stashapp

This plugin uses the Python `OpenCV` and `Perception` libraries to calculate
perceptual hashes for every frame of every video file (!) in your stashapp.

## Purpose

The purpose of this is to allow more fine-grained matching at the frame level
between (a hash of) a single frame of a single video to another set of (hashes
of) frames. The set to be matched against could be your local stashapp phash
database, or a public repository of frame hashes (in planning phase).

Possible use cases:

- Deduplication of databases more robustly than the built in .vtt based method.
- Partial matching, such as finding remixes / highlight reels.
- Matching a clip from a compilation to its original video.
- Finding derivative videos (compilations, PMVs) produced from an original
  video.

## How to configure the plugin

0. Install requirements: `pip install -r requirements.txt`. Briefly, it's opencv, stashapp-tools, perception, and their respective dependencies. This requires **python 3.11**.

1. Create a database for storing perceptual hashes:
  ```
  echo "
    CREATE TABLE phash(
      endpoint TEXT NOT NULL,
      stash_id TEXT NOT NULL,
      time_offset float not null, 
      time_duration float not null, 
      phash CHAR(12) NOT NULL, 
      method TEXT NOT NULL, 
      unique (stash_id, time_offset, method)
    );
  " | sqlite3 /path/to/phash.sqlite

2. Update `phash.yml` to use the path to the sqlite datbase you created. In the config, it's by default:
  `  - "{pluginDir}/../phash.sqlite"`
  Change accordingly.

## How to use the plugin

In stashapp settings > tasks, under plugin tasks, find a new task labeled
`PHash scenes`. This will trigger a database-wide hashing operation. It may
take many days to complete. Don't worry about interrupting it, it only commits
hashes to its database after processing a file, so interruption won't be a
problem - you can resume quickly anytime and without losing progress.
