# LEARNING Skill: IoT Security Basics

## Purpose
Learn Internet of Things security fundamentals.

## Architecture

### Components
```
┌─────────────┐
│   Cloud     │  - Data storage
│   Backend   │  - Analytics
├─────────────┤
│   Gateway   │  - Protocol translation
│             │  - Local processing
├─────────────┤
│   Sensors/  │  - Data collection
│   Actuators │  - Physical control
└─────────────┘
```

## Protocols

### Communication
```
MQTT     - Lightweight pub/sub
CoAP     - Constrained devices
AMQP     - Enterprise messaging
HTTP     - Web-based
WebSocket - Real-time
```

### MQTT
```
Broker-based
Topics: home/sensors/temp
QoS levels
Retained messages
```

### Zigbee
```
Low-power mesh
2.4GHz band
Home automation
```

### Z-Wave
```
Sub-GHz band
Interference resistant
Home automation
```

## Common Vulnerabilities

### Attack Surfaces
```
Cloud interfaces
Mobile apps
Gateway
Protocols
Firmware
```

### Findings
```
Hardcoded credentials
Insecure APIs
No encryption
Firmware extraction
Debug interfaces
```

## Firmware Analysis

### Extraction
```bash
# Download firmware
# binwalk for magic bytes
binwalk firmware.bin

# Extract
binwalk -e firmware.bin

# Squashfs
unsquashfs firmware.bin
```

### Analysis
```bash
# Strings
strings firmware.bin | head -100

# Mount
mkdir mnt
mount -o loop rootfs.img mnt

# Find binaries
find mnt -type f -exec file {} \;
```

## Hardware Analysis

### Interfaces
```
UART/JTAG    - Debug
SPI          - Flash memory
I2C          - Sensors
GPIO         - General purpose
```

### UART Access
```bash
# Identify UART pins
# Usually: RX, TX, GND, VCC

# Connect with USB-TTL
# Common baudrates: 115200, 57600, 9600
```

## Mobile Apps

### Analysis
```bash
# Decompile
apktool d app.apk

# Find hardcoded IPs
grep -r "http://" output/

# API analysis
grep -r "api" output/
```

## Network Analysis

### Traffic Capture
```bash
# Monitor WiFi
airmon-ng start wlan0
tcpdump -i wlan0mon -n

# Analyze MQTT
mqttten client
```

## Exploitation

### Default Credentials
```
admin/admin
root/root
user/password
```

### Common Exploits
```
- Unprotected services
- Buffer overflows
- Command injection
- Authentication bypass
```

## Tools

### Hardware
```
Bus Pirate
Shikra
ChipWhisperer
JTAGulator
```

### Software
```
Firmwalker
Firmware Analysis Toolkit
Sierra Tools
```

### Network
```
Wireshark
Mosquitto (MQTT broker)
Ettercap
```

## Secure Development

### Best Practices
```
Encrypt communications
Secure boot
Firmware signing
Secure defaults
No hardcoded secrets
```

## CTF IoT Challenges
```
- Firmware extraction
- Hardware hacking
- Protocol analysis
- Mobile app analysis
- Cloud backend
```

## Defense

### Hardening
```
Change defaults
Update firmware
Network segmentation
Monitor traffic
Disable unused services
```
