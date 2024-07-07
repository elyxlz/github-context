# GitHub Context Extractor

A simple CLI tool to extract context from GitHub repositories (code, issues, wiki ...) for AI. Now with parallel processing and progress bars!

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
- `--code-only`: Extract only code
- `--no-issues`: Exclude issues
- `--no-wiki`: Exclude wiki
- `--output DIR`: Specify output directory

## Features

- Parallel processing for faster extraction
- Progress bars to track extraction progress
- Option to extract only code
- Improved performance for large repositories

## Requirements

- Python 3.6+
- GitHub Personal Access Token (set as `GITHUB_TOKEN` environment variable)

## License

MIT
