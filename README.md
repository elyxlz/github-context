# GitHub Context Extractor

A simple CLI tool to extract context from GitHub repositories (code, issues, wiki ...) for AI.

## Install

```bash
pip install github-context
```

## Usage

```bash
ghc owner/repo [options]
```

Options:
- `--issues-only`: Extract only issues
- `--wiki-only`: Extract only wiki
- `--no-issues`: Exclude issues
- `--no-wiki`: Exclude wiki
- `--output DIR`: Specify output directory

## Requirements

- Python 3.6+
- GitHub Personal Access Token (set as `GITHUB_TOKEN` environment variable)

## License

MIT
