# LLM Skill: Prompt Engineering

## Purpose
Write effective prompts for RedForge security tasks.

## Basic Structure

### Prompt Components
```
Role:       Who the AI should be
Task:       What to do
Context:    Background information
Format:     How to respond
Constraints: Limitations or rules
```

## Role Definition

### Security Specialist
```markdown
You are an expert penetration tester specializing in web application security.
You have 10+ years of experience in bug bounty hunting.
```

### CTF Expert
```markdown
You are a CTF champion with expertise in:
- Binary exploitation
- Web vulnerabilities
- Cryptography
- Forensics
```

## Task Framing

### General Task
```
Analyze this URL for vulnerabilities:
https://example.com/page?id=1
```

### Detailed Task
```
As a web security expert, analyze https://example.com/page?id=1 for:
1. SQL injection (test ' OR 1=1--)
2. XSS (test <script>alert(1)</script>)
3. IDOR (test changing ID parameters)
Report findings in structured format.
```

## Security-Specific Prompts

### Reconnaissance
```markdown
Perform passive reconnaissance on example.com:
1. Identify subdomains using public sources
2. Check for information disclosure
3. Look for exposed APIs
4. Identify technologies via Wappalyzer

Use ONLY passive techniques (no active scanning).
```

### Vulnerability Analysis
```markdown
Analyze this HTTP response for security issues:

Request:
GET /admin HTTP/1.1
Host: target.com

Response:
HTTP/1.1 200 OK
Server: Apache/2.4.1

Identify:
- Missing security headers
- Information disclosure
- Authentication issues
```

### Exploitation
```markdown
Given this SQL injection vulnerability:
URL: https://target.com/product?id=1' OR 1=1--

1. Explain the vulnerability
2. Provide safe exploitation steps
3. Show how to enumerate database
4. Suggest remediation

Format: Step-by-step guide with code examples.
```

## Context Management

### Include Relevant Context
```markdown
Context:
- Target: example.com (in-scope for bug bounty)
- Authorization: Active testing permitted
- Tools available: nmap, ffuf, sqlmap, burp

Task: Find subdomains and test for takeover vulnerabilities.
```

### Exclude Irrelevant Context
```markdown
Context:
- Only test in-scope domains
- Do NOT test *.staging.example.com
- No social engineering allowed

Task: [Clear vulnerability research task]
```

## Output Formatting

### Structured Output
```markdown
Format your response as:

## Finding
[One-line summary]

## Severity
[Critical/High/Medium/Low/Info]

## Description
[Detailed explanation]

## Reproduction Steps
1. [Step 1]
2. [Step 2]

## Impact
[Business/security impact]

## Remediation
[Suggested fix]
```

### List Format
```markdown
List all findings in this format:
- **[SEVERITY]** Title: Description
```

## Constraints

### Scope Constraints
```
Constraints:
- Only test example.com and subdomains
- No denial of service testing
- Respect rate limits (10 req/sec max)
- No client-side only attacks
```

### Safety Constraints
```
Constraints:
- Do not execute malicious code
- Report only, do not exploit further
- Suggest safe testing methodologies
- Prioritize non-destructive techniques
```

## Chain of Thought

### Thinking Step by Step
```markdown
Think through this vulnerability step by step:

1. What type of vulnerability is this?
2. What are the attack vectors?
3. What data could be accessed?
4. What is the business impact?
5. How would you safely demonstrate this?

Then provide your analysis.
```

## Few-Shot Examples

### SQL Injection Analysis
```markdown
Example:
Input: ' OR '1'='1
Analysis: This attempts to bypass authentication
         by making the WHERE clause always true.
Response format:
- Vulnerability type
- Risk level
- Mitigation
```

### XSS Detection
```markdown
Example:
Input: <img src=x onerror=alert(1)>
Analysis: This is stored XSS using event handler
Response format:
- Vulnerability type
- Risk level  
- Mitigation
```

## RedForge Prompts

### Mode-Specific

#### Bug Bounty
```markdown
You are a bug bounty hunter targeting [SCOPE].
Follow the OWASP Top 10 methodology.
Report findings with PoC and remediation.
```

#### CTF
```markdown
You are solving a CTF challenge.
Think creatively about non-standard solutions.
Provide clear step-by-step exploitation.
```

#### Learning
```markdown
You are teaching security concepts.
Explain with examples and exercises.
Adapt to the user's skill level.
```

## Tips
```
1. Be specific about constraints
2. Define output format clearly
3. Include relevant context
4. Use examples when helpful
5. Break complex tasks into steps
6. Set role and tone appropriately
```
