package com.example.auth_service.dto.response;

import com.example.auth_service.enums.Role;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.time.LocalDateTime;
@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
@JsonInclude(JsonInclude.Include.NON_NULL)
public class UserResponse {

	private Long id;

	private String email;

	private String userName;

	private String password;

	private String avatarUrl;

	private String googleId;

	private Role role;

	private Boolean isActive;

	private LocalDateTime vipStartAt;

	private LocalDateTime vipEndAt;

	private Instant createdAt;

	private Instant updatedAt;

}
