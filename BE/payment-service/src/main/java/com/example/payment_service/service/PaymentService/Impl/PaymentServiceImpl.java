package com.example.payment_service.service.PaymentService.Impl;

import com.example.payment_service.dto.event.VipUpgradeEvent;
import com.example.payment_service.entity.Payment;
import com.example.payment_service.entity.VipPackage;
import com.example.payment_service.exception.AppException;
import com.example.payment_service.exception.ErrorCode;
import com.example.payment_service.repository.PaymentRepository;
import com.example.payment_service.repository.VipPackageRepository;
import com.example.payment_service.service.KafkaProducerService;
import com.example.payment_service.service.PaymentService.Factory.PaymentProviderFactory;
import com.example.payment_service.service.PaymentService.IPaymentService;
import com.example.payment_service.service.PaymentService.Provider.IPaymentProvider;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.Instant;

@Service
@RequiredArgsConstructor
@Slf4j
public class PaymentServiceImpl implements IPaymentService {
	private final VipPackageRepository vipPackageRepository;
	private final PaymentRepository paymentRepository;
	private final PaymentProviderFactory paymentProviderFactory;
	private final KafkaProducerService kafkaProducerService;  // ✅ Inject Kafka Producer

	@Override
	@Transactional
	public String createPayment(Long userId, Long vipPackageId, String method) {
		VipPackage vipPackage = vipPackageRepository.findById(vipPackageId)
				.orElseThrow(() -> new AppException(ErrorCode.VIP_PACKAGE_NOT_FOUND));

		String orderCode = "VIP-" + System.currentTimeMillis() + "-" + userId;

		Payment payment = Payment.builder()
				.userId(userId)
				.vipPackageId(vipPackage.getId())
				.paymentProvider(method)
				.amount(vipPackage.getPrice())
				.orderId(orderCode)
				.paymentStatus("PENDING")
				.build();

		paymentRepository.save(payment);
		log.info("💳 Payment created: orderId={}, userId={}, amount={}",
				orderCode, userId, vipPackage.getPrice());

		IPaymentProvider paymentProvider = paymentProviderFactory.getProvider(method);
		return paymentProvider.createPaymentUrl(payment);
	}

	@Override
	@Transactional
	public void finalizePayment(String responseCode, String orderInfo) {
		Payment payment = paymentRepository.findByOrderId(orderInfo)
				.orElseThrow(() -> new AppException(ErrorCode.PAYMENT_NOT_FOUND));

		if ("00".equals(responseCode)) {
			// ✅ Payment SUCCESS
			payment.setPaymentStatus("SUCCESS");
			paymentRepository.save(payment);

			log.info("✅ Payment SUCCESS: orderId={}, userId={}", payment.getOrderId(), payment.getUserId());


			VipPackage vipPackage = vipPackageRepository.findById(payment.getVipPackageId())
					.orElseThrow(() -> new AppException(ErrorCode.VIP_PACKAGE_NOT_FOUND));


			VipUpgradeEvent event = VipUpgradeEvent.builder()
					.userId(payment.getUserId())
					.vipPackageId(vipPackage.getId())
					.vipPackageName(vipPackage.getName())
					.durationDays(vipPackage.getDurationDays())
					.paymentId(payment.getId())
					.orderId(payment.getOrderId())
					.timestamp(Instant.now())
					.build();

			kafkaProducerService.publishVipUpgradeEvent(event);

		} else {
			payment.setPaymentStatus("FAILED");
			paymentRepository.save(payment);
			log.warn("❌ Payment FAILED: orderId={}, responseCode={}", payment.getOrderId(), responseCode);
		}
	}
}