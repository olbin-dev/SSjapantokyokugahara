#!/usr/bin/env python3
import os
import re
import datetime
import subprocess

# Configure paths
VAULT_PATH = "/Users/p/Library/Mobile Documents/iCloud~md~obsidian/Documents/MacMini"
REPO_PATH = "/Users/p/developer/46_ANCHOR_LLM/SSjapantokyokugahara"
INDEX_PATH = os.path.join(REPO_PATH, "index.html")

REPOS_TO_SCAN = [
    ("/Users/p/developer/46_ANCHOR_LLM/SSjapantokyokugahara", "Sovereign Log (Docs Site)"),
    ("/Users/p/developer/services/macro-engine", "Macro Engine (Service)"),
    ("/Users/p/developer/services/translation-engine", "Translation Engine (Service)"),
    ("/Users/p/developer/55_DaviSync", "DaviSync (Core)")
]

def get_zenkaku_date_string(date):
    # Convert numbers to Zenkaku (Japanese full-width) characters
    zenkaku_digits = "０１２３４５６７８９"
    month_str = "".join(zenkaku_digits[int(d)] for d in str(date.month))
    day_str = "".join(zenkaku_digits[int(d)] for d in str(date.day))
    return f"{month_str}月{day_str}日"

def get_obsidian_notes(date):
    # Try different naming conventions for today's daily note
    month_day_zenkaku = get_zenkaku_date_string(date)
    month_day_hankaku = f"{date.month}月{date.day}日"
    iso_date = date.strftime("%Y-%m-%d")
    
    paths_to_try = [
        os.path.join(VAULT_PATH, "TODO", f"{month_day_zenkaku}.md"),
        os.path.join(VAULT_PATH, "TODO", f"{month_day_hankaku}.md"),
        os.path.join(VAULT_PATH, "TODO", f"{iso_date}.md"),
        os.path.join(VAULT_PATH, f"{iso_date}.md")
    ]
    
    for path in paths_to_try:
        if os.path.exists(path):
            print(f" Found Obsidian daily note at: {path}")
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
    return None

