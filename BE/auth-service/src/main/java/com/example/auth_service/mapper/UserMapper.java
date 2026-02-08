package com.example.auth_service.mapper;

import com.example.auth_service.dto.request.GoogleUserCreationRequest;
import com.example.auth_service.dto.request.UserCreationRequest;
import com.example.auth_service.dto.response.UserResponse;
import com.example.auth_service.entity.User;
import org.mapstruct.Mapper;

@Mapper(componentModel = "spring")
public interface UserMapper {
	User toEntity(GoogleUserCreationRequest request);
	User toEntity(UserCreationRequest request);
	UserResponse toResponse(User user);
}
