# sigma-to-spl

![CI](https://github.com/cray44/sigma-to-spl/actions/workflows/validate.yml/badge.svg)

A thin wrapper around [pySigma](https://github.com/SigmaHQ/pySigma) and the [Splunk backend](https://github.com/SigmaHQ/pySigma-backend-splunk) that adds opinionated post-processing for production Splunk deployments.

`sigma-cli` handles the conversion. This tool handles the gap between "syntactically valid SPL" and "SPL you can actually deploy."

---

## What it adds on top of sigma-cli

- **Field mapping** — translates Sigma generic field names to your environment's actual field names (Corelight/Zeek sourcetypes, CIM-mapped fields, custom aliases)
- **Index and sourcetype injection** — prepends `index=` and `sourcetype=` based on log source category, configurable per environment
- **Macro substitution** — replaces common patterns with your Splunk macros (e.g., `dns_traffic` instead of raw sourcetype strings)
- **Output formats** — raw SPL, `savedsearches.conf` stanza, or a full alert stub ready to paste into Splunk
- **Batch conversion** — convert a directory of Sigma rules and write one SPL file per rule
- **CI-ready** — exits non-zero on conversion failure; designed to run in GitHub Actions

---

## Installation

```bash
pip install -r requirements.txt
```

Requires Python 3.10+.

---

## Usage

**Convert a single rule:**
```bash
python -m sigma_to_spl convert rules/network/dns-tunneling-high-entropy-subdomains.yml
```

**Convert a directory:**
```bash
python -m sigma_to_spl convert rules/ --output-dir output/
```

**Output as savedsearches.conf stanza:**
```bash
python -m sigma_to_spl convert rules/network/dns-tunneling-high-entropy-subdomains.yml --format savedsearches
```

**Use a custom field mapping config:**
```bash
python -m sigma_to_spl convert rules/ --config config/corelight.yml
```

---

## Configuration

Copy `config/corelight.yml` and edit to match your environment:

```yaml
# config/corelight.yml
index_map:
  dns: "index=network sourcetype=corelight_dns"
  firewall: "index=network sourcetype=corelight_conn"
  process_creation: "index=endpoint sourcetype=crowdstrike_falcon"

field_map:
  src_ip: "id.orig_h"
  dst_ip: "id.resp_h"
  dns_query: "query"
  dns_query_type: "qtype_name"

macros:
  dns_traffic: "`corelight_dns`"
  internal_networks: "`internal_subnets`"
```

---

## CI Usage (GitHub Actions)

```yaml
- name: Validate and convert Sigma rules
  uses: ./.github/workflows/validate.yml
```

See [`.github/workflows/validate.yml`](.github/workflows/validate.yml) for the full workflow.

---

## Rules

Sample Sigma rules are in `rules/` — these are the same rules documented in [detection-notes](https://github.com/cray44/detection-notes) with the Sigma rule as the source of truth.

---

## Limitations

- pySigma's Splunk backend handles most condition types but has gaps with complex aggregations. Where the generated SPL needs manual adjustment, this tool will note it in a comment at the top of the output.
- Entropy scoring is not expressible in Sigma's condition syntax — rules that require it will output a base SPL query with a `# MANUAL: add entropy scoring` comment.
