package com.example.market_service.controller;

import com.example.market_service.dto.request.GoogleUserCreationRequest;
import com.example.market_service.dto.request.UserCreationRequest;
import com.example.market_service.dto.response.ApiResponse;
import com.example.market_service.dto.response.UserResponse;
import com.example.market_service.service.UserService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/users")
@Slf4j
public class UserController {
	private final UserService userService;
	@PostMapping("/google")
	public ApiResponse<UserResponse> createUser(@RequestBody GoogleUserCreationRequest request) {
		return ApiResponse.<UserResponse>builder()
				.message("User created successfully")
				.data(userService.createGoogleUser(request))
				.build();
	}
	@PostMapping
	public ApiResponse<UserResponse> createUserRegular(@RequestBody UserCreationRequest request) {
		return ApiResponse.<UserResponse>builder()
				.message("User created successfully")
				.data(userService.createUser(request))
				.build();
	}
	@PutMapping("/upgrade-vip")
	public ApiResponse<UserResponse> upgradeToVip () {
		Long userId = Long.parseLong(SecurityContextHolder.getContext().getAuthentication().getName());
		return ApiResponse.<UserResponse>builder()
				.message("User upgraded to VIP successfully")
				.data(userService.upToVip(userId))
				.build();

	}
}
