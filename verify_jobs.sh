#!/bin/bash

USER_AGENT='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'

# Role definitions: index|title|company|url|ATS_label
ROLES=(
  "1|Technical Program Manager, Compute|Anthropic|https://www.builtinsf.com/job/technical-program-manager-compute/8633009|anthropic"
  "2|Senior TPM, Product Engineering|Lambda|https://www.builtinsf.com/job/senior-technical-program-manager-product-engineering/9156146|lambda"
  "3|TPM, Research|Deepgram|https://www.builtinsf.com/job/technical-program-manager-research/8556932|deepgram"
  "4|Data Governance TPM|Gusto|https://www.builtinsf.com/job/data-governance-technical-program-manager/9711141|gusto"
  "5|Hardware TPM, Energy Storage|Redwood Materials|https://www.builtinsf.com/job/hardware-technical-program-manager-energy-storage/8194780|redwood"
  "6|TPM|Decagon|https://www.builtinsf.com/job/technical-program-manager/9159071|decagon"
)

echo "=== TPM JOB VERIFICATION REPORT ==="
echo "Generated: $(date -u)"
echo

for ROLE_INFO in "${ROLES[@]}"; do
  IFS='|' read -r IDX TITLE COMPANY URL ATS_LABEL <<< "$ROLE_INFO"
  
  echo "========================================"
  echo "[$IDX] $TITLE @ $COMPANY"
  echo "URL: $URL"
  echo "----------------------------------------"
  
  # Step 1: Fetch Built In detail page
  HTML=$(curl -sL -A "$USER_AGENT" "$URL" 2>&1)
  CURL_EXIT=$?
  
  if [ $CURL_EXIT -ne 0 ] || [ -z "$HTML" ]; then
    echo "  ERROR: Failed to fetch Built In page (curl exit: $CURL_EXIT)"
    echo "  STATUS: UNKNOWN - could not fetch"
    echo
    continue
  fi
  
  echo "  [OK] Built In page fetched"
  
  # Step 2: Extract job details from the page
  # Try to find job title in the page
  PAGE_TITLE=$(echo "$HTML" | grep -oP '<title>[^<]+</title>' | head -1 | sed 's/<[^>]*>//g')
  echo "  Page title: $PAGE_TITLE"
  
  # Try to find salary info
  SALARY=$(echo "$HTML" | grep -oP '(?i)(\$[0-9,]+[\s-]*\$[0-9,]+|salary[^.]*\$[0-9,]+)' | head -5)
  if [ -z "$SALARY" ]; then
    SALARY=$(echo "$HTML" | grep -oP '\$[0-9]{2,3},[0-9]{3}\s*[-–]\s*\$[0-9]{2,3},[0-9]{3}' | head -3)
  fi
  if [ -z "$SALARY" ]; then
    SALARY="Not found on page"
  fi
  echo "  Salary: $SALARY"
  
  # Try to find work mode (remote/hybrid/on-site)
  WORK_MODE=$(echo "$HTML" | grep -oP '(?i)(remote|hybrid|on[- ]site|in[- ]person|onsite)' | sort -u | head -3 | tr '\n' ', ' | sed 's/,$//')
  if [ -z "$WORK_MODE" ]; then
    WORK_MODE="Not found on page"
  fi
  echo "  Work mode: $WORK_MODE"
  
  # Step 3: Search for howToApply field
  HOW_TO_APPLY=$(echo "$HTML" | grep -oP 'howToApply["\s:]+\s*"([^"]+)"' | head -1)
  
  if [ -n "$HOW_TO_APPLY" ]; then
    ATS_URL=$(echo "$HOW_TO_APPLY" | grep -oP '"https?://[^"]+' | head -1)
    echo "  howToApply found: $ATS_URL"
  else
    echo "  howToApply field: NOT FOUND"
    
    # Step 4: Scan for ATS URLs (greenhouse, ashby, lever, workday)
    ATS_URL=$(echo "$HTML" | grep -oP 'https?://[a-zA-Z0-9.-]*(greenhouse|ashby|lever|workday|bamboohr)[a-zA-Z0-9./?-]*' | head -1)
    
    if [ -z "$ATS_URL" ]; then
      # Try broader: look for apply URLs
      ATS_URL=$(echo "$HTML" | grep -oP '"applyUrl"\s*:\s*"([^"]+)"' | head -1 | grep -oP 'https?://[^"]+')
    fi
    
    if [ -z "$ATS_URL" ]; then
      ATS_URL=$(echo "$HTML" | grep -oP 'https?://[a-zA-Z0-9./?=_%-]*careers?[a-zA-Z0-9./?=_%-]*' | head -1)
    fi
    
    if [ -z "$ATS_URL" ]; then
      # Try to find any job board link in the page
      ATS_URL=$(echo "$HTML" | grep -oP 'https?://[a-zA-Z0-9./?=_%-]*(apply|jobs?|careers?)[a-zA-Z0-9./?=_%-]*' | head -3 | tail -1)
    fi
    
    if [ -n "$ATS_URL" ]; then
      echo "  ATS URL found via regex: $ATS_URL"
    fi
  fi
  
  # Step 5: Verify ATS URL
  if [ -n "$ATS_URL" ]; then
    ATS_HTML=$(curl -sL -A "$USER_AGENT" "$ATS_URL" 2>&1)
    ATS_EXIT=$?
    ATS_STATUS=$(curl -sL -o /dev/null -w "%{http_code}" -A "$USER_AGENT" "$ATS_URL" 2>&1)
    
    if [ "$ATS_EXIT" -eq 0 ] && [ "$ATS_STATUS" = "200" ]; then
      ATS_TITLE=$(echo "$ATS_HTML" | grep -oP '<title>[^<]+</title>' | head -1 | sed 's/<[^>]*>//g')
      echo "  ATS HTTP Status: $ATS_STATUS"
      echo "  ATS Page Title: $ATS_TITLE"
      
      # Check for stale signals
      STALE_SIGNALS=0
      if echo "$ATS_HTML" | grep -qi '(?i)(page not found|this job has been filled|this position has been closed|no longer accepting applications|job expired)'; then
        STALE_SIGNALS=1
        echo "  ⚠ WARNING: Possible stale/stale signals detected"
      fi
      
      if [ $STALE_SIGNALS -eq 0 ]; then
        echo "  ✅ ACTIVE - ATS page is live"
      else
        echo "  ❌ STALE - ATS page may be closed"
      fi
    else
      echo "  ❌ ATS HTTP Status: $ATS_STATUS (NOT 200)"
      echo "  STATUS: ATS page may be down or inaccessible"
    fi
  else
    echo "  ❌ No ATS URL found on Built In page"
    echo "  STATUS: Cannot verify - no ATS link"
  fi
  
  echo
done

echo "========================================"
echo "=== VERIFICATION COMPLETE ==="
