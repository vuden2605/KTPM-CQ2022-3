package com.example.auth_service.controller;

import com.example.auth_service.dto.request.GoogleLoginRequest;
import com.example.auth_service.dto.request.IntrospectRequest;
import com.example.auth_service.dto.request.LoginRequest;
import com.example.auth_service.dto.request.LogoutRequest;
import com.example.auth_service.dto.request.RefreshTokenRequest;
import com.example.auth_service.dto.response.ApiResponse;
import com.example.auth_service.dto.response.AuthenticationResponse;
import com.example.auth_service.dto.response.IntrospectResponse;
import com.example.auth_service.service.AuthenticationService.IAuthenticationService;
import com.example.auth_service.service.AuthenticationService.IAuthenticationService;
import com.example.auth_service.service.JwtService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

@RestController
@RequiredArgsConstructor
@RequestMapping("/auth")
@Slf4j
public class AuthenticationController {
	private final IAuthenticationService authenticationService;
	private final JwtService jwtService;

	@PostMapping("/login")
	public ApiResponse<AuthenticationResponse> login(@RequestBody @Valid LoginRequest request) {
		log.info("Login attempt for user: {}", request.getUserName());
		return ApiResponse.<AuthenticationResponse>builder()
				.message("Login successful")
				.data(authenticationService.login(request))
				.build();
	}

	@PostMapping("/login/google")
	public ApiResponse<AuthenticationResponse> loginWithGoogle(@RequestBody GoogleLoginRequest request) {
		return ApiResponse.<AuthenticationResponse>builder()
				.message("Login with Google successful")
				.data(authenticationService.loginWithGoogle(request))
				.build();
	}

	@PostMapping("/refresh-token")
	public ApiResponse<AuthenticationResponse> refreshToken(@RequestBody RefreshTokenRequest request) {
		return ApiResponse.<AuthenticationResponse>builder()
				.message("Token refreshed successfully")
				.data(authenticationService.refreshToken(request))
				.build();
	}

	@PostMapping("/logout")
	public ApiResponse<Void> logout(@RequestBody LogoutRequest request) {
		authenticationService.logout(request);
		return ApiResponse.<Void>builder()
				.message("Logout successful")
				.build();
	}

	@PostMapping("/introspect")
	public ApiResponse<IntrospectResponse> introspectToken(@RequestBody IntrospectRequest request) {
		return ApiResponse.<IntrospectResponse>builder()
				.message("Token introspection successful")
				.data(jwtService.introspectToken(request))
				.build();
	}
}