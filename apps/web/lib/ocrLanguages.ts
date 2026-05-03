/**
 * MinerU CLI `-l` / `--lang` values (pipeline & hybrid backends).
 * Labels mirror official UI wording where possible.
 */

export const OCR_LANGUAGE_OPTIONS = [
  {
    value: "ch",
    label:
      "ch (Chinese, English, Chinese Traditional)",
  },
  {
    value: "ch_lite",
    label:
      "ch_lite (Chinese, English, Chinese Traditional, Japanese)",
  },
  {
    value: "ch_server",
    label:
      "ch_server (Chinese, English, Chinese Traditional, Japanese)",
  },
  {
    value: "en",
    label: "en (English)",
  },
  {
    value: "korean",
    label: "korean (Korean, English)",
  },
  {
    value: "japan",
    label:
      "japan (Chinese, English, Chinese Traditional, Japanese)",
  },
  {
    value: "chinese_cht",
    label:
      "chinese_cht (Chinese, English, Chinese Traditional, Japanese)",
  },
  {
    value: "ta",
    label: "ta (Tamil, English)",
  },
  {
    value: "te",
    label: "te (Telugu, English)",
  },
  {
    value: "ka",
    label: "ka (Kannada)",
  },
  {
    value: "el",
    label: "el (Greek, English)",
  },
  {
    value: "th",
    label: "th (Thai, English)",
  },
  {
    value: "latin",
    label:
      "latin (French, German, Afrikaans, Italian, Spanish, Bosnian, Portuguese, Czech, Welsh, Danish, Estonian, Irish, Croatian, Uzbek, Hungarian, Serbian (Latin), Indonesian, Occitan, Icelandic, Lithuanian, Maori, Malay, Dutch, Norwegian, Polish, Slovak, Slovenian, Albanian, …)",
  },
  {
    value: "arabic",
    label: "arabic (Arabic, English, …)",
  },
  {
    value: "east_slavic",
    label: "east_slavic (East Slavic languages, English, …)",
  },
  {
    value: "cyrillic",
    label: "cyrillic (Cyrillic-script languages, English, …)",
  },
  {
    value: "devanagari",
    label: "devanagari (Hindi, Marathi, Nepali, English, …)",
  },
] as const;

export type OcrLanguageCode = (typeof OCR_LANGUAGE_OPTIONS)[number]["value"];

export const DEFAULT_OCR_LANGUAGE: OcrLanguageCode = "ch";

export const OCR_LANGUAGE_VALUES: OcrLanguageCode[] = OCR_LANGUAGE_OPTIONS.map(
  (o) => o.value,
);

export function isOcrLanguageCode(s: string): s is OcrLanguageCode {
  return (OCR_LANGUAGE_VALUES as readonly string[]).includes(s);
}
