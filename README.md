<div align="center">

<svg width="780" height="180" viewBox="0 0 780 180" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0b0b0b"/>
      <stop offset="100%" stop-color="#1a1300"/>
    </linearGradient>
    <linearGradient id="bnb" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#F3BA2F"/>
      <stop offset="100%" stop-color="#FFE08A"/>
    </linearGradient>
  </defs>
  <rect width="780" height="180" fill="url(#bg)" rx="14"/>

  <!-- pulse circles -->
  <circle cx="90" cy="90" r="6" fill="#F3BA2F">
    <animate attributeName="r" values="6;28;6" dur="2.2s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="1;0;1" dur="2.2s" repeatCount="indefinite"/>
  </circle>
  <circle cx="90" cy="90" r="6" fill="#F3BA2F"/>

  <text x="160" y="78" font-family="'Courier New', monospace" font-size="44" font-weight="800" fill="url(#bnb)">
    PulseBNB
  </text>
  <text x="160" y="112" font-family="'Courier New', monospace" font-size="15" fill="#bdbdbd">
    Real builders on BNB Chain, surfaced in real time.
  </text>
  <text x="160" y="138" font-family="'Courier New', monospace" font-size="13" fill="#7a7a7a">
    AI-classified. On-chain proof. No login, no token.
  </text>
</svg>

<br/>

