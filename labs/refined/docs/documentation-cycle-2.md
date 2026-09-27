# Cycle 2

> From `documentation` PLATO room

I'll execute the first task: read 5 random fleet repos and score their documentation quality.

First, let me explore the fleet structure to find repos.

```bash
#!/bin/bash
# Find git repositories in the fleet
find . -type d -name ".git" 2>/dev/null | head -20
```

Let me run this and see what we have.

```bash
pwd
ls -la
find . -type d -name ".git" 2>/dev/null | head -10
```

I'll write the exploration results to a file and then examine 5 random repos.

```bash
# Create work directory if it doesn't exist
mkdir -p work

# List all git repos
find . -type d -name ".git" 2>/dev/null | sed 's/\/.git$//' > work/all_repos.txt

# Count them
repo_count=$(wc -l < work/all_repos.txt)
echo "Found $repo_count repositories"

# Select 5 random repos
if [ $repo_count -gt 0 ]; then
    shuf work/all_repos.txt | head -5 > work/selected_repos.txt
    echo "Selected 5 random repos:"
    cat work/selected_repos.txt
else
    echo "No repositories found. Checking current directory..."
    ls -la
fi
```

Now
