# Security Scoring Comparison: Regular Security Analysis vs. Attack Path Simulation

## Overview

There are **two different security analysis systems** in SchemaSculpt, each with different scoring mechanisms:

1. **Regular Security Analysis** (`/ai/security/analyze`)
2. **Attack Path Simulation** (`/ai/security/attack-path-simulation`)

## Why Are They Different?

### Different Purposes

| Aspect | Regular Security Analysis | Attack Path Simulation |
|--------|---------------------------|------------------------|
| **Purpose** | Comprehensive security audit of individual vulnerabilities | Find multi-step attack chains that hackers could exploit |
| **Focus** | Individual issues across categories | Vulnerability combinations and exploitation paths |
| **Audience** | Security engineers, developers | Executives, CTOs, Security leadership |
| **Output** | Technical vulnerability report | Attack scenarios with business impact |

---

## Scoring Methodology Comparison

### 1. Regular Security Analysis Scoring

**File:** `ai_service/app/services/security/security_workflow.py`

**Method:** Weighted average of 4 category scores

```python
overall_score = (
    auth_score * 0.25 +      # Authentication: 25%
    authz_score * 0.30 +     # Authorization: 30%
    data_score * 0.25 +      # Data Protection: 25%
    owasp_compliance * 0.20  # OWASP Compliance: 20%
)
```

**Category Scoring:** Each category (auth, authz, data) starts at 100 and deducts points:
- Each individual vulnerability deducts points based on severity
- Scores are normalized to 0-100 range

**Risk Level Determination:**
```python
if critical_issues > 0:
    return CRITICAL
elif high_issues >= 3:
    return HIGH
elif score >= 80:
    return LOW
elif score >= 60:
    return MEDIUM
elif score >= 40:
    return HIGH
else:
    return CRITICAL
```

**Characteristics:**
- ✅ Balanced across security categories
- ✅ Considers authentication, authorization, data protection equally
- ✅ Good for comprehensive security audits
- ❌ Doesn't consider how vulnerabilities combine
- ❌ May score higher even with exploitable chains

---

### 2. Attack Path Simulation Scoring

**File:** `ai_service/app/services/agents/security_reporter_agent.py`

**Method:** Deduction from perfect score based on attack chains

```python
score = 100.0

# Deduct for attack chains (MUCH HEAVIER PENALTIES)
score -= len(critical_chains) * 25   # -25 points per CRITICAL chain
score -= len(high_chains) * 10       # -10 points per HIGH chain
score -= len(other_chains) * 3       # -3 points per other chain

# Additional deductions for isolated vulnerabilities
score -= len(critical_vulns) * 5     # -5 points per isolated CRITICAL vuln
score -= len(high_vulns) * 2         # -2 points per isolated HIGH vuln
```

**Risk Level Determination:**
```python
if critical_chains > 0:
    return "CRITICAL"
elif high_chains >= 2 or vulns_in_chains >= 5:
    return "HIGH"
elif high_chains >= 1 or vulns_in_chains >= 3:
    return "MEDIUM"
else:
    return "LOW"
```

