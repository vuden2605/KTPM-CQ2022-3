package com.example.auth_service.service;

import com.example.auth_service.dto.request.IntrospectRequest;
import com.example.auth_service.dto.response.IntrospectResponse;
import com.example.auth_service.entity.User;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.crypto.SecretKey;
import java.util.Date;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class JwtService {
	@Value("${jwt.secret}")
	private String secretKey;

	@Value("${jwt.access-time}")
	private long accessTime;

	@Value("${jwt.refresh-time}")
	private long refreshTime;

	private final TokenCacheService tokenCacheService;

	public SecretKey getSecretKey() {
		return Keys.hmacShaKeyFor(secretKey.getBytes());
	}

	public String generateAccessToken(User user) {
		String jti = UUID.randomUUID().toString();
		String rfId = UUID.randomUUID().toString();
		return Jwts.builder()
				.setId(jti)
				.setSubject(user.getId().toString())
				.claim("scope", user.getRole())
				.claim("name", user.getUserName())
				.claim("email", user.getEmail())
				.claim("rfId", rfId)
				.claim("type", "access_token")
				.setIssuedAt(new Date())
				.setExpiration(new Date(System.currentTimeMillis() + accessTime))
				.signWith(getSecretKey())
				.compact();
	}

	public String generateRefreshToken(User user) {
		String jti = UUID.randomUUID().toString();
		String acId = UUID.randomUUID().toString();
		return Jwts.builder()
				.setId(jti)
				.setSubject(user.getId().toString())
				.claim("scope", user.getRole())
				.claim("name", user.getUserName())
				.claim("email", user.getEmail())
				.claim("acId", acId)
				.claim("type", "refresh_token")
				.setIssuedAt(new Date())
				.setExpiration(new Date(System.currentTimeMillis() + refreshTime))
				.signWith(getSecretKey())
				.compact();
	}

	public Claims verifyToken(String token) {
		try {
			Claims claims = Jwts.parserBuilder()
					.setSigningKey(getSecretKey())
					.build()
					.parseClaimsJws(token)
					.getBody();
			String tokenId = claims.getId();
			if (tokenCacheService.isTokenInvalidated(tokenId)) {
				throw new JwtException("Token has been invalidated");
			}
			return claims;
		} catch (JwtException e) {
			throw new JwtException("Invalid or expired token", e);
		}
	}

	public IntrospectResponse introspectToken(IntrospectRequest request) {
		String token = request.getToken();
		try {
			Claims claims = verifyToken(token);
			return IntrospectResponse.builder()
					.isValid(true)
					.userId(claims.getSubject())
					.scope((String) claims.get("scope"))
					.build();
		} catch (JwtException e) {
			return IntrospectResponse.builder().isValid(false).build();
		}
	}
}