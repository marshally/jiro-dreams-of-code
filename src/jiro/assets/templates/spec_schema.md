# Feature Specification Schema

This document defines the format for feature specifications produced by the dreaming agent.

## Schema Definition

Every spec MUST contain the following sections:

### 1. Title

A clear, concise title for the feature.

```
# Feature: <Title>
```

### 2. Overview

1-2 paragraphs explaining what the feature does and why it matters. Focus on user value and business impact.

```
## Overview

<1-2 paragraphs describing the feature>
```

### 3. Requirements

Bullet list of functional requirements. Each requirement should be specific and testable.

```
## Requirements

- Requirement 1
- Requirement 2
- Requirement 3
```

### 4. Acceptance Criteria

Checkbox list of criteria that must be met for the feature to be considered complete.

```
## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
```

### 5. Out of Scope

Bullet list of things explicitly NOT included in this feature. Helps prevent scope creep.

```
## Out of Scope

- Item 1
- Item 2
```

### 6. Technical Notes

Optional section for implementation hints, architecture decisions, or technical constraints.

```
## Technical Notes

<Technical details, constraints, or recommendations>
```

## Example Specification

```markdown
# Feature: User Authentication

## Overview

Implement JWT-based authentication to secure API endpoints. Users will be able to register, login, and access protected resources using bearer tokens.

This feature is critical for the v1.0 launch as it enables user-specific functionality and data privacy.

## Requirements

- Users can register with email and password
- Users can login and receive a JWT token
- Protected endpoints validate JWT tokens
- Tokens expire after 24 hours
- Password reset via email is supported

## Acceptance Criteria

- [ ] Registration endpoint returns 201 on success
- [ ] Login endpoint returns JWT token on valid credentials
- [ ] Protected endpoints return 401 without valid token
- [ ] Token refresh works before expiration
- [ ] Password reset sends email and allows new password

## Out of Scope

- Social login (OAuth)
- Multi-factor authentication
- Session management
- Role-based access control

## Technical Notes

Use bcrypt for password hashing with cost factor 12. JWT should use RS256 algorithm with rotating keys stored in environment variables. Consider rate limiting login attempts to prevent brute force attacks.
```

## Validation Rules

A valid spec:

1. MUST have all required sections
1. MUST have at least 3 requirements
1. MUST have at least 3 acceptance criteria
1. SHOULD have at least 1 out of scope item
1. MAY omit Technical Notes if not needed
