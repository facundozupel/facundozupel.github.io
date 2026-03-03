#!/usr/bin/env python3
"""
Google Indexing API - Submit URLs for indexing/deindexing.

Usage:
    python scripts/google-indexing/index.py --action index --urls https://cascadaschile.com/page1
    python scripts/google-indexing/index.py --action deindex --urls https://cascadaschile.com/old-page
    python scripts/google-indexing/index.py --action index --file urls.txt
    python scripts/google-indexing/index.py --action index --urls https://cascadaschile.com/page1 --key /path/to/key.json
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from google.oauth2 import service_account
import google_auth_httplib2
import httplib2

ENDPOINT = "https://indexing.googleapis.com/v3/urlNotifications:publish"
SCOPES = ["https://www.googleapis.com/auth/indexing"]

ACTION_MAP = {
    "index": "URL_UPDATED",
    "deindex": "URL_DELETED",
}


def authenticate(key_path):
    credentials = service_account.Credentials.from_service_account_file(key_path, scopes=SCOPES)
    http = google_auth_httplib2.AuthorizedHttp(credentials, http=httplib2.Http())
    return http


def submit_url(http, url, action_type):
    body = json.dumps({"url": url, "type": action_type})
    response, content = http.request(
        ENDPOINT,
        method="POST",
        body=body,
        headers={"Content-Type": "application/json"},
    )
    status = int(response["status"])
    result = json.loads(content.decode("utf-8"))
    return status, result


def load_urls_from_file(file_path):
    path = Path(file_path)
    if not path.exists():
        print(f"Error: file '{file_path}' not found.")
        sys.exit(1)
    urls = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line)
    return urls


def main():
    parser = argparse.ArgumentParser(
        description="Submit URLs to Google Indexing API for indexing or removal."
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=["index", "deindex"],
        help="Action to perform: 'index' (URL_UPDATED) or 'deindex' (URL_DELETED)",
    )
    parser.add_argument(
        "--urls",
        nargs="+",
        help="One or more URLs to submit",
    )
    parser.add_argument(
        "--file",
        help="Path to a .txt file with one URL per line",
    )
    parser.add_argument(
        "--key",
        default=str(Path(__file__).parent / "facundogrowth.json"),
        help="Path to the service account JSON key (default: scripts/google-indexing/service_account.json)",
    )
    args = parser.parse_args()

    if not args.urls and not args.file:
        parser.error("You must provide --urls or --file.")

    # Collect URLs
    urls = list(args.urls) if args.urls else []
    if args.file:
        urls.extend(load_urls_from_file(args.file))

    if not urls:
        print("Error: no URLs to process.")
        sys.exit(1)

    # Validate URLs
    for url in urls:
        if not url.startswith(("http://", "https://")):
            print(f"Error: invalid URL '{url}'. Must start with http:// or https://")
            sys.exit(1)

    # Authenticate
    key_path = Path(args.key)
    if not key_path.exists():
        print(f"Error: service account key not found at '{key_path}'.")
        print("Download your JSON key from Google Cloud Console and place it there.")
        print("Docs: https://developers.google.com/search/apis/indexing-api/v3/prereqs")
        sys.exit(1)

    try:
        http = authenticate(str(key_path))
    except Exception as e:
        print(f"Error: authentication failed - {e}")
        sys.exit(1)

    action_type = ACTION_MAP[args.action]
    action_label = "Indexing" if args.action == "index" else "Deindexing"
    success = 0
    failed = 0

    print(f"\n{action_label} {len(urls)} URL(s)...\n")

    for url in urls:
        try:
            status, result = submit_url(http, url, action_type)
            timestamp = datetime.now().strftime("%H:%M:%S")

            if status == 200:
                notify_time = result.get("urlNotificationMetadata", {}).get(
                    "latestUpdate", {}
                ).get("notifyTime", "N/A")
                print(f"  [{timestamp}] OK  {url} (notifyTime: {notify_time})")
                success += 1
            elif status == 429:
                print(f"  [{timestamp}] RATE LIMITED  {url} - try again later")
                failed += 1
            else:
                error_msg = result.get("error", {}).get("message", "Unknown error")
                print(f"  [{timestamp}] FAIL ({status})  {url} - {error_msg}")
                failed += 1

        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"  [{timestamp}] ERROR  {url} - {e}")
            failed += 1

    print(f"\nDone: {success} ok, {failed} failed, {len(urls)} total.")
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
