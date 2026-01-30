package com.example.market_service.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.context.event.EventListener;
import org.springframework.security.authentication.event.AbstractAuthenticationFailureEvent;
import org.springframework.security.authentication.event.AuthenticationSuccessEvent;
import org.springframework.security.core.Authentication;
import org.springframework.security.web.authentication.WebAuthenticationDetails;
import org.springframework.stereotype.Component;

@Component
@Slf4j
public class SecurityAuditListener {

    private static final String AUDIT_PREFIX = "[SECURITY_AUDIT]";

    @EventListener
    public void onSuccess(AuthenticationSuccessEvent event) {
        Authentication auth = event.getAuthentication();
        String remoteIp = getRemoteIp(auth);
        String username = auth.getName();

        log.info("{} LOGIN_SUCCESS User:{} IP:{}", AUDIT_PREFIX, username, remoteIp);
    }

    @EventListener
    public void onFailure(AbstractAuthenticationFailureEvent event) {
        Authentication auth = event.getAuthentication();
        String remoteIp = getRemoteIp(auth);
        String username = (auth != null) ? auth.getName() : "Anonymous";
        String error = event.getException().getMessage();

        log.warn("{} LOGIN_FAILURE User:{} IP:{} Error:{}", AUDIT_PREFIX, username, remoteIp, error);
    }

    private String getRemoteIp(Authentication auth) {
        if (auth != null && auth.getDetails() instanceof WebAuthenticationDetails) {
            return ((WebAuthenticationDetails) auth.getDetails()).getRemoteAddress();
        }
        return "Unknown-IP";
    }
}
