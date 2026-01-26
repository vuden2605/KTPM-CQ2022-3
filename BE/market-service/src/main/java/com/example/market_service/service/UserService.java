package com.example.market_service.service;

import com.example.market_service.Exception.AppException;
import com.example.market_service.Exception.ErrorCode;
import com.example.market_service.Mapper.UserMapper;
import com.example.market_service.dto.request.GoogleUserCreationRequest;
import com.example.market_service.dto.request.UserCreationRequest;
import com.example.market_service.dto.response.UserResponse;
import com.example.market_service.entity.User;
import com.example.market_service.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

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

}
