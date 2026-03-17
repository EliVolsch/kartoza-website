# Kartoza Website Migration Plan

## Executive Summary

This document outlines the migration strategy for transitioning `kartoza.com` from the current ERPNext-hosted website to a new Hugo-based static site, while preserving ERPNext functionality on a dedicated subdomain (`erp.kartoza.com`).

## Current State vs Target State

### Current Architecture

```mermaid
flowchart TB
    subgraph current["CURRENT STATE"]
        dns1["DNS<br/>kartoza.com"]

        subgraph frappe1["Frappe Cloud Server"]
            web["Website"]
            erp["ERP System"]
            api1["API"]
        end

        subgraph integrations1["Integrations"]
            apisix1["APISIX"]
            ts1["Timesheets"]
            train1["Training"]
        end

        dns1 --> frappe1
        frappe1 --> integrations1
    end

    style current fill:#ffe6e6,stroke:#cc0000
    style frappe1 fill:#ffcccc,stroke:#990000
    style integrations1 fill:#ffdddd,stroke:#aa0000
```

### Target Architecture

```mermaid
flowchart TB
    subgraph target["TARGET STATE"]
        dns2["DNS<br/>kartoza.com"]
        dns3["DNS<br/>erp.kartoza.com"]

        subgraph hugo["kartoza.do.kartoza.com"]
            hugosite["Hugo Site"]
            apisix2["APISIX Gateway"]
            analytics["Google Analytics"]
            salespipe["Sales Pipeline"]
        end

        subgraph frappe2["Frappe Cloud Server"]
            erp2["ERP System"]
            api2["API"]
        end

        subgraph integrations2["Downstream Services"]
            ts2["Timesheets"]
            train2["Training Courses"]
            sales2["Sales API"]
        end

        dns2 --> hugo
        dns3 --> frappe2
        hugo --> apisix2
        frappe2 --> apisix2
        apisix2 --> integrations2
    end

    style target fill:#e6ffe6,stroke:#00cc00
    style hugo fill:#ccffcc,stroke:#009900
    style frappe2 fill:#ddffdd,stroke:#00aa00
    style integrations2 fill:#eeffee,stroke:#00bb00
```

## Migration Timeline

```mermaid
gantt
    title Migration Schedule
    dateFormat  YYYY-MM-DD
    section DNS Prep
    Register erp.kartoza.com           :done, dns1, 2026-02-27, 1d
    Register kartoza.do.kartoza.com    :done, dns2, 2026-02-27, 1d
    Frappe DNS update request          :active, dns3, 2026-02-27, 2d
    section Development
    Google Analytics integration       :dev1, 2026-02-28, 2d
    Sales pipeline Hugo+APISIX         :dev2, 2026-02-28, 2d
    section Go-Live
    Deploy Hugo site                   :crit, go1, 2026-03-02, 1d
    Update APISIX configuration        :crit, go2, 2026-03-02, 1d
    Training integration deploy        :go3, 2026-03-02, 1d
    Timesheets API update              :go4, 2026-03-02, 1d
    section Verification
    Post-go-live monitoring            :ver1, 2026-03-03, 2d
```

## Migration Sequence

```mermaid
sequenceDiagram
    participant T as Tharanath
    participant M as Marike
    participant Mo as Moloko
    participant Ti as Tim
    participant D as Dimas
    participant F as Frappe

    rect rgb(255, 230, 230)
        Note over T,F: FRIDAY - DNS Preparation
        T->>F: 1. Register erp.kartoza.com → current server
        T->>T: 2. Register kartoza.do.kartoza.com
        M->>F: 3. Request DNS update for both domains
        F-->>M: Confirm dual-domain registration
    end

    rect rgb(230, 230, 255)
        Note over T,F: WEEKEND - Development Work
        Ti->>Ti: 4. Integrate Google Analytics
        Ti->>Ti: 5. Integrate Sales Pipeline (Hugo + APISIX)
    end

    rect rgb(230, 255, 230)
        Note over T,F: MONDAY - Go-Live
        T->>T: 6. Deploy Hugo to kartoza.do.kartoza.com
        Mo->>Mo: 7. Update APISIX → erp.kartoza.com
        Mo->>Mo: 8. Deploy Training integration
        D->>D: 9. Update Timesheets API address
    end

    rect rgb(255, 255, 230)
        Note over T,F: VERIFICATION
        T->>T: Verify all systems operational
        Mo->>Mo: Confirm APISIX routing
        D->>D: Confirm Timesheets functional
    end
```

## Task Dependencies

