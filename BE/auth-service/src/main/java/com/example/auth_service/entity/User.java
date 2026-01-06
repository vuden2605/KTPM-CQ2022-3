package com.example.auth_service.entity;

import com.example.auth_service.enums.Role;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.Instant;
import java.time.LocalDateTime;

@Entity
@Table(name = "users")
@Builder
@Data
@AllArgsConstructor
@NoArgsConstructor
public class User {
	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private Long id;

	@Column(name = "email", nullable = false, unique = true, length = 255)
	private String email;

	@Column(name = "user_name", length = 255)
	private String userName;

	@Column(name = "password", length = 500)
	private String password;

	@Column(name = "avatar_url", length = 500)
	private String avatarUrl;

	@Column(name = "google_id", length = 500)
	private String googleId;

	@Enumerated(EnumType.STRING)
	@Builder.Default
	private Role role = Role.USER;

	@Builder.Default
	private Boolean isActive = true;

	@Column(name = "vip_start_at")
	private LocalDateTime vipStartAt;

	@Column(name = "vip_end_at")
	private LocalDateTime vipEndAt;

	@CreationTimestamp
	@Column(name = "created_at", nullable = false, updatable = false)
	private Instant createdAt;

	@UpdateTimestamp
	@Column(name = "updated_at")
	private Instant updatedAt;

}
