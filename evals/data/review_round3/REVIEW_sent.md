# Eval set review - changes since review_round2

Only items that are new or changed since the previous review round are listed. 113 items are unchanged and keep their earlier verdict.
Write OK or the problem after each **Review:** line.

## New items (replacements and re-paired comparisons) (16)

### comp-a35732 (comparison, dev)
**Q:** Which company reported higher net cash provided by operating activities: Exxon Mobil for its fiscal year 2025 (ended December 31, 2025) or Walmart for its fiscal year 2026 (ended January 31, 2026)?
**A:** XOM
**Expected:** answer
**Evidence:** 51,970 || 41,565
**Values:** XOM=51970000000 WMT=41565000000; year-ends 31 days apart
**Review:** 

### comp-6a0693 (comparison, test)
**Q:** Which company reported higher total revenue (for Exxon Mobil, total revenues and other income): Exxon Mobil for its fiscal year 2024 (ended December 31, 2024) or Johnson & Johnson for its fiscal year 2024 (ended December 29, 2024)?
**A:** XOM
**Expected:** answer
**Evidence:** 349,585 || 88,821
**Values:** XOM=349585000000 JNJ=88821000000; year-ends 2 days apart
**Review:** 

### comp-4ea460 (comparison, dev)
**Q:** Which company reported higher net cash provided by operating activities: Apple for its fiscal year 2025 (ended September 27, 2025) or Johnson & Johnson for its fiscal year 2025 (ended December 28, 2025)?
**A:** AAPL
**Expected:** answer
**Evidence:** 111,482 || 24,530
**Values:** AAPL=111482000000 JNJ=24530000000; year-ends 92 days apart
**Review:** 

### comp-20ef0e (comparison, test)
**Q:** Which company reported higher net income (excluding noncontrolling interests): NVIDIA for its fiscal year 2026 (ended January 25, 2026) or Walmart for its fiscal year 2026 (ended January 31, 2026)?
**A:** NVDA
**Expected:** answer
**Evidence:** 120,067 || 21,893
**Values:** NVDA=120067000000 WMT=21893000000; year-ends 6 days apart
**Review:** 

### comp-6f405e (comparison, dev)
**Q:** Which company reported higher net income (excluding noncontrolling interests): Walmart for its fiscal year 2024 (ended January 31, 2024) or Coca-Cola for its fiscal year 2023 (ended December 31, 2023)?
**A:** WMT
**Expected:** answer
**Evidence:** 15,511 || 10,714
**Values:** WMT=15511000000 KO=10714000000; year-ends 31 days apart
**Review:** 

### comp-52ad07 (comparison, test)
**Q:** Which company reported higher total revenue (for JPMorgan Chase, total net revenue): NVIDIA for its fiscal year 2026 (ended January 25, 2026) or JPMorgan Chase for its fiscal year 2025 (ended December 31, 2025)?
**A:** NVDA
**Expected:** answer
**Evidence:** 215,938 || 182,447
**Values:** NVDA=215938000000 JPM=182447000000; year-ends 25 days apart
**Review:** 

### comp-6c6094 (comparison, dev)
**Q:** Which company reported higher total assets: Walmart for its fiscal year 2026 (ended January 31, 2026) or UnitedHealth Group for its fiscal year 2025 (ended December 31, 2025)?
**A:** UNH
**Expected:** answer
**Evidence:** 284,668 || 309,581
**Values:** WMT=284668000000 UNH=309581000000; year-ends 31 days apart
**Review:** 

### comp-131953 (comparison, dev)
**Q:** Which company reported higher net income: Amazon for its fiscal year 2023 (ended December 31, 2023) or NVIDIA for its fiscal year 2024 (ended January 28, 2024)?
**A:** AMZN
**Expected:** answer
**Evidence:** 30,425 || 29,760
**Values:** AMZN=30425000000 NVDA=29760000000; year-ends 28 days apart
**Review:** 

### comp-b6fb88 (comparison, test)
**Q:** Which company reported higher net income (excluding noncontrolling interests): Exxon Mobil for its fiscal year 2025 (ended December 31, 2025) or Walmart for its fiscal year 2026 (ended January 31, 2026)?
**A:** XOM
**Expected:** answer
**Evidence:** 28,844 || 21,893
**Values:** XOM=28844000000 WMT=21893000000; year-ends 31 days apart
**Review:** 

### comp-feb2ad (comparison, dev)
**Q:** Which company reported higher total revenue (for JPMorgan Chase, total net revenue): JPMorgan Chase for its fiscal year 2024 (ended December 31, 2024) or Johnson & Johnson for its fiscal year 2024 (ended December 29, 2024)?
**A:** JPM
**Expected:** answer
**Evidence:** 177,556 || 88,821
**Values:** JPM=177556000000 JNJ=88821000000; year-ends 2 days apart
**Review:** 