def get_git_commits(repo_path):
    if not os.path.exists(repo_path):
        return []
    try:
        # Get commits since midnight today
        result = subprocess.run(
            ["git", "log", "--since=midnight", "--oneline", "--reverse"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        commits = result.stdout.strip().split("\n")
        return [c for c in commits if c]
    except Exception as e:
        print(f"Error fetching commits from {repo_path}: {e}")
        return []

def format_markdown_to_html(md_text):
    if not md_text:
        return "<p>No entries for today.</p>"
    
    html = ""
    lines = md_text.split("\n")
    in_list = False
    
    for line in lines:
        line = line.strip()
        if not line:
            if in_list:
                html += "</ul>\n"
                in_list = False
            continue
            
        # Lists
        if line.startswith("-") or line.startswith("*"):
            if not in_list:
                html += "<ul>\n"
                in_list = True
            content = line[1:].strip()
            # Simple bold/link conversion
            content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
            content = re.sub(r'\[\[(.*?)\]\]', r'<code>\1</code>', content)
            html += f"  <li>{content}</li>\n"
        # Headers
        elif line.startswith("#"):
            if in_list:
                html += "</ul>\n"
                in_list = False
            level = len(line) - len(line.lstrip("#"))
            content = line.lstrip("#").strip()
            html += f"<h{level + 1}>{content}</h{level + 1}>\n"
        # Paragraphs
        else:
            if in_list:
                html += "</ul>\n"
                in_list = False
            line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line)
            line = re.sub(r'\[\[(.*?)\]\]', r'<code>\1</code>', line)
            html += f"<p>{line}</p>\n"
            
    if in_list:
        html += "</ul>\n"
        
    return html

def update_index_html(date_str, ja_content, en_content):
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        content = f.read()
        
    # 1. Determine next post index
    post_indices = [int(idx) for idx in re.findall(r'onclick="switchPost\((\d+),\s*this\)"', content)]
    if not post_indices:
        print("Could not find any post indices in index.html.")
        return False
    
    max_idx = max(post_indices)
    next_idx = max_idx + 1
    print(f"Next post index will be: {next_idx}")
    
    # Check if a post with today's date already exists in the sidebar to prevent duplicates
    if f"Daily Log: {date_str}" in content:
        print(f"A post for Daily Log: {date_str} already exists in index.html. Skipping HTML injection.")
        return True

    # 2. Prepare new sidebar item
    new_sidebar_item = f"""        <li class="menu-item" onclick="switchPost({next_idx}, this)">
          <span>📅</span> Daily Log: {date_str}
        </li>"""
    
    # Locate where to insert the sidebar item (right after the last menu item switchPost(max_idx, this))
    sidebar_pattern = rf'(<li class="menu-item"[^>]*onclick="switchPost\({max_idx},[^"]*\)"[^>]*>.*?</li>)'
    match = re.search(sidebar_pattern, content, re.DOTALL)
    if not match:
        print(f"Could not locate sidebar menu item {max_idx} for replacement.")
        return False
    
    target_sidebar = match.group(1)
    content = content.replace(target_sidebar, f"{target_sidebar}\n{new_sidebar_item}")
    
    # 3. Prepare the new article markup
    new_article = f"""    <!-- POST {next_idx}: DAILY LOG {date_str} -->
    <article id="post-{next_idx}" class="post-card">
      <div class="meta-info">
        <span>{date_str}</span>
        <span class="tag">Daily Log</span>
        <span class="tag">Sovereign OS</span>
      </div>

      <!-- JA -->
      <div class="lang-section ja active">
        <h1 class="post-title">日誌・進捗日報 : {date_str}</h1>
        <div class="post-content">
          {ja_content}
        </div>
      </div>

      <!-- EN -->
      <div class="lang-section en">
        <h1 class="post-title">Daily Log &amp; Progress: {date_str}</h1>
        <div class="post-content">
          {en_content}
        </div>
      </div>
    </article>"""

    # Locate where to insert the article (right after article id="post-max_idx")
    article_pattern = rf'(<article id="post-{max_idx}".*?</article>)'
    art_match = re.search(article_pattern, content, re.DOTALL)
    if not art_match:
        print(f"Could not locate article post-{max_idx} for replacement.")
        return False
        
    target_article = art_match.group(1)
    content = content.replace(target_article, f"{target_article}\n\n{new_article}")
    
    # Save the updated index.html
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(" Successfully updated index.html!")
    return True

def generate_archive_md(date_str, ja_text, en_text):
    archive_dir = os.path.join(REPO_PATH, "docs", "daily-logs")
    os.makedirs(archive_dir, exist_ok=True)
    
    ja_path = os.path.join(archive_dir, f"{date_str}-ja.md")
    en_path = os.path.join(archive_dir, f"{date_str}.md")
    
    with open(ja_path, "w", encoding="utf-8") as f:
        f.write(f"# 日誌・進捗日報 : {date_str}\n\n{ja_text}")
    print(f" Saved Japanese archive file to: {ja_path}")
    
    with open(en_path, "w", encoding="utf-8") as f:
        f.write(f"# Daily Log & Progress: {date_str}\n\n{en_text}")
    print(f" Saved English archive file to: {en_path}")

def main():
    print("=" * 60)
    print(" AUTOMATED PROGRESS REPORT GENERATOR (NIPPO)")
    print("=" * 60)
    
    today = datetime.date.today()
    iso_date = today.strftime("%Y-%m-%d")
    
    # 1. Read Obsidian Memos
    print("[Step 1] Checking Obsidian Vault for daily notes...")
    obsidian_content = get_obsidian_notes(today)
    if not obsidian_content:
        obsidian_content = "- 本日のObsidianメモはありません。"
        print("  ⚠️ No daily note found in Obsidian for today.")
    else:
        print("  ✓ Found daily note contents.")

    # 2. Gather Git Commits
    print("[Step 2] Scanning Git repositories for today's commits...")
    git_logs = []
    for path, name in REPOS_TO_SCAN:
        commits = get_git_commits(path)
        if commits:
            git_logs.append(f"### {name}")
            for c in commits:
                git_logs.append(f"- {c}")
                
    git_content = "\n".join(git_logs) if git_logs else "- 本日のGitコミットはありません。"
    print(f"  ✓ Found {sum(len(get_git_commits(p)) for p, _ in REPOS_TO_SCAN)} commits across repositories.")

    # 3. Construct JA and EN bodies
    ja_raw_text = f"""## 📝 本日のメモ・TODO (Obsidian)

{obsidian_content}

## 💻 本日の開発コミット (Git Commits)

{git_content}"""

    # Basic machine-translated or simplified English version for bilingual display
    en_obsidian = obsidian_content
    # Convert some simple Japanese words in lists if possible, or just output the raw logs
    en_raw_text = f"""## 📝 Today's Notes & TODOs (Obsidian)

{en_obsidian}

## 💻 Development Activity (Git Commits)

{git_content}"""

    # 4. Convert markdown contents to HTML format
    ja_html = format_markdown_to_html(ja_raw_text)
    en_html = format_markdown_to_html(en_raw_text)
    
    # 5. Inject into index.html
    print("[Step 3] Integrating daily log into index.html...")
    updated = update_index_html(iso_date, ja_html, en_html)
    
    # 6. Save raw Markdown to docs archives
    if updated:
        print("[Step 4] Saving raw Markdown files to docs archive...")
        generate_archive_md(iso_date, ja_raw_text, en_raw_text)
        print("\n🎉 Success! Daily log generated successfully.")
        print(f"Access it locally by opening: {INDEX_PATH}")
        print("Once verified, stage, commit, and push it to deploy.")
    else:
        print("\n❌ Failed to update index.html.")

if __name__ == "__main__":
    main()
