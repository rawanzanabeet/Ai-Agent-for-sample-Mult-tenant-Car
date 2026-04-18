from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, List, Optional, Sequence

from .schemas import InsightFormatterConfig, InsightItem, InsightsRequest

DEFAULT_WINDOW = 7
DEFAULT_MAX_ITEMS = 4


FormatValue = Callable[[float], str]
FormatLabel = Callable[[Any], str]


def _to_number(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0

    if number != number:  # NaN guard
        return 0.0

    return number


def _average(values: Sequence[float]) -> float:
    if not values:
        return 0.0

    return sum(values) / len(values)


def _format_percent(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}f}%"


def _parse_date(value: Any) -> Optional[datetime]:
    if value is None:
        return None

    text = str(value)
    try:
        return datetime.fromisoformat(text.replace('Z', '+00:00'))
    except ValueError:
        return None


def _format_date(value: Any) -> str:
    date = _parse_date(value)
    if not date:
        return str(value)

    return date.strftime('%b %d')


def _value_formatter(formatter: Optional[InsightFormatterConfig]) -> FormatValue:
    if not formatter or formatter.valueType in (None, 'number'):
        digits = formatter.maximumFractionDigits if formatter and formatter.maximumFractionDigits is not None else 1
        return lambda value: f"{value:,.{digits}f}".rstrip('0').rstrip('.') if digits > 0 else f"{value:,.0f}"

    if formatter.valueType == 'percent':
        digits = formatter.maximumFractionDigits if formatter.maximumFractionDigits is not None else 1
        return lambda value: _format_percent(value, digits)

    digits = formatter.maximumFractionDigits if formatter.maximumFractionDigits is not None else 0
    currency = formatter.currency or 'USD'

    def _format_currency(value: float) -> str:
        formatted = f"{value:,.{digits}f}"
        if digits > 0:
            formatted = formatted.rstrip('0').rstrip('.')
        return f"{currency} {formatted}"

    return _format_currency


def _label_formatter(formatter: Optional[InsightFormatterConfig]) -> Optional[FormatLabel]:
    if not formatter or formatter.labelType in (None, 'none'):
        return None

    if formatter.labelType == 'date':
        return _format_date

    return lambda value: str(value)


