package com.example.payment_service.dto.event;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class VipUpgradeEvent {
	private Long userId;
	private Long vipPackageId;
	private String vipPackageName;
	private Long durationDays;
	private Long paymentId;
	private String orderId;
	private Instant timestamp;
}