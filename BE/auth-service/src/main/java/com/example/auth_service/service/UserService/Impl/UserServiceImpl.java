package com.example.auth_service.service.UserService.Impl;

import com.example.auth_service.dto.request.GoogleUserCreationRequest;
import com.example.auth_service.dto.request.UserCreationRequest;
import com.example.auth_service.dto.response.UserResponse;
import com.example.auth_service.entity.User;
import com.example.auth_service.enums.Role;
import com.example.auth_service.exception.AppException;
import com.example.auth_service.exception.ErrorCode;
import com.example.auth_service.mapper.UserMapper;
import com.example.auth_service.repository.UserRepository;
import com.example.auth_service.service.UserService.IUserService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class UserServiceImpl implements IUserService {
	private final UserRepository userRepository;
	private final UserMapper userMapper;

	public UserResponse createGoogleUser(GoogleUserCreationRequest request) {
		if (userRepository.existsByUserName(request.getUserName())) {
			throw new AppException(ErrorCode.USERNAME_ALREADY_EXISTS);
		}
		User user = userMapper.toEntity(request);
		return userMapper.toResponse(userRepository.save(user));
	}

	public UserResponse createUser(UserCreationRequest request) {
		if (userRepository.existsByUserName(request.getUserName())) {
			throw new AppException(ErrorCode.USERNAME_ALREADY_EXISTS);
		}
		if (userRepository.existsByEmail(request.getEmail())) {
			throw new AppException(ErrorCode.EMAIL_ALREADY_EXISTS);
		}
		User user = userMapper.toEntity(request);
		return userMapper.toResponse(userRepository.save(user));
	}

	public UserResponse upToVip(Long userId) {
		User user = userRepository.findById(userId)
				.orElseThrow(() -> new AppException(ErrorCode.USER_NOT_FOUND));
		user.setRole(Role.VIP);
		return userMapper.toResponse(userRepository.save(user));
	}

	public UserResponse getUserProfile(Long userId) {
		return userRepository.findById(userId)
				.map(userMapper::toResponse)
				.orElseThrow(() -> new AppException(ErrorCode.USER_NOT_FOUND));
	}

	public List<UserResponse> getAllUsers() {
		return userRepository.findAll().stream()
				.map(userMapper::toResponse)
				.toList();
	}

	public UserResponse toggleVip(Long userId) {
		User user = userRepository.findById(userId)
				.orElseThrow(() -> new AppException(ErrorCode.USER_NOT_FOUND));

		if (user.getRole() == Role.VIP) {
			user.setRole(Role.USER);
			user.setVipEndAt(null);
			user.setVipStartAt(null);
		} else if (user.getRole() == Role.USER) {
			user.setRole(Role.VIP);
			// Manual toggle by Admin -> Unlimited (null expiration)
			user.setVipStartAt(java.time.LocalDateTime.now());
			user.setVipEndAt(null);
		}
		// If ADMIN, ignore or toggle? Let's assume we don't toggle ADMIN.

		return userMapper.toResponse(userRepository.save(user));
	}
}