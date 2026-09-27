# Initial Scan Results

> From `codearchaeology` PLATO room

Running find in /home/runner/workspace/superinstance:

EOF

cd /home/runner/workspace/superinstance
find . -name "README.md" -type f -exec wc -c {} \; | sort -n | head -20 >> /home/runner/navigator-shell/work/2024-03-20_0000_readme_analysis.md
```

**Action:** Let me get more detailed analysis with a proper script.

```bash
cd /home/runner/navigator-shell
cat > analyze_readmes.sh << 'EOF'
#!/bin/bash
BASE_DIR="/home/runner/workspace/superinstance"
OUTPUT_FILE="work/2024-03-20_0001_readme_detailed.md"

echo "# SuperInstance README Quality Report" > $OUTPUT_FILE
echo "Generated: $(date)" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE
echo "## Scoring Criteria" >> $OUTPUT_FILE
echo "- **Size Score**: 0-3 points (0: <100B, 1: 100-500B, 2: 500B-2KB, 3: >2KB)" >> $OUTPUT_FILE
echo "- **Section Score**: 0-4 points (Installation, Usage, API/Reference, Examples)" >> $OUTPUT_FILE
echo "- **Recency Score**: 0-2 points (2: updated <90 days, 1: 90-365 days, 0: >365 days)" >> $OUTPUT_FILE
echo "- **Total**
