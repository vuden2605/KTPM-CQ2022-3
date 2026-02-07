package com.example.market_service.service.PaymentService.Provider;

import com.example.market_service.entity.Payment;

public interface IPaymentProvider {
	String getType();
	String createPaymentUrl(Payment payment);
}
