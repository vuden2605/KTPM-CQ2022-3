package com.example.market_service.service.VipService;

import com.example.market_service.entity.User;
import com.example.market_service.entity.VipPackage;

public interface IVipService {
	void upgradeVip(User user, VipPackage vipPackage);

	void checkExpiredVip(User user);
}
