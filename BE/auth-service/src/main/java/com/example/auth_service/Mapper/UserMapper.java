package com.example.auth_service.Mapper;

import com.example.auth_service.dto.request.UserCreationRequest;
import com.example.auth_service.dto.response.UserResponse;
import com.example.auth_service.entity.User;
import org.mapstruct.Mapper;

@Mapper(componentModel = "spring")
public interface UserMapper {
	User toEntity(UserCreationRequest request);
	UserResponse toResponse(User user);
}