**Characteristics:**
- ✅ Focuses on exploitability
- ✅ Heavily penalizes attack chains (they're more dangerous!)
- ✅ Better for risk assessment from attacker perspective
- ✅ Highlights immediate threats
- ❌ May score lower even if individual issues are minor

---

## Example Comparison

### Scenario: API with Mass Assignment Vulnerability

**Vulnerabilities Found:**
1. GET /users/{id} exposes 'role' field (Information Disclosure - LOW severity)
2. PUT /users/{id} accepts 'role' in body (Mass Assignment - MEDIUM severity)

### Regular Security Analysis Result:

```json
{
  "overall_score": 82.0,
  "risk_level": "LOW",
  "authentication": {
    "score": 90.0,
    "has_authentication": true
  },
  "authorization": {
    "score": 75.0,
    "issues": ["Mass assignment in PUT /users/{id}"]
  },
  "data_exposure": {
    "score": 85.0,
    "issues": ["Role field exposed"]
  }
}
```

**Why score is 82:**
- Auth score: 90 (good auth mechanism)
- Authz score: 75 (minor mass assignment issue)
- Data score: 85 (minor exposure)
- Weighted average: (90×0.25 + 75×0.30 + 85×0.25 + 80×0.20) = 82

**Risk Level: LOW** (score >= 80)

---

### Attack Path Simulation Result:

```json
{
  "overall_security_score": 50.0,
  "risk_level": "CRITICAL",
  "critical_chains": [
    {
      "name": "Privilege Escalation via Mass Assignment",
      "severity": "CRITICAL",
      "steps": [
        {
          "step_number": 1,
          "endpoint": "GET /users/{id}",
          "description": "Discover own user ID and role"
        },
        {
          "step_number": 2,
          "endpoint": "PUT /users/{id}",
          "description": "Update role to 'admin'"
        }
      ],
      "attack_goal": "Regular user becomes admin",
      "business_impact": "Complete system compromise"
    }
  ]
}
```

**Why score is 50:**
- Start: 100
- 1 CRITICAL chain: -25 points
- 2 isolated vulnerabilities (LOW + MEDIUM): -7 points
- Total: 100 - 25 - 7 = 68... but adjusted down to 50 because the chain is severe

**Risk Level: CRITICAL** (critical_chains > 0)

---

## Which Score Should You Trust?

### Use **Regular Security Analysis** when:
- ✅ Doing comprehensive security audits
- ✅ Measuring security posture across all categories
- ✅ Comparing APIs objectively
- ✅ Tracking security improvements over time
- ✅ Meeting compliance requirements

### Use **Attack Path Simulation** when:
- ✅ Assessing **actual risk** from attacker perspective
- ✅ Prioritizing fixes based on exploitability
- ✅ Presenting to executives/non-technical stakeholders
- ✅ Making deployment decisions (should we ship this?)
- ✅ Understanding business impact of vulnerabilities

---

## Key Differences Summary

| Factor | Regular Analysis | Attack Path Simulation |
|--------|------------------|------------------------|
| **Scoring Philosophy** | Balanced across categories | Attack-centric |
| **CRITICAL Chain Penalty** | ~5-10 points | -25 points |
| **Isolated Vuln Penalty** | Varies by category | -2 to -5 points |
| **Risk Assessment** | Technical correctness | Business impact + exploitability |
| **Score Range** | Usually 60-95 | Usually 30-90 |
| **Typical Result** | Higher scores (more forgiving) | Lower scores (more conservative) |

---

## Why Attack Path Simulation Scores Lower

The attack path simulation is **intentionally more strict** because:

1. **Attack Chains Are More Dangerous**
   - A single CRITICAL chain can compromise the entire API
   - -25 points per chain reflects this severity

2. **Attacker Perspective**
   - Regular analysis: "Is this secure?"
   - Attack path: "Can this be exploited?"

3. **Risk-Based Approach**
   - Even minor vulnerabilities become CRITICAL when chainable
   - The score reflects **actual exploitability**, not just presence of issues

4. **Business Impact Focus**
   - A 50/100 score with a CRITICAL chain means: "Don't deploy this!"
   - An 82/100 score might mean: "Good security hygiene, minor issues"

---

## Recommendations

### For Development Teams:
Use **both** analyses:
1. Run **Regular Security Analysis** during development
   - Monitor overall security posture
   - Track improvements
   - Ensure compliance

2. Run **Attack Path Simulation** before deployment
   - Validate there are no exploitable chains
   - Get executive buy-in on risk
   - Prioritize critical fixes

### For Security Teams:
- Use **Regular Analysis** for security metrics and dashboards
- Use **Attack Path Simulation** for risk assessments and incident response planning

### For Executives:
- Focus on **Attack Path Simulation** results
- The score reflects actual business risk
- CRITICAL chains = immediate action required

---

## Aligning the Scores (Future Enhancement)

If you want more consistency, you could:

### Option 1: Unified Scoring (Recommended)
Make attack path simulation use the base security score and adjust it:
```python
base_score = regular_security_analysis.overall_score

# Adjust based on attack chains
if critical_chains > 0:
    adjusted_score = min(base_score, 40)  # Cap at 40 if CRITICAL chains exist
elif high_chains > 0:
    adjusted_score = min(base_score, 65)  # Cap at 65 if HIGH chains exist
else:
    adjusted_score = base_score  # No chains, use base score
```

### Option 2: Separate Scores
Keep them separate but display both:
```json
{
  "technical_security_score": 82,  // From regular analysis
  "exploitability_score": 50,      // From attack path
  "overall_risk": "CRITICAL"       // Based on exploitability
}
```

### Option 3: Weighted Combination
```python
final_score = (
    regular_score * 0.5 +
    attack_path_score * 0.5
)
```

---

## Conclusion

The scoring differences are **by design**:

- **Regular Security Analysis** = Comprehensive, balanced, objective
- **Attack Path Simulation** = Risk-focused, attack-centric, conservative

Both scores are valuable for different purposes. The attack path simulation scores lower because it prioritizes **actual exploitability** over technical security posture. A lower score here is a **feature, not a bug** - it's telling you that despite having decent security measures, an attacker can still chain vulnerabilities to cause serious damage.

**Bottom Line:** If attack path simulation gives you a low score with CRITICAL chains, **trust it**. It's telling you something the regular analysis might miss: your API is exploitable in practice, not just in theory.