```mermaid
flowchart TD
    START([START - Friday]) --> dns1
    START --> dns2
    START --> dns3

    dns1["1. Register erp.kartoza.com<br/>(Tharanath)"]
    dns2["2. Register kartoza.do.kartoza.com<br/>(Tharanath)"]
    dns3["3. Frappe DNS Update<br/>(Marike)"]

    dns2 --> weekend
    dns3 --> weekend

    subgraph weekend["Weekend Development"]
        ga["4. Google Analytics<br/>(Tim)"]
        sales["5. Sales Pipeline<br/>(Tim)"]
    end

    weekend --> deploy
    dns1 --> apisix

    deploy["6. Hugo Deploy<br/>(Tharanath)"]

    deploy --> apisix

    apisix["7. APISIX Update<br/>(Moloko)"]

    apisix --> training
    apisix --> timesheet
    apisix --> verify

    training["8. Training Integration<br/>(Moloko)"]
    timesheet["9. Timesheets API<br/>(Dimas)"]
    verify["VERIFY ALL SYSTEMS"]

    training --> complete
    timesheet --> complete
    verify --> complete

    complete([MIGRATION COMPLETE])

    style START fill:#f9f,stroke:#333,stroke-width:2px
    style complete fill:#9f9,stroke:#333,stroke-width:2px
    style weekend fill:#e6e6ff,stroke:#333
```

## System Integration Architecture

```mermaid
flowchart TB
    subgraph public["Public Internet"]
        user["Users"]
    end

    subgraph dns["DNS Layer"]
        kartoza["kartoza.com"]
        erpdns["erp.kartoza.com"]
    end

    subgraph newinfra["New Infrastructure"]
        hugo["Hugo Static Site"]
        apisix["APISIX Gateway"]
        ga["Google Analytics"]
        salespipe["Sales Pipeline"]
    end

    subgraph erpnext["ERPNext (Frappe Cloud)"]
        erpsys["ERP System"]
        erpapi["ERPNext API"]
    end

    subgraph services["Integrated Services"]
        timesheets["timesheets.kartoza.com"]
        training["Training Courses"]
        salesapi["Sales API"]
    end

    user --> kartoza
    user --> erpdns
    kartoza --> hugo
    erpdns --> erpsys
    hugo --> apisix
    erpapi --> apisix
    apisix --> timesheets
    apisix --> training
    apisix --> salesapi
    hugo --> ga
    hugo --> salespipe

    style public fill:#f5f5f5,stroke:#333
    style dns fill:#e1f5fe,stroke:#0288d1
    style newinfra fill:#e8f5e9,stroke:#388e3c
    style erpnext fill:#fff3e0,stroke:#f57c00
    style services fill:#fce4ec,stroke:#c2185b
```

## Detailed Task Breakdown

### Phase 1: DNS Preparation (Friday)

| Task | Owner | Description | Dependencies | Rollback |
|------|-------|-------------|--------------|----------|
| 1.1 | Tharanath | Register `erp.kartoza.com` pointing to current ERPNext server IP | None | Remove DNS record |
| 1.2 | Tharanath | Register `kartoza.do.kartoza.com` with production deployment infrastructure | None | Remove DNS record |
| 1.3 | Marike | Contact Frappe Cloud to update DNS configuration | Task 1.1 | Frappe reverts DNS |

**Frappe DNS Request Details:**
- Reference: https://discuss.frappe.io/t/erpnext-domain-change/159241
- Request both `kartoza.com` AND `erp.kartoza.com` to be registered
- This dual registration enables rollback capability
- Must be completed and verified before Monday

### Phase 2: Development Work (Weekend)

| Task | Owner | Description | Dependencies | Rollback |
|------|-------|-------------|--------------|----------|
| 2.1 | Tim | Integrate Google Analytics into Hugo site | None | Remove GA script |
| 2.2 | Tim | Integrate sales pipeline functionality into Hugo & APISIX | None | Disable feature flag |

### Phase 3: Go-Live (Monday)

| Task | Owner | Description | Dependencies | Rollback |
|------|-------|-------------|--------------|----------|
| 3.1 | Tharanath | Deploy Hugo site to `kartoza.do.kartoza.com` | Phase 1, Phase 2 | Point DNS back to ERPNext |
| 3.2 | Moloko | Update APISIX API configuration to use `erp.kartoza.com` | Task 1.3, 3.1 | Revert APISIX config |
| 3.3 | Moloko | Verify and deploy APISIX integration with training course purchases | Task 3.2 | Disable integration |
| 3.4 | Dimas | Update API address for `timesheets.kartoza.com` | Task 3.2 | Revert API endpoint |

## Rollback Plan

### Rollback Decision Tree

