package com.example.auth_service.service;

import com.example.auth_service.Exception.AppException;
import com.example.auth_service.Exception.ErrorCode;
import com.example.auth_service.Mapper.UserMapper;
import com.example.auth_service.dto.request.UserCreationRequest;
import com.example.auth_service.dto.response.UserResponse;
import com.example.auth_service.entity.User;
import com.example.auth_service.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class UserService {
	private final UserRepository userRepository;
	private final UserMapper userMapper;
	public UserResponse createUser(UserCreationRequest request) {
		if(userRepository.existsByUserName(request.getUserName())) {
			throw new AppException(ErrorCode.USERNAME_ALREADY_EXISTS);
		}
		User user = userMapper.toEntity(request);
		return userMapper.toResponse(userRepository.save(user));
	}
}
