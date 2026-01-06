package com.example.auth_service.configure;

import com.example.auth_service.service.JwtService;
import io.jsonwebtoken.Claims;
import lombok.RequiredArgsConstructor;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.oauth2.jwt.JwtDecoder;
import org.springframework.security.oauth2.jwt.JwtException;
import org.springframework.stereotype.Component;

import java.util.Collections;

@Component
@RequiredArgsConstructor
public class CustomJwtDecoder implements JwtDecoder {
	private final JwtService jwtService;

	@Override
	public Jwt decode(String token) throws JwtException {
		Claims claims = jwtService.verifyToken(token);
		if(claims.get("type") == null || !claims.get("type").equals("access_token")) {
			throw new JwtException("Invalid token");
		}
		return new Jwt(
				token,
				claims.getIssuedAt().toInstant(),
				claims.getExpiration().toInstant(),
				Collections.singletonMap("alg", "HS256"),
				claims
		);
	}
}
