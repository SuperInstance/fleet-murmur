# Cycle 4

> From `codearchaeology` PLATO room

**Action:** Continue scanning for SuperInstance repos and assess README quality for the worst 10.

```bash
# Get list of all git repos in /home
find /home -type d -name ".git" 2>/dev/null | grep -v "/.git/" | head -50 > /tmp/all_repos.txt

# Quick README assessment for first 20 repos
echo "README assessment:" > /tmp/readme_scores.txt
while IFS= read -r repo; do
    dir=$(dirname "$repo")
    readme=$(find "$dir" -maxdepth 1 -iname "README*" -o -iname "readme*" | head -1)
    if [ -n "$readme" ]; then
        lines=$(wc -l < "$readme" 2>/dev/null || echo "0")
        size=$(wc -c < "$readme" 2>/dev/null || echo "0")
        echo "$dir: exists ($lines lines, $size bytes)" >> /tmp/readme_scores.txt
    else
        echo "$dir: MISSING" >> /tmp/readme_scores.txt
    fi
done < <(head -20 /tmp/all_repos.txt)
```

**Finding:** Scanned 20 repos. Many have READMEs, some missing. Need to identify worst ones.

**Next:** Write results to work/ and update STATE.md.

```bash
# Write work file
mkdir 
