# Git Branching Strategy & Webhooks

## Branch Model
- **main**: Production environment.
- **develop**: Staging environment.
- **feature/***: New features.
- **hotfix/***: Emergency fixes.

## GitHub Branch Protection
- **main**: Require 2 PR reviews, CI passing, no force-push.

## Webhook Config
- **Payload URL**: `http://JENKINS_IP:8080/github-webhook/`
- **Events**: Push, Pull Request

## Jenkins Multibranch Pipeline
- **feature/*** -> Tests only.
- **develop** -> Deploy to staging namespace.
- **main** -> Deploy to production (manual approval required).
