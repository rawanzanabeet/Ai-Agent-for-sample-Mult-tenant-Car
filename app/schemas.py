from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel

ChartInsightType = Literal["series", "multi-series", "pie"]
InsightValueType = Literal["number", "currency", "percent"]
InsightLabelType = Literal["none", "date"]


class Message(BaseModel):
    role: str
    content: str


class ContextUser(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    tenant: Optional[str] = None


class Context(BaseModel):
    user: Optional[ContextUser] = None
    application: Optional[str] = None
    version: Optional[str] = None


class CopilotRequest(BaseModel):
    messages: List[Message]
    context: Optional[Context] = None
    user: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class CopilotResponse(BaseModel):
    response: str
    suggestions: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class InsightItem(BaseModel):
    id: str
    text: str
    tone: Optional[Literal["positive", "neutral", "warning"]] = None


class InsightFormatterConfig(BaseModel):
    valueType: Optional[InsightValueType] = None
    currency: Optional[str] = None
    maximumFractionDigits: Optional[int] = None
    labelType: Optional[InsightLabelType] = None
    dateOptions: Optional[Dict[str, Any]] = None


class InsightsRequest(BaseModel):
    type: ChartInsightType
    data: List[Dict[str, Any]]
    labelKey: str
    metricLabel: str
    valueKey: Optional[str] = None
    valueKeys: Optional[List[str]] = None
    windowSize: Optional[int] = None
    maxItems: Optional[int] = None
    formatter: Optional[InsightFormatterConfig] = None


class InsightsResponse(BaseModel):
    insights: List[InsightItem]
    source: Literal["python"]

class MaintenanceInsightsRequest(BaseModel):
    carId: Optional[int] = None
    mileageSinceService: Optional[int] = None
    engineOilStatus: Optional[Literal["good", "fair", "needs_change"]] = None
    drivingIntensity: Optional[Literal["low", "moderate", "high", "extreme"]] = None
    engineHours: Optional[float] = None
    downtimeDays: Optional[int] = None
    costPerDowntimeDay: float = 0
    expectedDowntimeDays: float = 1
    currentServiceCost: float = 0
    windowDays: int = 30


class RoiDecision(BaseModel):
    recommendation: Literal["service_now", "monitor"]
    expectedLossIfDelayed: float
    estimatedSavings: float
    windowDays: int
    rationale: str


class MaintenanceInsightsResponse(BaseModel):
    carId: Optional[int] = None
    riskLevel: Literal["low", "medium", "high"]
    riskScore: float
    rootCauses: List[str]
    roiDecision: RoiDecision