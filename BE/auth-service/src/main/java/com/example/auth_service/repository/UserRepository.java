package com.example.auth_service.repository;

import com.example.auth_service.entity.User;
import com.example.auth_service.enums.Role;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface UserRepository extends JpaRepository<User, Long> {
	Optional<User> findByUserName(String userName);
	Optional<User> findByEmail(String email);
	boolean existsByUserName(String userName);
	boolean existsByEmail(String email);
	List<User> findByRoleAndVipEndAtBefore(Role role, LocalDateTime dateTime);
}