# sigma-to-spl

![CI](https://github.com/cray44/sigma-to-spl/actions/workflows/validate.yml/badge.svg)

pySigma converts Sigma rules to syntactically valid SPL. This tool handles the gap between "valid SPL" and "SPL you can actually deploy" — index routing, environment field names, Splunk macros, and savedsearches.conf output. Paired with detection-validator, every rule is also asserted against real log samples before it ships.

---

## What it adds

- **Field mapping** — translates Sigma generic field names to your environment's actual field names (Corelight/Zeek sourcetypes, CIM-mapped fields)
- **Index and sourcetype injection** — prepends `index=` and `sourcetype=` based on logsource category, configurable per environment
- **Macro substitution** — replaces raw sourcetype strings with your Splunk macros
- **MANUAL: warnings** — flags rules that need SPL additions the Sigma condition can't express (entropy scoring, aggregations, SPL-only filtering)
- **Output formats** — raw SPL or `savedsearches.conf` stanza ready to paste
- **Batch conversion** — convert a directory of rules, one SPL file per rule

---

## Installation

```bash
pip install -r requirements.txt
pip install -e .
```

Requires Python 3.10+.

---

## Usage

**Convert a single rule:**
```bash
python -m sigma_to_spl convert rules/network/dns-tunneling-high-entropy-subdomains.yml
```

Output:
```
* | title: DNS Tunneling via High-Entropy Subdomains
* | id: a8f3b2c1-4d5e-6f7a-8b9c-0d1e2f3a4b5c
* | status: experimental
* | description: Detects DNS queries with long subdomain labels indicative of data encoding
* | MANUAL: this rule category may require entropy scoring — see detection writeup for SPL additions

index=network sourcetype=corelight_dns qtype_name="TXT" OR NOT qtype_name=* OR qtype_name="CNAME"
    NOT (query IN ("*.internal.corp", "*.local"))
```

**Convert to savedsearches.conf stanza:**
```bash
python -m sigma_to_spl convert rules/network/dns-tunneling-high-entropy-subdomains.yml --format savedsearches
```

Output:
```
[dns-tunneling-high-entropy-subdomains]
search = index=network sourcetype=corelight_dns qtype_name="TXT" ...
dispatch.earliest_time = -24h
dispatch.latest_time = now
enableSched = 1
cron_schedule = 0 * * * *
alert.track = 1
```

**Convert a directory:**
```bash
python -m sigma_to_spl convert rules/ --output-dir output/
```

**Custom field mapping config:**
```bash
python -m sigma_to_spl convert rules/ --config config/corelight.yml
```

---

## MANUAL: warnings

Some rules require SPL logic that Sigma's condition syntax can't express — entropy scoring, `streamstats`-based beaconing, risk score additions. The PostProcessor emits a `MANUAL:` line in the output header when it detects:

- Logsource category is `dns` (entropy scoring required)
- Rule contains `count by`/`stats` aggregation
- Rule YAML contains a `# NOTE:` comment (SPL-only additions documented inline)

`MANUAL:` rules are still CI-tested — detection-validator asserts malicious events fire at the Sigma tier and treats benign false positives as expected (WARN, not FAIL). The SPL additions handle precision; the Sigma layer handles coverage.

---

## Configuration

Copy `config/corelight.yml` and edit to match your environment:

```yaml
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
```

---

## CI

Every push runs two jobs:

- **convert** — converts all rules, exits non-zero on any conversion failure
- **validate** — runs [detection-validator](https://github.com/cray44/detection-validator) against all rules with test-data samples; asserts malicious events match and benign events don't

The validate job checks out [detection-notes](https://github.com/cray44/detection-notes) and detection-validator as siblings so relative paths in `config/validator.yml` resolve identically to local dev.

[detection-workbench](https://github.com/cray44/detection-workbench) wraps this converter — `workbench convert <slug>` calls sigma-to-spl directly and stores the SPL output in the detection record.

---

## Rules

`rules/` contains the Sigma source of truth for all detections documented in [detection-notes](https://github.com/cray44/detection-notes). The ADS writeup references the rule by path; the rule is never embedded inline.

| Category | Rules |
|----------|-------|
| network | [DNS tunneling](rules/network/dns-tunneling-high-entropy-subdomains.yml), [TLS C2 via JA4](rules/network/tls-c2-ja4-certificate-anomalies.yml), [statistical beaconing](rules/network/statistical-beaconing-zeek-conn-log.yml), [SMB lateral movement](rules/network/smb-lateral-movement-admin-shares.yml) |
| identity | [OAuth device code phishing](rules/identity/oauth-device-code-phishing.yml), [Entra ID SPN credential addition](rules/identity/entra-id-service-principal-credential-addition.yml), [Kerberoasting RC4 downgrade](rules/windows/kerberoasting-rc4-downgrade.yml) |
| cloud | [AWS IAM privilege escalation](rules/cloud/aws-iam-privilege-escalation-policy-attachment.yml), [Azure illicit OAuth consent grant](rules/cloud/azure-illicit-oauth-consent-grant.yml), [AWS EC2 snapshot exfiltration](rules/cloud/aws-ec2-snapshot-exfiltration.yml) |
| endpoint | [LSASS process access](rules/endpoint/lsass-process-access-credential-dumping.yml), [WMI event subscription persistence](rules/windows/wmi-event-subscription-persistence.yml) |
