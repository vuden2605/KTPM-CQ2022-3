package com.example.payment_service.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;

import java.time.Instant;

@Entity
@Table(name = "payments")
@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class Payment {
	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private Long id;

	@Column(name = "user_id", nullable = false)
	private Long userId;

	@Column(name = "vip_package_id", nullable = false)
	private Long vipPackageId;

	@Column(name = "order_id", nullable = false, unique = true)
	private String orderId;

	@Column(name = "payment_provider")
	private String paymentProvider;

	@Column(name = "amount", nullable = false)
	private Long amount;

	@Column(name = "payment_status")
	private String paymentStatus; // PENDING, SUCCESS, FAILED

	@CreationTimestamp
	@Column(name = "created_at", nullable = false, updatable = false)
	private Instant createdAt;
}