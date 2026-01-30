package com.example.market_service.controller;

import com.example.market_service.dto.request.GoogleUserCreationRequest;
import com.example.market_service.dto.request.UserCreationRequest;
import com.example.market_service.dto.response.ApiResponse;
import com.example.market_service.dto.response.UserResponse;
import com.example.market_service.service.UserService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import java.util.List;

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
	public ApiResponse<UserResponse> upgradeToVip() {
		Long userId = Long.parseLong(SecurityContextHolder.getContext().getAuthentication().getName());
		return ApiResponse.<UserResponse>builder()
				.message("User upgraded to VIP successfully")
				.data(userService.upToVip(userId))
				.build();

	}

	@GetMapping
	@PreAuthorize("hasRole('ADMIN')")
	public ApiResponse<List<UserResponse>> getAllUsers() {
		return ApiResponse.<List<UserResponse>>builder()
				.message("List of users")
				.data(userService.getAllUsers())
				.build();
	}

	@PutMapping("/{userId}/vip-toggle")
	@PreAuthorize("hasRole('ADMIN')")
	public ApiResponse<UserResponse> toggleVip(@PathVariable Long userId) {
		return ApiResponse.<UserResponse>builder()
				.message("User VIP status toggled")
				.data(userService.toggleVip(userId))
				.build();
	}
}
