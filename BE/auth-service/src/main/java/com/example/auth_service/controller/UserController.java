package com.example.auth_service.controller;

import com.example.auth_service.dto.request.GoogleUserCreationRequest;
import com.example.auth_service.dto.request.UserCreationRequest;
import com.example.auth_service.dto.response.ApiResponse;
import com.example.auth_service.dto.response.UserResponse;
import com.example.auth_service.service.UserService.IUserService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequiredArgsConstructor
@RequestMapping("/users")
@Slf4j
public class UserController {
	private final IUserService userServiceImpl;

	@PostMapping("/google")
	public ApiResponse<UserResponse> createUser(@RequestBody GoogleUserCreationRequest request) {
		return ApiResponse.<UserResponse>builder()
				.message("User created successfully")
				.data(userServiceImpl.createGoogleUser(request))
				.build();
	}

	@PostMapping
	public ApiResponse<UserResponse> createUserRegular(@RequestBody UserCreationRequest request) {
		return ApiResponse.<UserResponse>builder()
				.message("User created successfully")
				.data(userServiceImpl.createUser(request))
				.build();
	}

	@PutMapping("/upgrade-vip")
	public ApiResponse<UserResponse> upgradeToVip() {
		Long userId = Long.parseLong(SecurityContextHolder.getContext().getAuthentication().getName());
		return ApiResponse.<UserResponse>builder()
				.message("User upgraded to VIP successfully")
				.data(userServiceImpl.upToVip(userId))
				.build();

	}

	@GetMapping("/my-profile")
	public ApiResponse<UserResponse> getMyProfile() {
		Long userId = Long.parseLong(SecurityContextHolder.getContext().getAuthentication().getName());
		return ApiResponse.<UserResponse>builder()
				.message("User profile retrieved successfully")
				.data(userServiceImpl.getUserProfile(userId))
				.build();
	}

	@GetMapping
	@PreAuthorize("hasRole('ADMIN')")
	public ApiResponse<List<UserResponse>> getAllUsers() {
		return ApiResponse.<List<UserResponse>>builder()
				.message("List of users")
				.data(userServiceImpl.getAllUsers())
				.build();
	}

	@PutMapping("/{userId}/vip-toggle")
	@PreAuthorize("hasRole('ADMIN')")
	public ApiResponse<UserResponse> toggleVip(@PathVariable Long userId) {
		return ApiResponse.<UserResponse>builder()
				.message("User VIP status toggled")
				.data(userServiceImpl.toggleVip(userId))
				.build();
	}
}
