package com.example.auth_service.service;

import com.example.auth_service.entity.User;
import com.example.auth_service.enums.Role;
import com.example.auth_service.exception.AppException;
import com.example.auth_service.exception.ErrorCode;
import com.example.auth_service.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;

@Service
@RequiredArgsConstructor
@Slf4j
public class VipService {
	private final UserRepository userRepository;

	@Transactional
	public void upgradeUserToVip(Long userId, Long durationDays, String packageName) {
		log.info("⬆️ Upgrading user {} to VIP with package: {} ({} days)",
				userId, packageName, durationDays);

		User user = userRepository.findById(userId)
				.orElseThrow(() -> new AppException(ErrorCode.USER_NOT_FOUND));

		LocalDateTime now = LocalDateTime.now();

		// ✅ Set role to VIP
		user.setRole(Role.VIP);

		// ✅ Calculate VIP period
		if (user.getVipEndAt() != null && user.getVipEndAt().isAfter(now)) {
			// User đã có VIP → Extend thêm
			log.info("   └─ Extending existing VIP from {} by {} days",
					user.getVipEndAt(), durationDays);
			user.setVipEndAt(user.getVipEndAt().plusDays(durationDays));
		} else {
			// User chưa có VIP hoặc đã hết hạn → Set mới
			log.info("   └─ Setting new VIP period: {} days", durationDays);
			user.setVipStartAt(now);
			user.setVipEndAt(now.plusDays(durationDays));
		}

		userRepository.save(user);

		log.info("✅ User {} upgraded to VIP successfully", userId);
		log.info("   └─ Role: {}", user.getRole());
		log.info("   └─ VIP Start: {}", user.getVipStartAt());
		log.info("   └─ VIP End: {}", user.getVipEndAt());
	}

	@Transactional
	public void checkAndDowngradeExpiredVip(Long userId) {
		User user = userRepository.findById(userId)
				.orElseThrow(() -> new AppException(ErrorCode.USER_NOT_FOUND));

		if (user.getVipEndAt() != null && user.getVipEndAt().isBefore(LocalDateTime.now())) {
			log.warn("⬇️ User {} VIP expired, downgrading to USER", userId);
			user.setRole(Role.USER);
			userRepository.save(user);
		}
	}
}