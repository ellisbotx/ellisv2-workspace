# Discord Migration Guide
**Date:** February 4, 2026  
**Purpose:** Switch from Telegram to Discord for OpenClaw

---

## Prerequisites

- Discord account (create at https://discord.com if you don't have one)
- Discord Desktop app installed (recommended) or use web browser
- 30 minutes of focused time

---

## Part 1: Create Your Discord Server (5 minutes)

### Step 1: Create Server
1. Open Discord (desktop app or https://discord.com/app)
2. Click the **+ icon** on the left sidebar (bottom of server list)
3. Click **"Create My Own"**
4. Choose **"For me and my friends"** (not a community server)
5. Name it: **"Marco's Business HQ"** (or whatever you prefer)
6. Upload server icon (optional): Use your logo or emoji 🎴
7. Click **Create**

### Step 2: Delete Default Channels
Discord creates some default channels you don't need:

1. Right-click **#general** → Delete Channel (confirm)
2. Right-click **#voice** → Delete Channel (confirm)

---

## Part 2: Create Business Channels (5 minutes)

### Create Text Channels

Right-click on **"TEXT CHANNELS"** section → **Create Channel** for each:

1. **#dashboard**
   - Topic: "Trifecta dashboard, reports, Week 2 features"
   
2. **#inventory**
   - Topic: "Stock levels, reorders, supplier issues, MCF"
   
3. **#products**
   - Topic: "SKU performance, kill/keep decisions, new product ideas"
   
4. **#automation**
   - Topic: "Scripts, cron jobs, Etsy automation, technical work"
   
5. **#analytics**
   - Topic: "Revenue analysis, profit trends, data validation"
   
6. **#general**
   - Topic: "Quick questions, status checks, misc"

**Result:** You should see 6 channels in the left sidebar.

---

## Part 3: Create Discord Bot (10 minutes)

### Step 3A: Create Application
1. Go to: https://discord.com/developers/applications
2. Click **"New Application"** (top-right)
3. Name it: **"OpenClaw"** (or "Ellis", "Business Assistant", etc.)
4. Click **Create**
5. (Optional) Upload bot avatar under "App Icon"

### Step 3B: Create Bot User
1. Click **"Bot"** in left sidebar
2. Click **"Reset Token"** (or "Add Bot" if it's your first time)
3. **IMPORTANT:** Copy the bot token that appears
   - It looks like: `YOUR_BOT_TOKEN_HERE`
   - **Save this somewhere safe** - you'll need it in Part 4
   - You can only see it once! If you lose it, you'll need to reset it again

### Step 3C: Configure Bot Permissions
Still on the Bot page:

1. Scroll down to **"Privileged Gateway Intents"**
2. Enable these three toggles:
   - ✅ **PRESENCE INTENT**
   - ✅ **SERVER MEMBERS INTENT**
   - ✅ **MESSAGE CONTENT INTENT**
3. Click **"Save Changes"** at the bottom

### Step 3D: Generate Invite Link
1. Click **"OAuth2"** → **"URL Generator"** in left sidebar
2. Under **SCOPES**, check:
   - ✅ `bot`
   - ✅ `applications.commands`
3. Under **BOT PERMISSIONS**, check:
   - ✅ `Send Messages`
   - ✅ `Read Message History`
   - ✅ `Embed Links`
   - ✅ `Attach Files`
   - ✅ `Add Reactions`
   - ✅ `Use Slash Commands`
4. Scroll down and copy the **Generated URL**

### Step 3E: Invite Bot to Your Server
1. Paste the Generated URL into a new browser tab
2. Select **"Marco's Business HQ"** (your server)
3. Click **Authorize**
4. Complete the CAPTCHA
5. Go back to Discord - you should see **OpenClaw** (or your bot name) in the member list on the right

---

## Part 4: Get Your Discord User ID (2 minutes)

### Enable Developer Mode
1. In Discord, click the ⚙️ **Settings** icon (bottom-left, next to your username)
2. Go to **"Advanced"** (in left sidebar)
3. Enable **"Developer Mode"** toggle
4. Click **ESC** to close settings

### Copy Your User ID
1. Right-click on **your username** anywhere (member list, a message you sent, etc.)
2. Click **"Copy User ID"**
3. Paste it somewhere safe (Notepad, Notes app, etc.)
   - It looks like: `123456789012345678` (18-digit number)

---

## Part 5: Update OpenClaw Configuration (5 minutes)

### Step 5A: Prepare Your Information

You should have:
- ✅ Discord Bot Token (from Step 3B)
- ✅ Your Discord User ID (from Part 4)

### Step 5B: Tell Ellis to Update Config

When you're back at your desk and ready, message me in Telegram:

```
Update OpenClaw config for Discord:

Bot Token: [paste your bot token here]
My User ID: [paste your user ID here]
```

I will:
1. Update `/Users/ellisbot/.openclaw/openclaw.json` to:
   - Disable Telegram
   - Enable Discord
   - Add your bot token
   - Add you to the allowlist (your user ID)
2. Restart the gateway
3. Test that the bot responds in Discord

---

## Part 6: Test Everything Works (3 minutes)

### Once I've updated the config:

1. Go to Discord → **#general** channel
2. Type: `@OpenClaw hello` (or whatever you named the bot)
3. You should get a response!

### Test each channel:
- Go to **#dashboard** and ask: "Show me the dashboard summary"
- Go to **#products** and ask: "What are my top 5 SKUs?"
- Go to **#general** and ask: "What's the weather today?"

### Verify agents work:
- Agents should respond in the appropriate channels
- You can still spawn sub-agents (Code, Analysis, Creative, Strategic)
- They'll report back in Discord instead of Telegram

---

## Part 7: Optional Enhancements (Do Later)

### Add Agent Routing
Configure specific agents for specific channels:
- **#automation** → Code Agent only
- **#analytics** → Analysis Agent preferred
- **#products** → Creative Agent for product ideas

(I can help set this up after basic Discord is working)

### Use Threads
For complex discussions:
1. Hover over a message
2. Click the 💬 icon (Create Thread)
3. Name it (e.g., "Feb 4 - Reorder Decision")
4. Discuss in the thread to keep main channel clean

### Pin Important Messages
Right-click any message → **Pin Message**
- Pin dashboard links
- Pin important decisions
- Pin weekly summaries

---

## Troubleshooting

### Bot doesn't respond:
- Make sure bot has "Send Messages" permission in the channel
- Check that MESSAGE CONTENT INTENT is enabled (Part 3C)
- Verify bot is online (green dot in member list)

### Bot offline:
- Check gateway is running: `ps aux | grep openclaw-gateway`
- Check Discord config is correct
- Restart gateway if needed

### Can't find bot token:
- Go back to https://discord.com/developers/applications
- Click your app → Bot → Reset Token
- Copy the new token and update OpenClaw config

---

## Summary Checklist

Before messaging me to update config, verify you have:
- ✅ Discord server created ("Marco's Business HQ")
- ✅ 6 channels created (#dashboard, #inventory, #products, #automation, #analytics, #general)
- ✅ Bot created and invited to server
- ✅ Bot token copied and saved
- ✅ Your Discord User ID copied and saved
- ✅ Bot appears in member list (offline is OK - it'll come online when I update config)

---

## When You're Ready

Message me in Telegram with:
1. Your bot token
2. Your Discord User ID

I'll handle the rest and let you know when it's ready to test!

---

**Estimated total time:** 25-30 minutes  
**Point of no return:** Once I update the config, OpenClaw switches to Discord (Telegram will stop working)  
**Can we switch back?** Yes, if needed - but let's give Discord a fair shot first!
