export const SUPPORTED_LOCALES = ["en"] as const;
export const DEFAULT_LOCALE = "en";

export type SupportedLocale = (typeof SUPPORTED_LOCALES)[number];

export function formatDateTime(value: string | number | Date | null | undefined, locale = DEFAULT_LOCALE) {
  if (value == null || value === "") {
    return "Not available";
  }
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Not available";
  }
  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(date);
}

export function formatNumber(value: number | null | undefined, locale = DEFAULT_LOCALE) {
  if (value == null || Number.isNaN(value)) {
    return "0";
  }
  return new Intl.NumberFormat(locale).format(value);
}

export function formatCompactNumber(value: number | null | undefined, locale = DEFAULT_LOCALE) {
  if (value == null || Number.isNaN(value)) {
    return "0";
  }
  return new Intl.NumberFormat(locale, {
    notation: "compact",
    maximumFractionDigits: 1
  }).format(value);
}

export function formatCurrency(
  value: number | null | undefined,
  currency = "USD",
  locale = DEFAULT_LOCALE
) {
  if (value == null || Number.isNaN(value)) {
    return "Not available";
  }
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    maximumFractionDigits: 0
  }).format(value);
}