[![Live Demo](https://img.shields.io/badge/Live_Demo-pulsebnb--web.vercel.app-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://pulsebnb-web.vercel.app)
[![Contract](https://img.shields.io/badge/Contract-BNB_Mainnet-F3BA2F?style=for-the-badge&logo=binance&logoColor=black)](https://bscscan.com/address/0x81eADEECc493fDa12dFf77aD8c55E779d1Db016b)
[![BNB Chain](https://img.shields.io/badge/Built_on-BNB_Chain-F0B90B?style=for-the-badge)](https://www.bnbchain.org)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)

</div>

---

> **The problem:** 100+ contracts deploy to BNB Chain every day. The overwhelming majority are forks, factory templates, copy-paste meme tokens, and name-spoof scams. The next real builder — the one airdrop hunters, scouts, and VCs want to find first — is buried in the noise.
>
> **The wedge:** PulseBNB indexes every deployment in real time, runs each through an AI classifier, and surfaces the real builders with a reason. Then it lets anyone *watch* a builder on-chain — a permissionless attestation that follows your wallet, not a login.

## Live

| | |
|---|---|
| **Frontend** | [pulsebnb-web.vercel.app](https://pulsebnb-web.vercel.app) |
| **API** | [pulsebnb-api.baserep.xyz/dashboard](https://pulsebnb-api.baserep.xyz/dashboard) |
| **Watchlist contract** | [`0x81eADEECc493fDa12dFf77aD8c55E779d1Db016b`](https://bscscan.com/address/0x81eADEECc493fDa12dFf77aD8c55E779d1Db016b) (BNB mainnet) |
| **X** | [@pulsebnb1](https://x.com/pulsebnb1) |

At the time of writing, the classifier had scanned **7,200+ contracts** and surfaced **~190 real builders** — a **97% noise filter rate**. Those numbers climb 24/7; the dashboard link above is live.

## How the classifier decides

Each deployment is reduced to its on-chain signals — bytecode function selectors (ERC20 / ERC721 / ERC1155 / other), verification status, contract name — and passed to a reasoning model with one job: **unique builder, or ecosystem noise?**

- **Real** — custom app logic, original protocols, distinct code worth tracking.
- **Noise** — DEX pair templates (PancakePair et al.), factory-deployed clones, copy-paste meme tokens, dead code.
- **Spoof** — a brand-new contract claiming a famous token name (Tether, USDC, NVIDIA…) is flagged as a name-impersonation scam with high confidence. The canonical issuers deployed years ago; a fresh "TetherUSD" is not Tether.

Every verdict ships with a one-line reason and a 0–100 confidence score. The dashboard surfaces only `real` at confidence ≥ 70 — the bar is deliberately high.

## The on-chain Watchlist

[`Watchlist.sol`](contracts/Watchlist.sol) is deployed to **BNB mainnet** — permissionless, no owner, no fees, no token.

```solidity
function watch(address target) external;       // attest interest in a builder
function unwatch(address target) external;      // revoke
function watchMany(address[] calldata targets); // batch
function isWatching(address watcher, address target) view returns (bool);
function watcherCount(address target) view returns (uint256);
function totalWatches() view returns (uint256); // global counter, shown live on the dashboard
```

When you click **👁 Watch on-chain** on the frontend, your wallet signs a real `watch()` transaction on BNB Chain. No backend writes, no database of users — your watchlist is on-chain and follows your wallet anywhere.

## Architecture

```
┌─────────────┐    ┌──────────────────┐    ┌──────────────┐
│ BNB RPC     │───▶│ Indexer          │───▶│ SQLite       │
│ (block tip) │    │ Python +         │    │ contracts +  │
└─────────────┘    │ APScheduler, PM2 │    │ deployers    │
                   └─────┬────────────┘    └──────┬───────┘
                         │ each new contract       │
                         ▼                         ▼
        ┌────────────────────────┐    ┌─────────────────────────┐
        │ AI Classifier          │    │ FastAPI  (port 8093)     │
        │ via LiteLLM router      │    │ /dashboard /feed /best   │
        │ → label + reason + score│    │ /leaderboard /hot        │
        └────────────────────────┘    │ /builder/:a /watchlist/:a│
                                       └───────────┬─────────────┘
                                                   │
                         ┌─────────────────────────┴────────┐
                         ▼                                   ▼
                  ┌─────────────┐                  ┌────────────────────┐
                  │ Next.js UI  │── Watch button ─▶│ Watchlist.sol      │
                  │ (Vercel)    │   (wallet tx)    │ (BNB mainnet)      │
                  └─────────────┘                  └────────────────────┘
                                                   reads totalWatches ──┘
                                                   back into /dashboard
```

## Tech stack

| Layer | Choice | Notes |
|---|---|---|
| Indexer | Python 3 + APScheduler | Polls block tip, classifies bytecode by selectors, stores to SQLite (WAL) |
| Data source | Etherscan V2 unified API | One key, `chainid=56` for BNB |
| AI classifier | LiteLLM router → reasoning model | Local routing; binary real/noise + reason + score |
| Identity | Space ID + Farcaster resolvers | BNB-native + cross-chain handles where available |
| Storage | SQLite | Lean read patterns, zero ops overhead |
| API | FastAPI (port 8093) | CORS-open, read-only, fronted by Cloudflare tunnel |
| Frontend | Next.js (App Router) on Vercel | Dark + BNB-yellow, polls the API, wallet-native Watch button |
| On-chain | `Watchlist.sol`, Foundry, Solc 0.8.33 | Deployed to BNB mainnet, permissionless |

## Local dev

```bash
git clone https://github.com/Makabeez/pulsebnb.git
cd pulsebnb
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add your Etherscan V2 API key + LiteLLM endpoint
python indexer.py             # terminal 1 — starts indexing + classifying
./start-api.sh                # terminal 2 — FastAPI on :8093
curl http://127.0.0.1:8093/dashboard
```

Frontend lives in a separate repo ([pulsebnb-web](https://github.com/Makabeez/pulsebnb-web)); point `NEXT_PUBLIC_API_URL` at your API and `npm run dev`.

## Production

```bash
pm2 start ecosystem.config.js   # absolute paths (WSL gotcha)
pm2 save
```

API fronted via Cloudflare tunnel at `pulsebnb-api.baserep.xyz`; frontend on Vercel.

## Contract deployment

```bash
cd contracts
export PATH="$HOME/.foundry/bin:$PATH"
forge create src/Watchlist.sol:Watchlist \
  --rpc-url https://bsc-dataseed.binance.org \
  --private-key $DEPLOYER_PK \
  --broadcast
```

## Hackathon

Built solo for **[BNB Hack: Online Edition](https://www.bnbchain.org/en/hackathons/bnb-ai-hack)** (June 2026). Lineage: ports and extends the author's Base Builder Radar to BNB Chain, adding the AI classifier and the on-chain watchlist.

## License

MIT — fork it, ship it, win with it.
