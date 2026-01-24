package com.example.ws_service.websocket;

import lombok.extern.slf4j.Slf4j;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.messaging.SessionConnectedEvent;
import org.springframework.web.socket.messaging.SessionDisconnectEvent;

import java.util.concurrent.atomic.AtomicInteger;

@Component
@Slf4j
public class WebSocketEventListener {

    private static final AtomicInteger activeConnections = new AtomicInteger(0);

    @EventListener
    public void handleWebSocketConnectListener(SessionConnectedEvent event) {
        int current = activeConnections.incrementAndGet();
        // Reduce log noise: only log every 500th connection
        if (current % 10 == 0) {
            log.info("[LOAD-TEST] Active Users Reached: {} (Instance: {})", current, System.getenv("HOSTNAME"));
        }
    }

    @EventListener
    public void handleWebSocketDisconnectListener(SessionDisconnectEvent event) {
        activeConnections.decrementAndGet();
        // optional: log disconnects sparingly too
    }
}
