package com.example.auth_service.configure;

import com.example.auth_service.entity.User;
import com.example.auth_service.enums.Role;
import com.example.auth_service.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class SeedDataRunner implements CommandLineRunner {
    private final UserRepository userRepository;

    @Override
    public void run(String... args) throws Exception {
        String seedUser = "testuser";
        if (userRepository.existsByUserName(seedUser)) {
            System.out.println("Seed user already exists: " + seedUser);
            return;
        }

        User u = User.builder()
                .email("testuser@example.com")
                .userName(seedUser)
                .password("password123")
                .role(Role.USER)
                .isActive(true)
                .build();

        userRepository.save(u);
        System.out.println("Seeded user: " + seedUser + " / password123");
    }
}
