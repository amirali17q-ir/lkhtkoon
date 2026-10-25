#!/data/data/com.termux/files/usr/bin/bash
# One-time setup for Termux. Secrets stay in local files that git ignores.
cd "$(dirname "$0")"
pkg update -y && pkg install -y python
pip install -r requirements.txt

read -s -p "Bot token (from @BotFather): " T; echo
echo "$T" > token.txt
read -p "Page URL (https://...github.io/...): " U
echo "$U" > url.txt
read -p "Your numeric Telegram ID (Enter to skip, get it later with /id): " O
[ -n "$O" ] && echo "$O" > owner.txt

echo
echo "Done. Start with:  termux-wake-lock; python bot.py"
