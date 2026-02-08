package com.example.auth_service.service.UserService;

import com.example.auth_service.dto.request.GoogleUserCreationRequest;
import com.example.auth_service.dto.request.UserCreationRequest;
import com.example.auth_service.dto.response.UserResponse;

import java.util.List;

public interface IUserService {
	public UserResponse createGoogleUser(GoogleUserCreationRequest request);

	public UserResponse createUser(UserCreationRequest request);

	public UserResponse upToVip(Long userId);

	public UserResponse getUserProfile(Long userId);

	public List<UserResponse> getAllUsers();

	public UserResponse toggleVip(Long userId);
}