### comp-450265 (comparison, dev)
**Q:** Which company reported higher net income: Coca-Cola for its fiscal year 2025 (ended December 31, 2025) or Apple for its fiscal year 2025 (ended September 27, 2025)?
**A:** AAPL
**Expected:** answer
**Evidence:** 13,107 || 112,010
**Values:** KO=13107000000 AAPL=112010000000; year-ends 95 days apart
**Review:** 

### comp-e88544 (comparison, test)
**Q:** Which company reported higher total assets: UnitedHealth Group for its fiscal year 2023 (ended December 31, 2023) or NVIDIA for its fiscal year 2024 (ended January 28, 2024)?
**A:** UNH
**Expected:** answer
**Evidence:** 273,720 || 65,728
**Values:** UNH=273720000000 NVDA=65728000000; year-ends 28 days apart
**Review:** 

### comp-844340 (comparison, dev)
**Q:** Which company reported higher total revenue: Walmart for its fiscal year 2024 (ended January 31, 2024) or Coca-Cola for its fiscal year 2023 (ended December 31, 2023)?
**A:** WMT
**Expected:** answer
**Evidence:** 648,125 || 45,754
**Values:** WMT=648125000000 KO=45754000000; year-ends 31 days apart
**Review:** 

### comp-3c3552 (comparison, dev)
**Q:** Which company reported higher net cash provided by operating activities: NVIDIA for its fiscal year 2025 (ended January 26, 2025) or JPMorgan Chase for its fiscal year 2024 (ended December 31, 2024)?
**A:** NVDA
**Expected:** answer
**Evidence:** 64,089 || 42,012
**Values:** NVDA=64089000000 JPM=-42012000000; year-ends 26 days apart
**Review:** 

### comp-19dc9f (comparison, dev)
**Q:** Which company reported higher net income (excluding noncontrolling interests): Exxon Mobil for its fiscal year 2023 (ended December 31, 2023) or UnitedHealth Group for its fiscal year 2023 (ended December 31, 2023)?
**A:** XOM
**Expected:** answer
**Evidence:** 36,010 || 22,381
**Values:** XOM=36010000000 UNH=22381000000; year-ends 0 days apart
**Review:** 

### text-ce3dc7 (factual_text, dev)
**Q:** On what date does Microsoft perform its annual goodwill impairment test, according to its fiscal year 2024 Form 10-K?
**A:** Microsoft tests goodwill for impairment annually on May 1, at the reporting unit level. It also tests between annual dates if events make it more likely than not that a unit's fair value has fallen below its carrying value.
**Expected:** answer
**Evidence:** Goodwill is tested for impairment at the reporting unit level (operating segment or one level below an operating segment) on an annual basis (May 1) and between annual tests if an event occurs or circumstances change that would more likely than not reduce the fair value of a reporting unit below its carrying value.
**Review:** 

## Changed text items (wording or evidence) (6)

### text-436c04 (factual_text, dev)
**Q:** According to Apple's fiscal year 2023 Form 10-K, by when is Apple required to comply with the EU Digital Markets Act, which may force changes to its App Store?
**A:** Apple states it is required to comply with the EU Digital Markets Act by March 2024.
**Expected:** answer
**Evidence:** The Company expects to make further business changes in the future, including as a result of legislative initiatives impacting the App Store, such as the EU Digital Markets Act, which the Company is required to comply with by March 2024, or similar laws in other jurisdictions.
**Review:** 

### text-79530b (factual_text, dev)
**Was (text-0003):** According to Johnson & Johnson's fiscal year 2023 10-K, what is the earliest date by which the company anticipates a biosimilar version of STELARA could launch in the United States?
**Q:** According to Johnson & Johnson's fiscal year 2023 10-K, before what date does the company say it does not anticipate a U.S. launch of a biosimilar version of STELARA?
**A:** Because of settlements and other agreements with third parties, Johnson & Johnson does not anticipate a U.S. biosimilar launch of STELARA before January 1, 2025.
**Expected:** answer
**Evidence:** As a result of settlements and other agreements with third parties, the Company does not anticipate the launch of a biosimilar version of STELARA before January 1, 2025 in the United States.
**Review:** 

### text-c21c2e (factual_text, test)
**Q:** According to Apple's fiscal year 2024 Form 10-K, in which fiscal quarter has Apple historically experienced higher net sales, and why?
**A:** Apple has historically experienced higher net sales in its first fiscal quarter, due in part to seasonal holiday demand.
**Expected:** answer
**Evidence:** The Company has historically experienced higher net sales in its first quarter compared to other quarters in its fiscal year due in part to seasonal holiday demand.
**Review:** 

