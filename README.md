# gitanalyze

A learning project: build a GitHub contribution chart in Go, Python, and C.

Scans directories for Git repos, reads commit history, and prints a colored contribution grid (26 weeks × 7 days, ANSI terminal).

## Pipeline

```
CLI args (dir, email)
    │
    ▼
 scan directory for .git repos
    │
    ▼
 save repo list to ~/.gogitlocalstats
    │
    ▼
 for each repo: git log → count commits per day (past 6 months)
    │
    ▼
 print GitHub-style ANSI grid
```

## Project layout

```
gitanalyze/
├── go/
│   ├── scan.go         # directory scan, file I/O, main
│   ├── stats.go        # git log parsing, grid display
│   ├── go.mod
│   └── go.sum
├── python/
│   └── gitstats.py     # single file, subprocess + git log
└── c/
    └── gitstats.c      # single file, popen + POSIX APIs
```

## Features

- Recursive directory scan (skips `vendor`, `node_modules`)
- Persistent repo list with deduplication
- Email-filtered commit counting
- 6-month contribution grid with ANSI color coding
- Three languages, same pipeline — compare patterns
