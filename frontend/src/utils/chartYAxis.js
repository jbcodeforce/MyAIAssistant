/**
 * Top / middle / bottom labels for a linear Y-axis from 0 to maxValue.
 * Avoids duplicate labels when max is small (e.g. Math.round(1/2) === 1).
 */
export function getYAxisTickLabels(maxValue) {
  const max = Math.max(0, Number(maxValue) || 0)
  const mid = max / 2

  function formatTop(value) {
    if (!Number.isFinite(value) || value <= 0) return '0'
    if (Number.isInteger(value) || Math.abs(value - Math.round(value)) < 1e-9) {
      return String(Math.round(value))
    }
    return value.toFixed(1)
  }

  function formatMiddle(value) {
    if (!Number.isFinite(value) || max <= 0) return '0'
    if (max <= 1) {
      return value.toFixed(1)
    }
    if (Number.isInteger(max)) {
      return String(Math.round(max / 2))
    }
    if (max < 20) {
      if (Math.abs(value - Math.round(value)) < 1e-9) {
        return String(Math.round(value))
      }
      return value.toFixed(1)
    }
    return String(Math.round(value))
  }

  return {
    top: formatTop(max),
    middle: formatMiddle(mid),
    bottom: '0'
  }
}
