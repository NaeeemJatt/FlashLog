# TODO: Remaining Security and Feature Enhancements for FlashLog

## High Priority
- [ ] Implement secure password reset (forgot password) with email verification
- [ ] Add two-factor authentication (2FA) for admin accounts
- [ ] Regenerate session on privilege change (e.g., after login, password change)
- [ ] Enhance input validation and sanitization across all forms and file uploads
- [ ] Add comprehensive security event logging and monitoring
- [ ] Add virus/malware scanning for uploaded files

## Medium Priority
- [ ] Implement database connection pooling and review for prepared statement usage
- [ ] Add concurrent session control (limit number of active sessions per user)
- [ ] Invalidate all sessions on password change
- [ ] Add audit trail for admin/user actions (compliance)
- [ ] Add API-specific rate limiting
- [ ] Add user notification for account lockout and suspicious activity

## Low Priority
- [ ] Add user profile picture upload with security checks
- [ ] Add user self-service account deletion (with verification)
- [ ] Add admin dashboard for security analytics and audit logs
- [ ] Add accessibility and usability improvements
- [ ] Add more unit and integration tests for security features

---

**Next Steps:**
- Prioritize password reset and 2FA implementation
- Review and enhance all input validation
- Plan for security logging and monitoring
- Review this list before starting tomorrow 