```mermaid
flowchart TD
    issue["Issue Detected"] --> severity{"Severity?"}

    severity -->|Critical| immediate["Immediate Rollback"]
    severity -->|Moderate| partial["Partial Rollback"]
    severity -->|Minor| monitor["Monitor & Fix Forward"]

    immediate --> dns_rollback["1. DNS: Point kartoza.com<br/>back to ERPNext"]
    dns_rollback --> apisix_rollback["2. APISIX: Revert to<br/>kartoza.com endpoint"]
    apisix_rollback --> timesheet_rollback["3. Timesheets: Revert<br/>API endpoint"]
    timesheet_rollback --> verify_rollback["4. Verify all systems"]

    partial --> which{"Which Component?"}
    which -->|Analytics| ga_off["Remove GA script"]
    which -->|Sales Pipeline| sales_off["Disable feature flag"]
    which -->|Training| training_off["Disable APISIX route"]
    which -->|Timesheets| ts_off["Revert API config"]

    monitor --> hotfix["Deploy hotfix"]
    hotfix --> retest["Retest affected systems"]

    style issue fill:#ffcccc,stroke:#cc0000
    style immediate fill:#ff9999,stroke:#990000
    style partial fill:#ffcc99,stroke:#cc6600
    style monitor fill:#99ff99,stroke:#009900
```

### Rollback Contacts

| Component | Rollback Action | Owner | Time to Rollback |
|-----------|-----------------|-------|------------------|
| DNS | Point `kartoza.com` to ERPNext | Tharanath | ~15 min (propagation) |
| APISIX | Revert configuration | Moloko | ~5 min |
| Google Analytics | Remove tracking script | Tim | ~5 min |
| Sales Pipeline | Disable feature flag | Tim | ~5 min |
| Training Integration | Disable APISIX route | Moloko | ~5 min |
| Timesheet API | Revert endpoint configuration | Dimas | ~5 min |

## Verification Checklist

### Pre-Go-Live (Friday/Weekend)

- [ ] `erp.kartoza.com` resolves to correct IP
- [ ] `kartoza.do.kartoza.com` resolves to deployment server
- [ ] Frappe confirms dual-domain registration
- [ ] Google Analytics integration tested in staging
- [ ] Sales pipeline integration tested in staging

### Go-Live (Monday)

- [ ] Hugo site accessible at `kartoza.com`
- [ ] ERPNext accessible at `erp.kartoza.com`
- [ ] APISIX routing correctly to ERPNext API
- [ ] Training course purchases functional
- [ ] Timesheets API responding correctly
- [ ] Google Analytics receiving data
- [ ] Sales pipeline forms functional

### Post-Go-Live (Tuesday)

- [ ] Monitor error rates in all systems
- [ ] Verify Analytics data collection
- [ ] Confirm all integrations operational
- [ ] User acceptance testing complete

## Risk Assessment

```mermaid
quadrantChart
    title Risk Assessment Matrix
    x-axis Low Impact --> High Impact
    y-axis Low Likelihood --> High Likelihood
    quadrant-1 Monitor Closely
    quadrant-2 Critical - Mitigate
    quadrant-3 Accept
    quadrant-4 Plan Response

    DNS Propagation Delays: [0.7, 0.5]
    Frappe DNS Update Delayed: [0.75, 0.5]
    APISIX Misconfiguration: [0.8, 0.3]
    Analytics Data Loss: [0.2, 0.3]
    Training Purchase Failures: [0.6, 0.5]
```

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| DNS propagation delays | Medium | High | Early DNS changes, low TTL values |
| Frappe DNS update delayed | Medium | High | Dual-domain request allows fallback |
| APISIX misconfiguration | Low | High | Staged rollout, immediate rollback capability |
| Analytics data loss | Low | Low | Verify tracking before go-live |
| Training purchase failures | Medium | Medium | Manual order processing backup |

## Communication Plan

| Stakeholder | Notification | Timing |
|-------------|--------------|--------|
| Internal Staff | Email: Migration timeline and expected changes | Thursday |
| External Users | Website banner: Brief maintenance window | Sunday |
| Support Team | Detailed rollback procedures | Friday |

## Contact Information

| Role | Name | Responsibility |
|------|------|----------------|
| DNS/Infrastructure | Tharanath | DNS records, Hugo deployment |
| Frappe Liaison | Marike | ERPNext domain configuration |
| API Gateway | Moloko | APISIX configuration, training integration |
| Frontend/Analytics | Tim | Hugo site, Google Analytics, sales pipeline |
| Timesheets | Dimas | Timesheet API updates |

---

*Document Version: 1.0*
*Last Updated: 2026-02-27*
*Next Review: Post-migration retrospective*
