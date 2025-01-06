# LINK Staking Pool Alert Bot

The **LINK Staking Pool Alert Bot** monitors the Chainlink staking pool and posts real-time updates to Twitter whenever space becomes available for staking. This bot uses Twitter to alert users about the current available LINK tokens for staking, ensuring they never miss an opportunity.

---

## 🚀 Features
1. **Real-Time Monitoring**:
   - Checks the Chainlink staking pool every 5 minutes for available space (< 40,875,000 LINK).
2. **Smart Updates**:
   - Posts only when:
     - Space is available for staking.
     - The available amount is different from the last alert.
3. **GIF Attachments**:
   - Posts a custom GIF (`LINK_diamondhand.gif`) along with the tweet to grab attention.
4. **Fails Gracefully**:
   - Posts the text-only message if the GIF upload fails.
5. **Runs Automatically**:
   - Fully automated via GitHub Actions.

---

## 🛠 How It Works
1. **Monitoring**:
   - The bot queries the Chainlink staking pool API every 5 minutes.
   - If space is available and the available amount has changed since the last post, it triggers a tweet.

2. **Posting Alerts**:
   - Tweets the available amount of LINK with the custom GIF:
     ```text
     🔥 LINK Staking Pool Update: 5,454 LINK available to stake! 🔓
     💎 Stake now: https://staking.chain.link #Chainlink
     ```

3. **Caching**:
   - The bot maintains a cache (`last_posted.txt`) to avoid duplicate alerts.

---

## 📦 Repository Structure
```plaintext
.
├── cl_staking_check_bot.py   # Main bot script
├── LINK_diamondhand.gif      # GIF attached to tweets
├── last_posted.txt           # Cache file storing the last posted amount
├── .github/workflows/
│   └── staking_pool_alert.yml  # GitHub Actions workflow
└── README.md                 # Repository documentation
```

<div align="center">
  <img src="LINK_diamondhand.gif" alt="LINK Staking Pool Alert" width="600">
</div>

