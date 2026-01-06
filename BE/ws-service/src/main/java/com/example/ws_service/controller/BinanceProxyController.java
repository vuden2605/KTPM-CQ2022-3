package com.example.ws_service.controller;

import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.http.client.ClientHttpResponse;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.RequestCallback;
import org.springframework.web.client.ResponseExtractor;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;

@RestController
@RequestMapping("/proxy")
@Slf4j
public class BinanceProxyController {

    private final RestTemplate restTemplate = new RestTemplate();

    @CrossOrigin(origins = "*")
    @GetMapping("/klines")
    public ResponseEntity<String> klines(
            @RequestParam("symbol") String symbol,
            @RequestParam("interval") String interval,
            @RequestParam(value = "limit", required = false) Integer limit
    ) {
        String url = String.format("https://api.binance.com/api/v3/klines?symbol=%s&interval=%s", symbol, interval);
        if (limit != null) url += "&limit=" + limit;

        try {
            ResponseEntity<String> resp = restTemplate.exchange(url, HttpMethod.GET, null, String.class);
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            return new ResponseEntity<>(resp.getBody(), headers, resp.getStatusCode());
        } catch (HttpStatusCodeException hsce) {
            // forward Binance error status and body for debugging
            log.warn("Binance returned error: {} {}", hsce.getStatusCode(), hsce.getResponseBodyAsString());
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            return new ResponseEntity<>(hsce.getResponseBodyAsString(), headers, hsce.getStatusCode());
        } catch (Exception e) {
            log.error("Binance proxy unexpected error", e);
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            return new ResponseEntity<>("[]", headers, HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
}