def _clamp_window(window_size: int, length: int) -> int:
    safe_window = max(2, window_size)
    half_length = max(2, length // 2)
    return min(safe_window, half_length)


def _find_extreme(data: Sequence[dict[str, Any]], value_key: str, mode: str) -> Optional[dict[str, Any]]:
    if not data:
        return None

    best = data[0]
    best_value = _to_number(best.get(value_key))

    for point in data[1:]:
        value = _to_number(point.get(value_key))
        if (mode == 'max' and value > best_value) or (mode == 'min' and value < best_value):
            best = point
            best_value = value

    return best


def build_series_insights(
    data: Sequence[dict[str, Any]],
    label_key: str,
    value_key: str,
    metric_label: str,
    format_value: FormatValue,
    format_label: Optional[FormatLabel],
    window_size: int,
) -> List[InsightItem]:
    if len(data) < 2:
        return []

    label = format_label or (lambda value: str(value))

    first_value = _to_number(data[0].get(value_key))
    last_value = _to_number(data[-1].get(value_key))
    change = last_value - first_value
    percent_change = (change / abs(first_value) * 100) if first_value != 0 else 0.0
    direction = 'up' if change >= 0 else 'down'

    insights: List[InsightItem] = [
        InsightItem(
            id='trend',
            tone='positive' if change >= 0 else 'warning',
            text=f"{metric_label} is trending {direction} {_format_percent(abs(percent_change))} over the selected range.",
        )
    ]

    peak_point = _find_extreme(data, value_key, 'max')
    if peak_point:
        peak_value = _to_number(peak_point.get(value_key))
        peak_label = label(peak_point.get(label_key))
        insights.append(
            InsightItem(
                id='peak',
                tone='neutral',
                text=f"Peak {metric_label.lower()} reached {format_value(peak_value)} on {peak_label}.",
            )
        )

    safe_window = _clamp_window(window_size, len(data))
    recent_values = [_to_number(point.get(value_key)) for point in data[-safe_window:]]
    previous_values = [_to_number(point.get(value_key)) for point in data[-safe_window * 2 : -safe_window]]

    if len(previous_values) == safe_window:
        recent_avg = _average(recent_values)
        previous_avg = _average(previous_values)
        momentum_change = recent_avg - previous_avg
        momentum_direction = 'higher' if momentum_change >= 0 else 'lower'
        momentum_pct = (momentum_change / abs(previous_avg) * 100) if previous_avg != 0 else 0.0
        insights.append(
            InsightItem(
                id='momentum',
                tone='positive' if momentum_change >= 0 else 'warning',
                text=f"The recent {safe_window}-point average is {momentum_direction} by {_format_percent(abs(momentum_pct))} versus the previous window.",
            )
        )

    return insights


def build_multi_series_insights(
    data: Sequence[dict[str, Any]],
    label_key: str,
    value_keys: Sequence[str],
    metric_label: str,
    format_value: FormatValue,
    format_label: Optional[FormatLabel],
    window_size: int,
) -> List[InsightItem]:
    if not value_keys:
        return []

    primary_key = value_keys[0]
    insights = build_series_insights(data, label_key, primary_key, metric_label, format_value, format_label, window_size)

    if len(value_keys) < 2 or len(data) < 2:
        return insights

    secondary_key = value_keys[1]
    latest_point = data[-1]
    previous_point = data[-2]

    current_primary = _to_number(latest_point.get(primary_key))
    current_secondary = _to_number(latest_point.get(secondary_key))
    previous_primary = _to_number(previous_point.get(primary_key))
    previous_secondary = _to_number(previous_point.get(secondary_key))

    if current_secondary > 0 and previous_secondary > 0:
        current_ratio = current_primary / current_secondary
        previous_ratio = previous_primary / previous_secondary
        ratio_change = current_ratio - previous_ratio
        ratio_pct = (ratio_change / abs(previous_ratio) * 100) if previous_ratio != 0 else 0.0
        direction = 'up' if ratio_change >= 0 else 'down'
        insights.append(
            InsightItem(
                id='ratio',
                tone='positive' if ratio_change >= 0 else 'warning',
                text=f"Efficiency per {secondary_key.lower()} moved {direction} {_format_percent(abs(ratio_pct))} to {format_value(current_ratio)}.",
            )
        )

    return insights


def build_pie_insights(
    data: Sequence[dict[str, Any]],
    label_key: str,
    value_key: str,
    metric_label: str,
    format_value: FormatValue,
    format_label: Optional[FormatLabel],
    max_items: int,
) -> List[InsightItem]:
    if not data:
        return []

    label = format_label or (lambda value: str(value))

    enriched = [
        {**item, '_value': _to_number(item.get(value_key))}
        for item in data
        if _to_number(item.get(value_key)) > 0
    ]

    if not enriched:
        return []

    total = sum(item['_value'] for item in enriched)
    sorted_items = sorted(enriched, key=lambda item: item['_value'], reverse=True)
    top = sorted_items[0]
    top_share = (top['_value'] / total) * 100 if total else 0.0

    insights: List[InsightItem] = [
        InsightItem(
            id='top-share',
            tone='warning' if top_share > 50 else 'neutral',
            text=f"{label(top.get(label_key))} leads with {_format_percent(top_share)} of {metric_label.lower()} ({format_value(top['_value'])}).",
        )
    ]

    slice_size = min(max_items, len(sorted_items))
    top_slice = sorted_items[:slice_size]
    top_slice_value = sum(item['_value'] for item in top_slice)
    concentration = (top_slice_value / total) * 100 if total else 0.0

    insights.append(
        InsightItem(
            id='concentration',
            tone='warning' if concentration > 80 else 'neutral',
            text=f"Top {slice_size} categories account for {_format_percent(concentration)} of the total distribution.",
        )
    )

    insights.append(
        InsightItem(
            id='coverage',
            tone='positive',
            text=f"{len(sorted_items)} active segments contribute to the current {metric_label.lower()} mix.",
        )
    )

    return insights


def build_insights(request: InsightsRequest) -> List[InsightItem]:
    formatter = request.formatter
    format_value = _value_formatter(formatter)
    format_label = _label_formatter(formatter)
    window_size = request.windowSize or DEFAULT_WINDOW
    max_items = request.maxItems or DEFAULT_MAX_ITEMS

    if request.type == 'pie':
        if not request.valueKey:
            return []
        return build_pie_insights(
            request.data,
            request.labelKey,
            request.valueKey,
            request.metricLabel,
            format_value,
            format_label,
            max_items,
        )

    if request.type == 'multi-series':
        if not request.valueKeys:
            return []
        return build_multi_series_insights(
            request.data,
            request.labelKey,
            request.valueKeys,
            request.metricLabel,
            format_value,
            format_label,
            window_size,
        )

    if not request.valueKey:
        return []

    return build_series_insights(
        request.data,
        request.labelKey,
        request.valueKey,
        request.metricLabel,
        format_value,
        format_label,
        window_size,
    )