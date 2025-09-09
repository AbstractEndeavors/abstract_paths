# build-react.sh
set -euo pipefail
cd "${1:-.}"

if [ -s "$HOME/.nvm/nvm.sh" ]; then . "$HOME/.nvm/nvm.sh"; fi
command -v corepack >/dev/null 2>&1 && corepack enable >/dev/null 2>&1 || true

if [ -f yarn.lock ]; then
  yarn install --frozen-lockfile
  yarn build
elif [ -f pnpm-lock.yaml ]; then
  pnpm install --frozen-lockfile
  pnpm build
else
  npm ci
  npm run build
fi
