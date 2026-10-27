#!/usr/bin/env bash
# Runs every minute from sme-sync.timer as user "sme". Pulls the 3 sources, rebuilds only on change,
# swaps the live site atomically. If anything fails, the old site keeps serving.
set -uo pipefail
ENV_FILE=${SME_ENV:-/etc/sme/sme.env}
# shellcheck disable=SC1090
source "$ENV_FILE"
BASE=/var/lib/sme
SITE=$BASE/sjsu-sme; SIGNS=$BASE/spartan-signs; MNEMO=$BASE/mnemosyne
REL=$BASE/releases; LIVE=/var/www/sjsu-sme
export GIT_TERMINAL_PROMPT=0

exec 9>"$BASE/sync.lock"; flock -n 9 || exit 0   # never run two at once

pull() {  # pull <dir> <branch>; keeps the last good checkout if the network is down
  git -C "$1" fetch -q --depth=20 origin "$2" && git -C "$1" reset -q --hard "origin/$2" \
    || echo "warn: could not update $1, using last good copy" >&2
}

pull "$SITE" "${SITE_BRANCH:-main}"
[ -d "$SIGNS/.git" ] && pull "$SIGNS" main

if [ "${MNEMO_ENABLED:-0}" = "1" ] && [ -d "$MNEMO/.git" ]; then
  export GIT_SSH_COMMAND="ssh -i $MNEMO_KEY -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"
  git -C "$MNEMO" fetch -q --depth=1 --filter=blob:none origin main \
    && git -C "$MNEMO" reset -q --hard origin/main \
    || echo "warn: could not update mnemosyne, using last good copy" >&2
fi

# Rebuild when any source moved, or every 10 minutes (so events roll from Upcoming to Past on time).
tenmin="$(date +%Y%m%d%H)$((10#$(date +%M) / 10))"
fp=$(printf '%s|%s|%s|%s' \
  "$(git -C "$SITE" rev-parse HEAD 2>/dev/null)" "$(git -C "$SIGNS" rev-parse HEAD 2>/dev/null)" \
  "$( [ "${MNEMO_ENABLED:-0}" = 1 ] && git -C "$MNEMO" rev-parse HEAD 2>/dev/null )" "$tenmin" | sha1sum | cut -c1-16)
[ -f "$BASE/.fingerprint" ] && [ "$(cat "$BASE/.fingerprint")" = "$fp" ] && exit 0

new="$REL/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$new"
if MNEMO_DIR="$MNEMO" SIGNS_DIR="$SIGNS" OUT_DIR="$new" python3 -I "$SITE/build/build.py"; then
  ln -sfn "$new" "$BASE/live.tmp" && mv -T "$BASE/live.tmp" "$LIVE"   # atomic swap
  echo "$fp" > "$BASE/.fingerprint"
  ls -1dt "$REL"/* | tail -n +4 | xargs -r rm -rf                   # keep last 3 builds
  echo "Deployed $(git -C "$SITE" rev-parse --short HEAD)"
else
  echo "build failed, keeping previous site" >&2
  rm -rf "$new"
  exit 1
fi
