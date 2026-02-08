package com.example.payment_service.controller;

import com.example.payment_service.dto.response.ApiResponse;
import com.example.payment_service.dto.response.VipPackageResponse;
import com.example.payment_service.entity.VipPackage;
import com.example.payment_service.repository.VipPackageRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/vip-packages")
@RequiredArgsConstructor
public class VipPackageController {
	private final VipPackageRepository vipPackageRepository;

	@GetMapping
	public ApiResponse<List<VipPackageResponse>> getAllVipPackages() {
		List<VipPackageResponse> packages = vipPackageRepository.findByIsActiveTrue()
				.stream()
				.map(this::toResponse)
				.collect(Collectors.toList());

		return ApiResponse.<List<VipPackageResponse>>builder()
				.message("VIP packages retrieved successfully")
				.data(packages)
				.build();
	}

	@GetMapping("/{id}")
	public ApiResponse<VipPackageResponse> getVipPackage(@PathVariable Long id) {
		VipPackage vipPackage = vipPackageRepository.findById(id)
				.orElseThrow(() -> new RuntimeException("VIP package not found"));

		return ApiResponse.<VipPackageResponse>builder()
				.message("VIP package retrieved successfully")
				.data(toResponse(vipPackage))
				.build();
	}

	private VipPackageResponse toResponse(VipPackage vipPackage) {
		return VipPackageResponse.builder()
				.id(vipPackage.getId())
				.name(vipPackage.getName())
				.durationDays(vipPackage.getDurationDays())
				.price(vipPackage.getPrice())
				.description(vipPackage.getDescription())
				.isActive(vipPackage.getIsActive())
				.createdAt(vipPackage.getCreatedAt())
				.updatedAt(vipPackage.getUpdatedAt())
				.build();
	}
}