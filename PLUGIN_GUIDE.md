# RedForge Plugins Development Guide

This guide explains how to construct, package, and deploy custom extensions for RedForge.

---

## Plugin Schema

A plugin is structured as a directory containing:
* `plugin.json`: Metadata configuration defining hooks, routing, and tools.
* `skills/`: Markdown skill directories.
* `agents/`: Custom LLM agent prompts.

### Example `plugin.json`
```json
{
  "plugin_id": "shodan-connector",
  "name": "Shodan Intel Connector",
  "version": "1.0.0",
  "description": "Enables passive host recon using Shodan API queries",
  "enabled": true,
  "permissions": ["network", "storage"]
}
```

---

## Installing custom plugins

Plugins can be managed using the API Gateway or React Dashboard:

### Install via API
```bash
curl -X POST http://localhost:8000/api/v1/plugins/install \
     -H "Content-Type: application/json" \
     -d '{"plugin_id": "shodan-connector", "version": "1.0.0"}'
```

### Toggle plugin states
* **Enable**: `POST /api/v1/plugins/{id}/enable`
* **Disable**: `POST /api/v1/plugins/{id}/disable`
* **Uninstall**: `DELETE /api/v1/plugins/{id}`
