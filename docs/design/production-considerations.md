# Design: Production Considerations

> These topics are **not implemented in this mock environment** due to cost and complexity
> constraints. They are documented here to demonstrate awareness of what a production-grade
> enterprise deployment requires.
>
> For implementation-level decisions actually made in this repository, see
> [`docs/design/platform-layer.md`](platform-layer.md).

---

## Network Isolation

### VNet per Workspace

Each Databricks workspace requires its own VNet (or dedicated subnet range). In a
multi-workspace architecture (dev / staging / prod / biz), this means managing multiple VNets
and their peering relationships.

### Hub-and-Spoke Topology

For enterprise environments connected to a corporate network, a hub-and-spoke model is typical:

- A shared hub VNet handles connectivity to on-premises or corporate networks (via ExpressRoute
  or VPN Gateway)
- Each workspace VNet is a spoke, peered to the hub
- All egress traffic routes through the hub for inspection and control

This adds significant setup effort but is usually non-negotiable in large organizations with
existing network governance.

### VNet Injection Scope — A Common Oversight

VNet Injection controls where compute nodes (clusters, Serverless) are deployed — it does not
cover the Databricks Control Plane (Workspace UI, API, Job scheduler), which is a
Databricks-managed SaaS endpoint. To restrict access to the Control Plane, a separate measure
is required: either an IP Allowlist or Azure Private Link for the Control Plane endpoint.
Treating VNet Injection alone as "network isolation complete" is a common oversight.

### CI/CD Impact

Network isolation has a direct impact on CI/CD execution. GitHub-hosted runners operate from
dynamic IPs and cannot reach a network-isolated workspace by default. Two options:

- **GitHub-hosted runner + IP allowlist**: Assign a static IP to the runner (via a NAT Gateway
  or similar) and add it to the Workspace IP access list
- **Self-hosted runner**: Deploy a runner inside the VNet — full network access, but adds
  operational overhead for runner maintenance

Neither option is free. Factor this in when deciding how aggressively to isolate the workspace
network.

---

## Storage Account Architecture

Storage Account architecture is the most consequential infrastructure decision in a Unity
Catalog deployment — and the right answer depends on organizational requirements.

**Decision tree:**

```
Q: Can all Unity Catalog data live in a single Storage Account?
│
├─ Yes (cost simplicity, single team, uniform redundancy acceptable)
│   └─ Single Storage Account + VNet Injection
│       ✓ One Private Endpoint to manage
│       ✓ Simpler NCC configuration if using Serverless compute
│       ✗ No per-team cost attribution at Storage layer
│       ✗ Redundancy level (LRS / ZRS / GRS) unified across all data
│
└─ No (team-level cost separation needed, or Prod requires higher redundancy)
    └─ Multiple Storage Accounts
        ✓ Cost attribution per team or environment
        ✓ GRS for Prod, LRS for dev/staging (cost optimization)
        ✗ Private Endpoint required per Storage Account
        ✗ NCC configuration multiplies with each account
        ✗ Operational overhead increases significantly
```

**Recommendation:** Default to a single Storage Account unless there is a clear organizational
requirement for cost separation or differential redundancy. The operational cost of managing
multiple Private Endpoints and NCC configurations is frequently underestimated.

---

## Serverless Compute & Network Configuration (NCC)

If Serverless compute is used (increasingly common as the default for jobs and SQL warehouses),
**Network Connectivity Configuration (NCC)** must be explicitly set up to allow Serverless
nodes to reach the Storage Account via Private Endpoint.

This is a common oversight: classic compute (with VNet Injection) reaches Storage through the
injected VNet, but Serverless compute runs outside the customer VNet by default. Without NCC,
Serverless jobs will fail to access Storage even if the rest of the network config is correct.

In a multi-Storage-Account setup, NCC configuration must be repeated for each account — another
reason to prefer a single Storage Account where possible.
