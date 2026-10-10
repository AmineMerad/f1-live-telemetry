# AWS deployment — NOT provisioned. Decide region/compute after measuring
# local resource use (spec: open decisions). Budget target (< USD 20/mo incl.
# live data) is unverified; price everything below before `terraform apply`.

## Pre-provisioning checklist
- [ ] Region + AZ selected; priced: compute, storage, networking, transfer,
      logging, Temporal persistence, live data subscription
- [ ] Self-hosted Temporal vs. Temporal Cloud decision recorded (persistence,
      backup, memory/disk sized; Cloud pricing reviewed if chosen)
- [ ] Small, time-bounded topology: single small host, run only during
      dev sessions + race weekends
- [ ] AWS Budget alert + explicit shutdown procedure tested (`make compose-down`
      equivalent for AWS; see docs/runbook.md)
- [ ] Data-provider terms rechecked (redistribution, branding, publication)
- [ ] No secrets in repo / TF state; provider tokens in Secrets Manager only

## Layout (when approved)
- `main.tf` — provider + minimal network/compute (TODO after sizing)
- `variables.tf` — region, instance type, flags (TODO)
