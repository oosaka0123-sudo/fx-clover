# GitHub Pages enablement fix

The initial Pages deployment failed because the repository did not yet have a Pages site configured. The deployment workflow now passes `enablement: true` to `actions/configure-pages@v5` so the workflow can attempt to enable Pages automatically when repository permissions allow it.

Safety boundary is unchanged:
- read-only public dashboard
- no live trade signals
- no broker account data
- no secrets
- `orders_enabled: false`
