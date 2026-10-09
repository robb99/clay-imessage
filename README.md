# clay-imessage 📱

Unified iMessage/SMS CLI for Clay - send messages to family and friends.

## Why?

Clay already has multiple communication channels:
- **TTS** (clay-voice) - speaks through Home Assistant speakers
- **Email** (clay_mailer) - sends emails
- **Push** (clay-push) - instant push notifications via ntfy

What's missing? **iMessage/SMS** - the most direct way to reach someone's phone. Now Clay can send text messages to Robb's family directly.

## Requirements

- macOS with Messages.app signed in
- `imsg` CLI tool installed: `brew install steipete/tap/imsg`
- Full Disk Access for terminal (System Settings → Privacy & Security → Full Disk Access)
- Automation permission for Messages.app

## Setup

1. **Install imsg:**
   ```bash
   brew install steipete/tap/imsg
   ```

2. **Grant permissions:**
   - Full Disk Access: System Settings → Privacy & Security → Full Disk Access → Enable terminal
   - Automation: System Settings → Privacy & Security → Automation → Enable terminal (for Messages.app)

3. **Add contacts (optional but recommended):**
   ```bash
   python3 tools/clay_imessage.py contacts add "Julie" "+15551234567"
   python3 silk" "+15559876543"
   ```

## Usage

### Send a Message

```bash
# By name (if contact saved)
python3 tools/clay_imessage.py send "Julie" "Love you!"

# By phone number
python3 tools/clay_imessage.py send "+15551234567" "On my way home!"

# Force SMS (green bubble)
python3 tools/clay_imessage.py send "Julie" "Message" --service sms

# With attachment
python3 tools/clay_imessage.py send "Julie" "Check this out" --file /path/to/photo.jpg
```

### List Recent Chats

```bash
python3 tools/clay_imessage.py list
python3 tools/clay_imessage.py list --limit 5
python3 tools/clay_imessage.py list --json
```

### Message History

```bash
python3 tools/clay_imessage.py history "Julie"
python3 tools/clay_imessage.py history "Julie" --limit 10
```

### Manage Contacts

```bash
# List saved contacts
python3 tools/clay_imessage.py contacts

# Add a contact
python3 tools/clay_imessage.py contacts add "Julie" "+15551234567"

# Remove a contact
python3 tools/clay_imessage.py contacts --remove Julie
```

### Watch for New Messages

```bash
# Watch all new messages
python3 tools/clay_imessage.py watch

# Watch specific chat
python3 tools/clay_imessage.py watch --chat-id 1
```

## Contact Storage

Contacts are stored in `~/.clay/imessage/contacts.json`:

```json
{
  "Julie": "+15551234567",
  "Silas": "+15559876543"
}
```

## Integration Examples

### In Presence Monitor
```python
# When someone arrives home
os.system('python3 tools/clay_imessage.py send "Julie" "I just arrived home!"')
```

### In Morning Briefing
```python
# Send daily summary to family
subprocess.run(['python3', 'tools/clay_imessage.py', 'send', 'Julie', 'Good morning! Have a great day!'])
```

### In Security Alerts
```python
# Alert on security event
subprocess.run(['python3', 'tools/clay_imessage.py', 'send', 'Robb', 'Motion detected at front door!', '--service', 'sms'])
```

## Files

- `clay_imessage.py` - Main CLI tool
- `README.md` - This file
- `~/.clay/imessage/contacts.json` - Saved contacts (auto-created)

## License

MIT
