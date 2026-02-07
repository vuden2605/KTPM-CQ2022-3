package com.example.market_service.service.PaymentService.Provider;

import com.example.market_service.Configure.VNPayConfig;
import com.example.market_service.Utils.VNPayUtil;
import com.example.market_service.entity.Payment;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.text.SimpleDateFormat;
import java.util.*;

@Slf4j
@RequiredArgsConstructor
@Service
public class VNPayProvider implements IPaymentProvider {
	@Override
	public String getType() {
		return "VNPAY";
	}

	private final VNPayConfig config;
	private final VNPayUtil vnPayUtil;

	@Override
	public String createPaymentUrl(Payment payment) {
		Map<String, String> params = new TreeMap<>();

		params.put("vnp_Version", "2.1.0");
		params.put("vnp_Command", "pay");
		params.put("vnp_TmnCode", config.getTmnCode());

		long amountInVND = payment.getAmount() * 100;
		params.put("vnp_Amount", String.valueOf(amountInVND));
		params.put("vnp_CurrCode", "VND");
		params.put("vnp_TxnRef", payment.getOrderId());
		params.put("vnp_OrderInfo", "Thanh toan don hang " + payment.getOrderId());
		params.put("vnp_OrderType", "other");

		// ✅ Thêm BankCode (quan trọng cho sandbox)
		params.put("vnp_BankCode", "NCB"); // Hoặc có thể để trống "" để user chọn

		params.put("vnp_Locale", "vn");
		params.put("vnp_ReturnUrl", config.getReturnUrl());

		// ✅ Sửa IP - lấy IP thật hoặc dùng IP public
		params.put("vnp_IpAddr", "8.8.8.8"); // test sandbox
		// Thay bằng IP thật từ request

		TimeZone timeZone = TimeZone.getTimeZone("Asia/Ho_Chi_Minh");
		SimpleDateFormat formatter = new SimpleDateFormat("yyyyMMddHHmmss");
		formatter.setTimeZone(timeZone);

		Calendar now = Calendar.getInstance(timeZone);
		String vnp_CreateDate = formatter.format(now.getTime());
		params.put("vnp_CreateDate", vnp_CreateDate);

		Calendar expireTime = Calendar.getInstance(timeZone);
		expireTime.add(Calendar.MINUTE, 15);
		String vnp_ExpireDate = formatter.format(expireTime.getTime());
		params.put("vnp_ExpireDate", vnp_ExpireDate);

		// Tạo hash
		String hashData = vnPayUtil.buildHashData(params);
		String secureHash = vnPayUtil.hmacSHA512(config.getHashSecret(), hashData);

		log.info("=== VNPay Debug ===");
		log.info("Hash Data: {}", hashData);
		log.info("Secure Hash: {}", secureHash);

		String queryString = vnPayUtil.buildQueryString(params);

		return config.getPayUrl() + "?" + queryString + "&vnp_SecureHash=" + secureHash;
	}
}