### text-89ac3b (factual_text, dev)
**Q:** According to NVIDIA's fiscal year 2025 10-K, how long is the delayed compliance period before the USG's "AI Diffusion" interim final rule imposes its worldwide licensing requirement, and on what date was the rule published?
**A:** The AI Diffusion IFR was published in the Federal Register on January 15, 2025. Its worldwide licensing requirement takes effect after a 120-day delayed compliance period, unless the rule is modified.
**Expected:** answer
**Evidence:** On January 15, 2025, the USG published the "AI Diffusion" IFR in the Federal Register. || After a 120-day delayed compliance period, the IFR will, unless modified, impose a worldwide licensing requirement on all products classified under Export Control Classification Numbers, or ECCNs, 3A090.a, 4A090.a, or corresponding .z ECCNs, including all related software and technology.
**Review:** 

### text-d9c222 (factual_text, dev)
**Was (text-0030):** In fiscal year 2025, which constitutional amendments did Johnson & Johnson's subsidiary Janssen claim the IRA's Medicare Drug Price Negotiation Program violates in its litigation against HHS and CMS?
**Q:** According to Johnson & Johnson's fiscal year 2025 10-K, which constitutional amendments does its subsidiary Janssen claim the IRA's Medicare Drug Price Negotiation Program violates, in its litigation against HHS and CMS?
**A:** Janssen sought a declaration that the IRA violates its rights under the First Amendment and the Fifth Amendment to the Constitution.
**Expected:** answer
**Evidence:** In July 2023, Janssen Pharmaceuticals, Inc. (Janssen) filed litigation against the U.S. Department of Health and Human Services as well as the Centers for Medicare and Medicaid Services challenging the constitutionality of the IRA's Medicare Drug Price Negotiation Program. || The litigation requests a declaration that the IRA violates Janssen's rights under the First Amendment and the Fifth Amendment to the Constitution and therefore that Janssen is not subject to the IRA's mandatory pricing scheme.
**Review:** 

### text-f42d67 (factual_text, dev)
**Was (text-0040):** In fiscal year 2025, which countries' bottling operations did Coca-Cola refranchise, contributing to the decrease in its Bottling Investments segment operating income?
**Q:** According to Coca-Cola's fiscal year 2025 10-K, where did Coca-Cola refranchise bottling operations, contributing to the decrease in its Bottling Investments segment operating income?
**A:** Coca-Cola refranchised its bottling operations in the Philippines, Bangladesh and certain territories in India.
**Expected:** answer
**Evidence:** Bottling Investments' operating income for the years ended December 31, 2025 and 2024 was $426 million and $496 million, respectively. The decrease in operating income was primarily driven by the impact of refranchising our bottling operations in the Philippines, Bangladesh and certain territories in India, higher commodity costs and an unfavorable foreign currency exchange rate impact of 2%, partially offset by favorable pricing initiatives and lower operating expenses.
**Review:** 

## Template rewording, code-generated items (15)

Systematic wording changes from template fixes (see the review feedback files).
Skim; answers are unchanged.

- num-0003: What was Johnson & Johnson's net income for fiscal year 2023?
- num-0012: What was Amazon's net income for fiscal year 2024?
- num-0014: What was JPMorgan Chase's net income for fiscal year 2023?
- num-0031: What was Apple's net income for fiscal year 2025?
- num-0045: What was Coca-Cola's net income for fiscal year 2023?
- calc-0005: By what percentage did Coca-Cola's net income change from fiscal year 2023 to fiscal year 2024?
- calc-0006: By what percentage did JPMorgan Chase's net income change from fiscal year 2024 to fiscal year 2025?
- calc-0010: By what percentage did Johnson & Johnson's net income change from fiscal year 2023 to fiscal year 2024?
- calc-0012: What was Coca-Cola's net profit margin (net income as a percentage of total revenue) for fiscal year 2024?
- calc-0013: What was Johnson & Johnson's net profit margin (net income as a percentage of total revenue) for fiscal year 2024?
- calc-0014: What was Amazon's net profit margin (net income as a percentage of total revenue) for fiscal year 2023?
- calc-0015: What was JPMorgan Chase's net profit margin (net income as a percentage of total net revenue) for fiscal year 2023?
- calc-0017: What was Microsoft's net profit margin (net income as a percentage of total revenue) for fiscal year 2024?
- calc-0018: What was NVIDIA's net profit margin (net income as a percentage of total revenue) for fiscal year 2026?
- calc-0020: What was Apple's net profit margin (net income as a percentage of total revenue) for fiscal year 2025?
