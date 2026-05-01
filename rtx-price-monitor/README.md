# RTX Price Monitor

A GPU price alert workspace. Every hour, it scrapes RTX 5080 listings from major retailers, checks for prices under $1,400, and sends you a Gmail alert if any qualifying listings are found.

> This workspace is set up for RTX 5080s, but it's not hard-coded to them. If you want to track something else — a different GPU, a piece of furniture, concert tickets, whatever — just ask Friday in chat and it will reconfigure the workspace for you.

It checks four retailers on the hour:

- **Best Buy, Newegg, Amazon, B&H Photo** — scraped for current price, availability status, and direct purchase URL, focused specifically on the RTX 5080 (not 5080 Super, not 5090)

If any listing comes back in-stock and under $1,400, you get an email with the retailer, product name, price, availability, and a direct link to buy. If nothing qualifies, nothing is sent.

---

## Setup

### 1. Download Friday

1. Go to [hellofriday.ai](https://hellofriday.ai) and download the macOS installer
2. Open the DMG and drag Friday to your Applications folder
3. Launch Friday and complete the initial setup

### 2. Import the workspace

1. Open Friday and go to **Discover Spaces**
2. Find this workspace and click it
3. Click **Add Space**

### 3. Connect Gmail

1. Go to **MCP Catalog → Gmail**
2. Under **Credentials**, click **Add one**
3. Follow the OAuth flow to grant access to your Google account (alerts are sent from and to this account)

### 4. Set your recipient email

1. Go to **Agents > rtx-alert-emailer**
2. In the agent prompt, find: `[ADD EMAIL RECIPIENT HERE]`
3. Replace it with your email address

Once both steps are done, the schedule fires automatically at the top of every hour.

---

## What the alert looks like

> **Subject: RTX 5080 Alert: Sub-$1400 listing found!**
>
> An automated price monitor found the following RTX 5080 listings under $1,400:
>
> **Newegg** — ASUS TUF Gaming GeForce RTX 5080
> Price: $1,349 | In Stock
> Link: https://www.newegg.com/...
>
> *(Found by your Friday RTX Price Monitor — running hourly)*

If no listings qualify, no email is sent.

---

## How to use it

It runs automatically. Nothing to trigger, nothing to open.

If you want to run a check immediately outside the hourly schedule, trigger the `rtx-price-check-cron` signal from the workspace.

---

## How it works

| Component | Role |
|---|---|
| `rtx-price-scraper` agent | Bundled web agent that searches Best Buy, Newegg, Amazon, and B&H for current RTX 5080 listings and returns structured price data |
| `rtx-alert-emailer` agent | LLM agent (Claude Sonnet) that reviews the scraped data and sends a Gmail alert if any listing is under $1,400 and in stock |
| `rtx-price-monitor` job | Two-state FSM: scrape prices → evaluate and alert |
| `rtx-price-check-cron` signal | Schedule signal firing at `0 * * * *` in `America/Los_Angeles` (top of every hour, Pacific) |
| `google-gmail` MCP server | Provides `send_gmail_message` for outbound alerts |

The cron signal fires the `rtx-price-monitor` FSM. The FSM runs the scraper first, passes its output to the emailer, and the emailer decides whether to send — or stays silent if nothing qualifies.

---

## Notes

- The price threshold is $1,400. To change it, update the `rtx-alert-emailer` prompt with your preferred ceiling.
- The scraper targets the RTX 5080 specifically — not the 5080 Super or 5090. If you want to track a different model, update the `rtx-price-scraper` prompt.
- No email is sent on clean runs. You'll only hear from this workspace when something actionable turns up.
- To change the recipient, update the `rtx-alert-emailer` agent prompt and replace the email address.
- All data stays within your Friday workspace and Google OAuth session. Nothing is routed through external services beyond the LLM call, Google's own APIs, and the public retailer pages being scraped.
