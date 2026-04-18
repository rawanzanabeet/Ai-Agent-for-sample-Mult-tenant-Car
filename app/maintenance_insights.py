from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .schemas import MaintenanceInsightsRequest, MaintenanceInsightsResponse, RoiDecision


@dataclass(frozen=True)
class _RiskResult:
    score: float
    causes: List[str]


def _clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(value, max_value))


def _risk_from_inputs(payload: MaintenanceInsightsRequest) -> _RiskResult:
    causes: List[str] = []
    score = 0.0

    if payload.engineOilStatus == "needs_change":
        score += 0.35
        causes.append("حالة زيت المحرك تحتاج تغيير")
    elif payload.engineOilStatus == "fair":
        score += 0.2
        causes.append("حالة زيت المحرك متوسطة")

    if payload.mileageSinceService is not None:
        if payload.mileageSinceService > 9000:
            score += 0.3
            causes.append("عدد الكيلومترات منذ آخر صيانة مرتفع")
        elif payload.mileageSinceService > 6000:
            score += 0.2
            causes.append("عدد الكيلومترات منذ آخر صيانة أعلى من المتوسط")

    if payload.engineHours is not None:
        if payload.engineHours > 300:
            score += 0.15
            causes.append("ساعات تشغيل المحرك مرتفعة")
        elif payload.engineHours > 200:
            score += 0.1
            causes.append("ساعات تشغيل المحرك أعلى من المتوسط")

    if payload.drivingIntensity in {"high", "extreme"}:
        score += 0.1
        causes.append("شدة القيادة عالية")

    if payload.downtimeDays is not None and payload.downtimeDays > 3:
        score += 0.1
        causes.append("سجل توقفات متكرر")

    return _RiskResult(score=_clamp(score), causes=causes)


def _risk_level(score: float) -> str:
    if score >= 0.6:
        return "high"
    if score >= 0.3:
        return "medium"
    return "low"


def _build_roi(payload: MaintenanceInsightsRequest, score: float) -> RoiDecision:
    expected_loss = (
        score
        * payload.costPerDowntimeDay
        * payload.expectedDowntimeDays
    )
    estimated_savings = max(expected_loss - payload.currentServiceCost, 0.0)
    recommendation = "service_now" if estimated_savings > 0 else "monitor"
    rationale = (
        "الصيانة الآن تقلل خسائر التوقف المتوقعة."
        if recommendation == "service_now"
        else "التكلفة الحالية أعلى من الخسائر المتوقعة."
    )

    return RoiDecision(
        recommendation=recommendation,
        expectedLossIfDelayed=round(expected_loss, 2),
        estimatedSavings=round(estimated_savings, 2),
        windowDays=payload.windowDays,
        rationale=rationale,
    )


def build_maintenance_insights(
    payload: MaintenanceInsightsRequest,
) -> MaintenanceInsightsResponse:
    risk = _risk_from_inputs(payload)
    level = _risk_level(risk.score)
    roi = _build_roi(payload, risk.score)

    return MaintenanceInsightsResponse(
        carId=payload.carId,
        riskLevel=level,
        riskScore=round(risk.score, 2),
        rootCauses=risk.causes or ["لا توجد مؤشرات واضحة حتى الآن"],
        roiDecision=roi,
    )