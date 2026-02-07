package com.example.market_service.service.PaymentService.Factory;

import com.example.market_service.service.PaymentService.Provider.IPaymentProvider;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Map;
import java.util.Optional;

@Component
public class PaymentProviderFactory {
	private final Map<String, IPaymentProvider> providers;
	private PaymentProviderFactory(List<IPaymentProvider> paymentProviders) {
		providers = paymentProviders.stream()
				.collect(java.util.stream.Collectors.toMap(
						IPaymentProvider::getType,
						provider -> provider
				));
	}
	public IPaymentProvider getProvider(String type) {
		return Optional.ofNullable(providers.get(type))
				.orElseThrow(() ->
						new RuntimeException("Unsupported payment type"));
	}
}
