package com.example.market_service.service;

import com.example.market_service.Exception.AppException;
import com.example.market_service.Exception.ErrorCode;
import com.example.market_service.Mapper.UserMapper;
import com.example.market_service.dto.request.GoogleUserCreationRequest;
import com.example.market_service.dto.request.UserCreationRequest;
import com.example.market_service.dto.response.UserResponse;
import com.example.market_service.entity.User;
import com.example.market_service.enums.Role;
import com.example.market_service.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
@RequiredArgsConstructor
public class UserService {
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
		} else if (user.getRole() == Role.USER) {
			user.setRole(Role.VIP);
		}
		// If ADMIN, ignore or toggle? Let's assume we don't toggle ADMIN.

		return userMapper.toResponse(userRepository.save(user));
	}
}
