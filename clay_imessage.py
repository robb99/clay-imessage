#!/usr/bin/env python3
"""
clay-imessage - Unified iMessage/SMS CLI for Clay

A simple CLI to send iMessages and SMS from the terminal.
Built as part of Clay's autonomy projects.

Usage:
    python3 clay_imessage.py send "Julie" "Love you!"
    python3 clay_imessage.py list
    python3 clay_imessage.py history "Julie"
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# Paths
CONFIG_DIR = Path.home() / ".clay" / "imessage"
CONTACTS_FILE = CONFIG_DIR / "contacts.json"
CONFIG_FILE = CONFIG_DIR / "config.yaml"


def ensure_config_dir():
    """Ensure config directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_contacts():
    """Load contacts from JSON file."""
    if CONTACTS_FILE.exists():
        with open(CONTACTS_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_contacts(contacts):
    """Save contacts to JSON file."""
    ensure_config_dir()
    with open(CONTACTS_FILE, 'w') as f:
        json.dump(contacts, f, indent=2)


def resolve_contact(name_or_number):
    """Resolve a contact name to phone number."""
    contacts = load_contacts()
    
    # Check if it's already a phone number
    if name_or_number.startswith('+') or name_or_number.replace('-', '').replace(' ', '').isdigit():
        return format_number(name_or_number)
    
    # Look up by name (case-insensitive)
    name_lower = name_or_number.lower()
    for contact_name, number in contacts.items():
        if contact_name.lower() == name_lower:
            return number
    
    # Partial match
    for contact_name, number in contacts.items():
        if name_lower in contact_name.lower():
            return number
    
    # Not found - return as-is (might be a number)
    return name_or_number


def format_number(number):
    """Format phone number to E.164 format."""
    # Remove all non-digit characters
    digits = ''.join(c for c in number if c.isdigit())
    
    # Add country code if missing (assume US +1)
    if len(digits) == 10:
        digits = '1' + digits
    elif len(digits) == 11 and digits.startswith('1'):
        pass  # Already has country code
    else:
        return number  # Can't format
    
    return f"+{digits}"


def cmd_send(args):
    """Send an iMessage or SMS."""
    recipient = resolve_contact(args.recipient)
    message = args.message
    
    # Determine service (imessage or sms)
    service = args.service if args.service else "auto"
    
    cmd = ["imsg", "send", "--to", recipient, "--text", message]
    if service != "auto":
        cmd.extend(["--service", service])
    
    if args.file:
        cmd.extend(["--file", args.file])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Message sent to {args.recipient}: {message}")
            return 0
        else:
            print(f"❌ Failed to send: {result.stderr}", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


def cmd_list(args):
    """List recent chats."""
    limit = args.limit
    
    try:
        result = subprocess.run(
            ["imsg", "chats", "--limit", str(limit), "--json"],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            print(f"❌ Failed to list chats: {result.stderr}", file=sys.stderr)
            return 1
        
        # Parse NDJSON (newline-delimited JSON)
        chats = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                chats.append(json.loads(line))
        
        if args.json:
            print(json.dumps(chats, indent=2))
        else:
            print(f"📱 Recent Chats (last {limit}):\n")
            for i, chat in enumerate(chats, 1):
                # Get name - try displayName, then identifier (phone), then fallback
                name = chat.get('displayName') or chat.get('identifier') or str(chat.get('id', 'Unknown'))
                service = chat.get('service', 'iMessage')
                last_msg_at = chat.get('last_message_at', '')[:10] if chat.get('last_message_at') else ''
                print(f"{i}. {name} ({service})")
                if last_msg_at:
                    print(f"   Last: {last_msg_at}")
                print()
        
        return 0
    except json.JSONDecodeError:
        print("Failed to parse chat list", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


def cmd_history(args):
    """Show message history for a chat."""
    # First resolve the contact
    recipient = resolve_contact(args.chat)
    
    # Find the chat ID by looking through chats
    try:
        result = subprocess.run(
            ["imsg", "chats", "--limit", "50", "--json"],
            capture_output=True, text=True
        )
        # Parse NDJSON
        chats = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                chats.append(json.loads(line))
        
        # Find matching chat - check identifier, name, and participants
        chat_id = None
        recipient_formatted = format_number(recipient) if not recipient.startswith('+') else recipient
        for chat in chats:
            name = chat.get('displayName', '') or ''
            identifier = chat.get('identifier', '') or ''
            # Match by identifier (phone number) or name
            if (identifier and recipient_formatted in identifier) or (name and name.lower() == args.chat.lower()):
                chat_id = chat.get('id')
                break
        
        if not chat_id:
            print(f"❌ Chat not found: {args.chat}", file=sys.stderr)
            return 1
        
        # Get history
        result = subprocess.run(
            ["imsg", "history", "--chat-id", str(chat_id), "--limit", str(args.limit), "--json"],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            print(f"❌ Failed to get history: {result.stderr}", file=sys.stderr)
            return 1
        
        # Parse NDJSON (newline-delimited JSON)
        messages = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                messages.append(json.loads(line))
        
        if args.json:
            print(json.dumps(messages, indent=2))
        else:
            print(f"💬 History with {args.chat}:\n")
            for msg in messages:
                direction = "⬅️" if msg.get('incoming') else "➡️"
                text = msg.get('text', '[attachment]')
                print(f"{direction} {text}")
        
        return 0
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


def cmd_contacts(args):
    """List or add contacts."""
    contacts = load_contacts()
    
    if args.add:
        # Add a contact
        name = args.add[0]
        number = args.add[1]
        contacts[name] = format_number(number)
        save_contacts(contacts)
        print(f"✅ Added contact: {name} -> {number}")
        return 0
    
    if args.remove:
        # Remove a contact
        name = args.remove
        if name in contacts:
            del contacts[name]
            save_contacts(contacts)
            print(f"✅ Removed contact: {name}")
        else:
            print(f"❌ Contact not found: {name}")
        return 0
    
    # List contacts
    if args.json:
        print(json.dumps(contacts, indent=2))
    else:
        if not contacts:
            print("📒 No contacts saved.")
            print("   Add one: clay_imessage.py contacts add \"Julie\" \"+15551234567\"")
        else:
            print("📒 Contacts:\n")
            for name, number in contacts.items():
                print(f"  {name}: {number}")
    return 0


def cmd_watch(args):
    """Watch for new messages."""
    cmd = ["imsg", "watch"]
    if args.chat_id:
        cmd.extend(["--chat-id", str(args.chat_id)])
    if args.attachments:
        cmd.append("--attachments")
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n👋 Stopped watching")
        return 0
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="clay-imessage - Unified iMessage/SMS CLI for Clay",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Send command
    send_parser = subparsers.add_parser("send", help="Send an iMessage or SMS")
    send_parser.add_argument("recipient", help="Recipient name or number")
    send_parser.add_argument("message", help="Message to send")
    send_parser.add_argument("-s", "--service", choices=["imessage", "sms", "auto"],
                             help="Service to use (default: auto)")
    send_parser.add_argument("-f", "--file", help="Attachment file path")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List recent chats")
    list_parser.add_argument("-l", "--limit", type=int, default=10, help="Number of chats to show")
    list_parser.add_argument("--json", action="store_true", help="JSON output")
    
    # History command
    history_parser = subparsers.add_parser("history", help="Show message history")
    history_parser.add_argument("chat", help="Chat name or number")
    history_parser.add_argument("-l", "--limit", type=int, default=20, help="Number of messages")
    history_parser.add_argument("--json", action="store_true", help="JSON output")
    
    # Contacts command
    contacts_parser = subparsers.add_parser("contacts", help="Manage contacts")
    contacts_parser.add_argument("--add", nargs=2, metavar=("NAME", "NUMBER"),
                                  help="Add a contact")
    contacts_parser.add_argument("--remove", help="Remove a contact")
    contacts_parser.add_argument("--json", action="store_true", help="JSON output")
    
    # Watch command
    watch_parser = subparsers.add_parser("watch", help="Watch for new messages")
    watch_parser.add_argument("--chat-id", type=int, help="Watch specific chat")
    watch_parser.add_argument("-a", "--attachments", action="store_true", help="Show attachments")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to command handler
    if args.command == "send":
        return cmd_send(args)
    elif args.command == "list":
        return cmd_list(args)
    elif args.command == "history":
        return cmd_history(args)
    elif args.command == "contacts":
        return cmd_contacts(args)
    elif args.command == "watch":
        return cmd_watch(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
