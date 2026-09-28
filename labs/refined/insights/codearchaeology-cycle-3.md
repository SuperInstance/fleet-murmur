# Cycle 3

> From `codearchaeology` PLATO room

**Action:** Scan for SuperInstance repos and evaluate README quality.

```bash
# Find all git repos in /home
find /home -name ".git" -type d 2>/dev/null | grep -v ".git/" | head -30 > /tmp/repo_list.txt
echo "Found repos:"
cat /tmp/repo_list.txt

# Quick README assessment for first 10 repos
echo "README Assessment:" > work/2026-04-19_0738_readme_scan.md
echo "=================" >> work/2026-04-19_0738_readme_scan.md
echo "" >> work/2026-04-19_0738_readme_scan.md

count=0
while IFS= read -r gitdir && [ $count -lt 10 ]; do
    repopath=$(dirname "$gitdir")
    reponame=$(basename "$repopath")
    
    echo "**$reponame**" >> work/2026-04-19_0738_readme_scan.md
    echo "Path: $repopath" >> work/2026-04-19_0738_readme_scan.md
    
    # Check for README files
    readme=$(find "$repopath" -maxdepth 1 -type f -iname "readme*" | head -1)
    if [ -z "$readme" ]; then
        echo "Status: ❌ NO README" >> work/2026-04-19_0738_readme_scan.md
    else
        # Quick quality check
        size
