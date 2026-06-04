# Integrations

CortexOS connects to external platforms for commerce, code, and content distribution. All integrations are optional — the system runs without any of them.

---

## Etsy

### Getting Your API Key

1. Go to [etsy.com/developers/your-apps](https://www.etsy.com/developers/your-apps)
2. Click **Create a New App**
3. Fill in app name and description (can be anything)
4. Note your **Keystring** (this is your `ETSY_API_KEY`)
5. Note your **Shared Secret** (this is your `ETSY_API_SECRET`)

### OAuth Flow

Etsy uses OAuth 2.0 with PKCE. CortexOS handles this automatically:

1. In CortexOS → Settings → Integrations → Etsy → **Connect**
2. You're redirected to Etsy's authorisation page
3. Approve access → redirect back to CortexOS
4. OAuth tokens are stored encrypted in PostgreSQL

**Required scopes requested:**
- `listings_r` — read listings
- `listings_w` — create/update listings
- `shops_r` — read shop info
- `transactions_r` — read order data

### What's Supported

| Feature | Supported |
|---------|-----------|
| List active listings | Yes |
| Create/update listing | Yes |
| Upload listing photos | Yes |
| Read orders | Yes |
| Revenue sync | Yes (daily cron) |
| Inventory management | Partial |
| Coupon management | No |

### Revenue Sync

Once connected, CortexOS syncs Etsy revenue daily at 2am (UTC) via Celery beat. Revenue appears in the Finance dashboard under "Etsy" channel.

---

## Gumroad

### Getting Your Access Token

1. Go to [app.gumroad.com/settings/advanced](https://app.gumroad.com/settings/advanced)
2. Scroll to **Application → Access Token**
3. Click **Generate access token**
4. Copy to `GUMROAD_ACCESS_TOKEN` in `.env`

No OAuth required — Gumroad uses a single bearer token.

### Publishing Workflow

CortexOS agents can create Gumroad products programmatically:

```json
{
  "tool": "gumroad_create_product",
  "args": {
    "name": "AI Research Report: SaaS Market 2026",
    "description": "...",
    "price": 4700,
    "file_url": "https://github.com/.../outputs/report.pdf"
  }
}
```

### What's Supported

| Feature | Supported |
|---------|-----------|
| Create product | Yes |
| Update product | Yes |
| Upload files | Yes |
| Read sales | Yes |
| Revenue sync | Yes (daily cron) |
| Discount codes | No |
| Variants | No |

---

## LemonSqueezy

### Getting Your API Key

1. Go to [app.lemonsqueezy.com/settings/api](https://app.lemonsqueezy.com/settings/api)
2. Click **Create API Key**
3. Name it (e.g., "CortexOS") and copy to `LEMONSQUEEZY_API_KEY` in `.env`

### Products and Subscriptions Sync

CortexOS syncs:
- **Products**: name, price, status
- **Orders**: customer, product, amount, date
- **Subscriptions**: plan, status, renewal date, MRR contribution

Sync runs daily at 2:30am (UTC). Access data in the Finance dashboard.

### Webhook Setup (Recommended)

For real-time updates instead of polling:

1. LemonSqueezy → Settings → Webhooks → **Add Endpoint**
2. URL: `https://api.cortexos.yourdomain.com/webhooks/lemonsqueezy`
3. Select events: `order_created`, `subscription_created`, `subscription_updated`, `subscription_cancelled`
4. Set signing secret → add to `.env` as `LEMONSQUEEZY_WEBHOOK_SECRET`

### What's Supported

| Feature | Supported |
|---------|-----------|
| Product sync | Yes |
| Order sync | Yes |
| Subscription tracking | Yes |
| MRR calculation | Yes |
| Webhook ingestion | Yes |
| Refund tracking | Partial |
| License keys | No |

---

## GitHub

### Token Scopes Needed

1. Go to [github.com/settings/tokens](https://github.com/settings/tokens) → **Generate new token (classic)**
2. Select scopes:
   - `repo` — full control of repositories (needed for file read/write)
   - `read:org` — read org membership (if using org repos)
   - `workflow` — if you want agents to trigger workflows
3. Copy to `GITHUB_TOKEN` in `.env`

**Minimum scopes** (read-only):
- `repo:status`
- `public_repo`

### What CortexOS Uses GitHub For

- **File operations**: agents can read and write files to your repos
- **Issue creation**: workflow output can create GitHub issues automatically
- **Outputs storage**: all generated media/files are saved to the configured outputs repo

### Outputs Repository

Configure in `.env`:
```env
GITHUB_TOKEN=ghp_...
GITHUB_OUTPUTS_REPO=your-org/outputs
GITHUB_OUTPUTS_BRANCH=main
```

When an agent produces a file (report, image, PDF), it's committed to:
`github.com/your-org/outputs/outputs/{venture-name}/{type}/{filename}`

---

## Langfuse (Self-Hosted)

Langfuse is included in the Docker Compose stack. No external account needed for self-hosted.

### Initial Setup

1. Start the stack: `make up`
2. Open [http://localhost:3001](http://localhost:3001)
3. Create an admin account on first visit
4. Go to **Settings** → **API Keys** → **Create**
5. Copy Secret Key and Public Key to `.env`:
   ```env
   LANGFUSE_SECRET_KEY=sk-lf-...
   LANGFUSE_PUBLIC_KEY=pk-lf-...
   LANGFUSE_HOST=http://langfuse:3000
   ```

### Tracing Configuration

Every LLM call in CortexOS is automatically traced. You see:

- **Traces**: one per agent task
- **Spans**: one per tool call or LLM generation
- **Generations**: raw prompt/completion pairs with token counts
- **Scores**: QC scores attached to generations
- **Cost**: per-model USD cost calculated automatically

### What You Can Do in Langfuse

- View full prompt histories for any task
- Compare model performance (cost vs quality)
- Set up evaluators for automatic quality scoring
- Create prompt templates and version them
- Export data for fine-tuning

### Disabling Tracing

Set in `.env`:
```env
LANGFUSE_ENABLED=false
```

This disables all Langfuse calls. The `LANGFUSE_HOST`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_PUBLIC_KEY` env vars are then ignored.

---

## Adding a New Integration

To add a new integration (e.g., Shopify, Stripe, ConvertKit):

1. Create `/backend/app/integrations/{name}/client.py` — API client
2. Create `/backend/app/integrations/{name}/sync.py` — data sync logic
3. Add Celery task in `/backend/app/tasks/integrations.py`
4. Add config fields to `Integration` model
5. Register tool in tool registry if agents should call it directly
6. Add env vars to `.env.example`
7. Document here

The integration framework handles OAuth token storage, refresh, and encryption automatically via `app.integrations.base.OAuthIntegration`.
