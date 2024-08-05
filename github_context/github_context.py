#!/usr/bin/env python3

import os
import sys
import argparse
import pyperclip
from github import Github
import base64
from typing import Optional, List
from github.Repository import Repository
from github.ContentFile import ContentFile
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


def add_content(header: str, content: str) -> str:
    return f"{'='*50}\n{header}\n{'='*50}\n\n{content}\n\n"


def should_ignore(path: str, ignore_patterns: List[str]) -> bool:
    return any(pattern in path for pattern in ignore_patterns) or path == ".gitignore"


def is_binary(content: bytes, sample_size: int = 1024) -> bool:
    if b"\x00" in content[:sample_size]:
        return True
    try:
        content[:sample_size].decode("utf-8")
        return False
    except UnicodeDecodeError:
        return True


def extract_file_content(
    repo: Repository, content_file: ContentFile, ignore_patterns: List[str]
) -> Optional[str]:
    if not should_ignore(content_file.path, ignore_patterns):
        try:
            file_content = base64.b64decode(content_file.content)
            if not is_binary(file_content):
                return add_content(
                    f"File: {content_file.path}", file_content.decode("utf-8")
                )
            else:
                print(f"Skipping binary file: {content_file.path}")
        except Exception as e:
            print(f"Error extracting {content_file.path}: {str(e)}")
    return None


def extract_repo_content(
    repo: Repository,
    path: str = "",
    ignore_patterns: List[str] = [],
    branch: str = "main",
) -> str:
    all_content = ""
    contents: List[ContentFile] = repo.get_contents(path, ref=branch)

    with ThreadPoolExecutor() as executor:
        future_to_content = {
            executor.submit(
                extract_file_content, repo, content_file, ignore_patterns
            ): content_file
            for content_file in contents
            if content_file.type != "dir"
        }

        for content_file in contents:
            if content_file.type == "dir":
                all_content += extract_repo_content(
                    repo, content_file.path, ignore_patterns, branch
                )

        for future in tqdm(
            as_completed(future_to_content),
            total=len(future_to_content),
            desc="Extracting files",
        ):
            content = future.result()
            if content:
                all_content += content

    return all_content


def extract_issues(repo: Repository) -> str:
    all_content = ""
    issues = list(repo.get_issues(state="all"))

    with ThreadPoolExecutor() as executor:
        future_to_issue = {
            executor.submit(extract_single_issue, issue): issue for issue in issues
        }

        for future in tqdm(
            as_completed(future_to_issue),
            total=len(future_to_issue),
            desc="Extracting issues",
        ):
            all_content += future.result()

    return all_content


def extract_single_issue(issue) -> str:
    content = f"Issue #{issue.number}: {issue.title}\n\n{issue.body}\n\nComments:\n"
    for comment in issue.get_comments():
        content += f"- {comment.user.login}: {comment.body}\n\n"
    return add_content(f"Issue: #{issue.number}", content)


def extract_wiki(repo: Repository) -> str:
    all_content = ""
    try:
        wiki = repo.get_wiki()
        pages = list(wiki.get_pages())

        with ThreadPoolExecutor() as executor:
            future_to_page = {
                executor.submit(extract_single_wiki_page, page): page for page in pages
            }

            for future in tqdm(
                as_completed(future_to_page),
                total=len(future_to_page),
                desc="Extracting wiki pages",
            ):
                all_content += future.result()
    except AttributeError:
        pass
    except Exception as e:
        print(f"Error extracting wiki: {str(e)}")
    return all_content


def extract_single_wiki_page(page) -> str:
    return add_content(f"Wiki Page: {page.title}", page.content)


def extract_readme(repo: Repository, branch: str) -> str:
    try:
        readme = repo.get_readme(ref=branch)
        content = base64.b64decode(readme.content).decode("utf-8")
        return add_content("README", content)
    except Exception as e:
        print(f"Error extracting README: {str(e)}")
        return ""


def extract_file_tree(
    repo: Repository, path: str = "", branch: str = "main", prefix: str = ""
) -> str:
    tree = ""
    contents = repo.get_contents(path, ref=branch)

    for content in contents:
        if content.type == "dir":
            tree += f"{prefix}├── {content.name}/\n"
            tree += extract_file_tree(repo, content.path, branch, prefix + "│   ")
        else:
            tree += f"{prefix}├── {content.name}\n"

    return tree


def get_default_branch(repo: Repository) -> str:
    try:
        return repo.default_branch
    except:
        return "main"  # Fallback to "main" if default_branch is not accessible


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract content from a GitHub repository."
    )
    parser.add_argument("repo", help="Repository name in the format 'owner/repo'")
    parser.add_argument(
        "--branch",
        help="Branch to extract content from (default: repository's default branch)",
    )
    parser.add_argument(
        "--issues-only", action="store_true", help="Extract only issues"
    )
    parser.add_argument("--wiki-only", action="store_true", help="Extract only wiki")
    parser.add_argument("--code-only", action="store_true", help="Extract only code")
    parser.add_argument(
        "--readme-only", action="store_true", help="Extract only README"
    )
    parser.add_argument(
        "--no-issues", action="store_true", help="Do not extract issues"
    )
    parser.add_argument("--no-wiki", action="store_true", help="Do not extract wiki")
    parser.add_argument("--output", help="Output directory for the text file")
    args = parser.parse_args()

    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print("Please set the GITHUB_TOKEN environment variable")
        sys.exit(1)

    g = Github(github_token)
    repo = g.get_repo(args.repo)

    default_branch = get_default_branch(repo)
    branch = args.branch if args.branch else default_branch

    all_content = f"Content of {args.repo} (branch: {branch})\n\n"

    try:
        ignore_patterns: List[str] = []
        try:
            gitignore_content = repo.get_contents(
                ".gitignore", ref=branch
            ).decoded_content.decode("utf-8")
            ignore_patterns = [
                line.strip()
                for line in gitignore_content.split("\n")
                if line.strip() and not line.startswith("#")
            ]
        except Exception:
            pass

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []

            if args.readme_only:
                futures.append(executor.submit(extract_readme, repo, branch))
            else:
                if args.code_only or (not args.issues_only and not args.wiki_only):
                    futures.append(
                        executor.submit(
                            extract_repo_content, repo, "", ignore_patterns, branch
                        )
                    )

                if not args.no_issues and not args.wiki_only and not args.code_only:
                    futures.append(executor.submit(extract_issues, repo))

                if not args.no_wiki and not args.issues_only and not args.code_only:
                    futures.append(executor.submit(extract_wiki, repo))

            for future in tqdm(
                as_completed(futures),
                total=len(futures),
                desc="Extracting repository data",
            ):
                try:
                    result = future.result()
                    all_content += result
                except Exception as e:
                    print(f"Error during extraction: {str(e)}")

        if args.code_only or (
            not args.issues_only and not args.wiki_only and not args.readme_only
        ):
            file_tree = extract_file_tree(repo, branch=branch)
            all_content += add_content("File Structure", file_tree)

        if args.output:
            output_filename = os.path.join(
                args.output, f"{args.repo.replace('/', '_')}_{branch}_content.txt"
            )
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(all_content)
            print(f"Repository content extracted to '{output_filename}'")
        else:
            pyperclip.copy(all_content)
            print("Repository content copied to clipboard")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
