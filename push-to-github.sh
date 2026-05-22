
#!/bin/bash
cd ~
git add -A
git commit -m "Update: $(date '+%Y-%m-%d %H:%M')"
git push
