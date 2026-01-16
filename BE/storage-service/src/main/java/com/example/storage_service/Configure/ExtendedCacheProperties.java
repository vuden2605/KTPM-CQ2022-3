package com.example.storage_service.Configure;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

@Data
@Configuration
@ConfigurationProperties(prefix = "cache")
public class ExtendedCacheProperties {
	Map<String, Duration> expires = new HashMap<>();
}
