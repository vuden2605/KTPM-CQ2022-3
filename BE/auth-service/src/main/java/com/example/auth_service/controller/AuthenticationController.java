package com.example.auth_service.controller;

import com.example.auth_service.dto.request.GoogleLoginRequest;
import com.example.auth_service.dto.request.LoginRequest;
import com.example.auth_service.dto.request.LogoutRequest;
import com.example.auth_service.dto.request.RefreshTokenRequest;
import com.example.auth_service.dto.response.ApiResponse;
import com.example.auth_service.dto.response.AuthenticationResponse;
import com.example.auth_service.service.AuthenticationService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/auth")
public class AuthenticationController {
	private final AuthenticationService authenticationService;
	@PostMapping("/login")
	public ApiResponse<AuthenticationResponse> login(@RequestBody LoginRequest request) {
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
	public ApiResponse<AuthenticationResponse> refreshToken(@RequestBody RefreshTokenRequest refreshToken) {
		return ApiResponse.<AuthenticationResponse>builder()
				.message("Token refreshed successfully")
				.data(authenticationService.refreshToken(refreshToken))
				.build();
	}
	@PostMapping("/logout")
	public ApiResponse<Void> logout(@RequestBody LogoutRequest request) {
		authenticationService.logout(request);
		return ApiResponse.<Void>builder()
				.message("Logout successful")
				.build();
	}
}
