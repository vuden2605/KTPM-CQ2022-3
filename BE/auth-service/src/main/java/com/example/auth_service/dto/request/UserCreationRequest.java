package com.example.auth_service.dto.request;

import lombok.*;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class UserCreationRequest {
	private String email;

	private String userName;

	private String password;
}
