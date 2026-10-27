# Judge calibration - label each response

For each item, compare the **Response** with the **Reference answer** and the
**Evidence** from the filing. Write PASS or FAIL after **Your verdict:**
(optionally a short reason).

- **PASS:** the response answers the question correctly and completely. Extra detail
  is fine unless it is wrong or contradicts the evidence.
- **FAIL:** wrong, incomplete on an important point, or contains a wrong claim.

The judge's verdicts are stored separately; this file doesn't show them.

## cal-01
**Question:** What long-term debt rating did Moody's Investors Service assign to Walmart as of January 31, 2024, as reported in Walmart's fiscal year 2024 10-K?

**Reference answer:** Moody's assigned Walmart's long-term debt a rating of Aa2 (and P-1 for commercial paper).

**Evidence:** As of January 31, 2024, the ratings assigned to our commercial paper and rated series of our outstanding long-term debt were as follows: || Rating agency || Commercial paper || Long-term debt || Moody's Investors Service || P-1 || Aa2

**Response:**

> Moody's Investors Service assigned Walmart a long-term debt rating of **Aa2** as of January 31, 2024, as reported in the FY2024 Form 10-K.

**Your verdict:** PASS - Aa2 correct; omitting P-1 fine since the question asks about long-term debt.

## cal-02
**Question:** Approximately how many full-time equivalent employees did Apple report having as of the end of fiscal year 2025 (September 27, 2025)?

**Reference answer:** Apple had approximately 166,000 full-time equivalent employees as of September 27, 2025.

**Evidence:** As of September 27, 2025, the Company had approximately 166,000 full-time equivalent employees.

**Response:**

> Apple reported approximately **166,000** full-time equivalent employees as of September 27, 2025.

**Your verdict:** PASS

## cal-03
**Question:** In its fiscal year 2024 10-K risk factors, which acquisition does Exxon Mobil specifically name when discussing its ability to integrate and achieve anticipated synergies as part of operational efficiency?

**Reference answer:** Exxon Mobil specifically names the acquisition of Pioneer.

**Evidence:** Operational efficiency. || An important component of ExxonMobil's competitive performance, especially given the commodity-based nature of many of our businesses, is our ability to operate efficiently, including our ability to manage expenses, improve production || yields on an ongoing basis and successfully integrate and achieve the anticipated synergies of acquisitions, including the acquisition of Pioneer.

**Response:**

> In its fiscal year 2024 10-K risk factors, ExxonMobil specifically names its **acquisition of Pioneer Natural Resources Company (Pioneer)** when discussing its ability to integrate and achieve anticipated synergies under operational efficiency.

**Your verdict:** PASS

## cal-04
**Question:** What was NVIDIA's overall employee turnover rate in fiscal year 2024?

**Reference answer:** NVIDIA's overall turnover rate in fiscal year 2024 was 2.7%.

**Evidence:** In fiscal year 2024, our overall turnover rate was 2.7%.

**Response:**

> NVIDIA's overall employee turnover rate in fiscal year 2024 was 2.7% [C1].

**Your verdict:** PASS

## cal-05
**Question:** In its fiscal year 2024 10-K risk factors, which acquisition does Exxon Mobil specifically name when discussing its ability to integrate and achieve anticipated synergies as part of operational efficiency?

**Reference answer:** Exxon Mobil specifically names the acquisition of Pioneer.

**Evidence:** Operational efficiency. || An important component of ExxonMobil's competitive performance, especially given the commodity-based nature of many of our businesses, is our ability to operate efficiently, including our ability to manage expenses, improve production || yields on an ongoing basis and successfully integrate and achieve the anticipated synergies of acquisitions, including the acquisition of Pioneer.

**Response:**

> In its FY2024 10-K, Exxon Mobil names the **Pioneer** acquisition, which is Pioneer Natural Resources Company. The operational efficiency discussion refers to the need to "successfully integrate and achieve the anticipated synergies of acquisitions, including the acquisition of Pioneer."

**Your verdict:** PASS

## cal-06
**Question:** According to Johnson & Johnson's fiscal year 2023 10-K, before what date does the company say it does not anticipate a U.S. launch of a biosimilar version of STELARA?

**Reference answer:** Because of settlements and other agreements with third parties, Johnson & Johnson does not anticipate a U.S. biosimilar launch of STELARA before January 1, 2025.

**Evidence:** As a result of settlements and other agreements with third parties, the Company does not anticipate the launch of a biosimilar version of STELARA before January 1, 2025 in the United States.

**Response:**

> According to the FY2023 10-K, the company does not anticipate a U.S. launch of a biosimilar version of STELARA before January 1, 2025 [C1]. It reiterates that it does not anticipate a launch of a biosimilar version of STELARA until January 1, 2025 in the United States [C2].

**Your verdict:** PASS

## cal-07
**Question:** Approximately how many full-time and part-time employees did Amazon employ as of December 31, 2023, according to its fiscal year 2023 10-K?

**Reference answer:** Amazon employed approximately 1,525,000 full-time and part-time employees as of December 31, 2023.

**Evidence:** As of December 31, 2023, we employed approximately 1,525,000 full-time and part-time employees.

**Response:**

> Amazon employed approximately **1,525,000** full-time and part-time employees as of December 31, 2023, according to its FY2023 Form 10-K.

**Your verdict:** PASS

## cal-08
**Question:** According to Apple's fiscal year 2025 10-K, what was the primary reason for the decrease in Greater China net sales during fiscal year 2025 compared to 2024, and what partially offset it?

**Reference answer:** Greater China net sales fell mainly because of lower iPhone net sales, partially offset by higher Mac net sales.

**Evidence:** Greater China net sales decreased during 2025 compared to 2024 primarily due to lower net sales of iPhone, partially offset by higher net sales of Mac.

**Response:**

> According to Apple's fiscal 2025 Form 10-K, **Greater China net sales fell mainly because of lower iPhone sales. Higher Mac sales partially offset that decline.**
> 
> Greater China net sales dropped about 4%, from $66,952 million in fiscal 2024 to $64,377 million in fiscal 2025. It was the only reportable segment whose sales declined that year. It also continued the drop from the prior year, when sales fell 8% from $72,559 million in fiscal 2023.

**Your verdict:** PASS - Core answer right; extra segment figures not in evidence but plausible, no contradiction.

## cal-09
**Question:** On what date does Microsoft perform its annual goodwill impairment test, according to its fiscal year 2024 Form 10-K?

**Reference answer:** Microsoft tests goodwill for impairment annually on May 1, at the reporting unit level. It also tests between annual dates if events make it more likely than not that a unit's fair value has fallen below its carrying value.

**Evidence:** Goodwill is tested for impairment at the reporting unit level (operating segment or one level below an operating segment) on an annual basis (May 1) and between annual tests if an event occurs or circumstances change that would more likely than not reduce the fair value of a reporting unit below its carrying value.

**Response:**

> Microsoft performs its annual goodwill impairment test on **May 1**. The test is done at the reporting unit level, primarily using a discounted cash flow method with a peer-based, risk-adjusted weighted average cost of capital.
> 
> The fiscal year 2024 Form 10-K reports no impairments in the May 1, 2024, May 1, 2023, or May 1, 2022 tests. Accumulated goodwill impairment was $11.3 billion as of June 30, 2024 and 2023.

**Your verdict:** PASS - May 1 correct; extra impairment details consistent with the filing.

## cal-10
**Question:** In its fiscal year 2024 10-K risk factors, what position has the Indian tax authority asserted against Amazon, and how is Amazon responding?

**Reference answer:** The Indian tax authority has asserted that tax applies to cloud services fees paid to Amazon in the U.S., and Amazon is contesting this position.

**Evidence:** For example, the Indian tax authority has asserted that tax applies to cloud services fees paid to Amazon in the U.S. || We are contesting this position; however, if this matter is adversely resolved, we may be required to pay additional amounts with respect to current and prior periods and our taxes in the future could increase.

**Response:**

> In its FY2024 Form 10-K risk factors, Amazon reports that the Indian tax authority has asserted that tax applies to cloud services fees paid to Amazon in the U.S.
> 
> Amazon is contesting this position. It warns that if the matter is adversely resolved, it may have to pay additional amounts for current and prior periods, and its future taxes could increase. Amazon also says it regularly assesses the likelihood of an adverse outcome to determine whether its tax accruals are adequate.

**Your verdict:** PASS

## cal-11
**Question:** What percentage of NVIDIA's total revenue for fiscal year 2024 was estimated to come from a single indirect customer purchasing primarily through system integrators and distributors, and to which segment was it attributable?

**Reference answer:** That indirect customer was estimated at about 19% of total revenue for fiscal year 2024. It was attributable to the Compute & Networking segment.

**Evidence:** One indirect customer which primarily purchases our products through system integrators and distributors, including through Customer A, is estimated to have represented approximately 19% of total revenue for fiscal year 2024, attributable to the Compute & Networking segment.

**Response:**

> NVIDIA estimated that one indirect customer, which bought mainly through system integrators and distributors (including through Customer A), accounted for about **19% of total revenue in fiscal year 2024**. That revenue was attributable to the **Compute & Networking** segment.

**Your verdict:** PASS

## cal-12
**Question:** According to Coca-Cola's fiscal year 2025 10-K, where did Coca-Cola refranchise bottling operations, contributing to the decrease in its Bottling Investments segment operating income?

**Reference answer:** Coca-Cola refranchised its bottling operations in the Philippines, Bangladesh and certain territories in India.

**Evidence:** Bottling Investments' operating income for the years ended December 31, 2025 and 2024 was $426 million and $496 million, respectively. The decrease in operating income was primarily driven by the impact of refranchising our bottling operations in the Philippines, Bangladesh and certain territories in India, higher commodity costs and an unfavorable foreign currency exchange rate impact of 2%, partially offset by favorable pricing initiatives and lower operating expenses.

**Response:**

> According to the 2025 10-K, the refranchising of bottling operations in the **Philippines, Bangladesh, and certain territories in India** drove the decrease in Bottling Investments' operating income, which fell to $426 million in 2025 from $496 million in 2024.

**Your verdict:** PASS

## cal-13
**Question:** What long-term debt rating did Moody's Investors Service assign to Walmart as of January 31, 2024, as reported in Walmart's fiscal year 2024 10-K?

**Reference answer:** Moody's assigned Walmart's long-term debt a rating of Aa2 (and P-1 for commercial paper).

**Evidence:** As of January 31, 2024, the ratings assigned to our commercial paper and rated series of our outstanding long-term debt were as follows: || Rating agency || Commercial paper || Long-term debt || Moody's Investors Service || P-1 || Aa2

**Response:**

> Moody's Investors Service assigned Walmart a long-term debt rating of Aa2 as of January 31, 2024, per the FY2024 10-K ratings table [C1]. The ratings table in the FY2025 10-K also shows Aa2 but is for a different reporting period [C5].

**Your verdict:** PASS

## cal-14
**Question:** What was NVIDIA's overall employee turnover rate in fiscal year 2024?

**Reference answer:** NVIDIA's overall turnover rate in fiscal year 2024 was 2.7%.

**Evidence:** In fiscal year 2024, our overall turnover rate was 2.7%.

**Response:**

> NVIDIA's overall employee turnover rate in fiscal year 2024 was **2.7%**.
> 
> For comparison, the context also gives the rates for the following years: 2.5% in fiscal year 2025 and 3.7% in fiscal year 2026.

**Your verdict:** PASS - Extra FY2025/FY2026 turnover rates not in evidence.

## cal-15
**Question:** What was the size of the charge associated with H20 excess inventory and purchase obligations that contributed to NVIDIA's gross margin decrease in fiscal year 2026?

**Reference answer:** NVIDIA recorded a $4.5 billion charge associated with H20 excess inventory and purchase obligations in fiscal year 2026.

**Evidence:** Gross margin decreased in fiscal year 2026 as our business model transitioned from offering Hopper HGX systems to Blackwell full-scale datacenter solutions. || The gross margin decrease was also impacted by a $4.5 billion charge associated with H20 excess inventory and purchase obligations.

**Response:**

> The charge was $4.5 billion. NVIDIA recorded it in the first quarter of fiscal year 2026 for H20 excess inventory and purchase obligations, after the USG required licenses for H20 exports to China in April 2025.

**Your verdict:** PASS

## cal-16
**Question:** In its fiscal year 2023 10-K risk factors, what program does Amazon describe under which it may reimburse customers when third-party sellers fail to deliver products or deliver products materially different from their descriptions?

**Reference answer:** The A-to-z Guarantee, under which Amazon may reimburse customers for payments up to certain limits; its cost will increase as third-party seller sales grow.

**Evidence:** Under our seller programs, we maintain policies and processes designed to prevent sellers from collecting payments, fraudulently or otherwise, when buyers never receive the products they ordered or when the products received are materially different from the sellers' descriptions, and to prevent sellers in our stores or through other stores from selling unlawful, counterfeit, pirated, or stolen goods, selling goods in an unlawful or unethical manner, violating the proprietary rights of others, or otherwise violating our policies. || Under our A-to-z Guarantee, we may reimburse customers for payments up to certain limits in these situations, and as our third-party seller sales grow, the cost of this program will increase and could negatively affect our operating results.

**Response:**

> Under its **A-to-z Guarantee**, Amazon may reimburse customers for payments up to certain limits when buyers never receive products from third-party sellers, or when the products received are materially different from the sellers' descriptions. Amazon notes that as third-party seller sales grow, the cost of this program will increase and could negatively affect its operating results.

**Your verdict:** PASS

## cal-17
**Question:** According to Exxon Mobil's fiscal year 2025 10-K risk factors, what combined program does the company use to minimize spills?

**Reference answer:** ExxonMobil works to minimize spills through a combined program of effective operations integrity management, ongoing upgrades, key equipment replacements, and comprehensive inspection and surveillance.

**Evidence:** For example, we work to minimize spills through a combined program of effective operations integrity management, ongoing upgrades, key equipment replacements, and comprehensive inspection and surveillance.

**Response:**

> According to Exxon Mobil's FY2025 10-K risk factors, the company minimizes spills through a combined program of effective operations integrity management, ongoing upgrades, key equipment replacements, and comprehensive inspection and surveillance.

**Your verdict:** PASS

## cal-18
**Question:** According to Coca-Cola's fiscal year 2025 10-K, where did Coca-Cola refranchise bottling operations, contributing to the decrease in its Bottling Investments segment operating income?

**Reference answer:** Coca-Cola refranchised its bottling operations in the Philippines, Bangladesh and certain territories in India.

**Evidence:** Bottling Investments' operating income for the years ended December 31, 2025 and 2024 was $426 million and $496 million, respectively. The decrease in operating income was primarily driven by the impact of refranchising our bottling operations in the Philippines, Bangladesh and certain territories in India, higher commodity costs and an unfavorable foreign currency exchange rate impact of 2%, partially offset by favorable pricing initiatives and lower operating expenses.

**Response:**

> According to the FY2025 10-K, the decline in Bottling Investments' operating income (from $496 million to $426 million) was driven partly by refranchising bottling operations in **the Philippines, Bangladesh, and certain territories in India**.

**Your verdict:** PASS

## cal-19
**Question:** On what date does Microsoft perform its annual goodwill impairment test, according to its fiscal year 2024 Form 10-K?

**Reference answer:** Microsoft tests goodwill for impairment annually on May 1, at the reporting unit level. It also tests between annual dates if events make it more likely than not that a unit's fair value has fallen below its carrying value.

**Evidence:** Goodwill is tested for impairment at the reporting unit level (operating segment or one level below an operating segment) on an annual basis (May 1) and between annual tests if an event occurs or circumstances change that would more likely than not reduce the fair value of a reporting unit below its carrying value.

**Response:**

> According to Microsoft's FY2024 Form 10-K, Microsoft performs its annual goodwill impairment test on **May 1**.

**Your verdict:** PASS

## cal-20
**Question:** In fiscal year 2025, which two Microsoft businesses were combined into a single revenue growth metric as part of the metric updates tied to the segment changes?

**Reference answer:** Microsoft combined Windows OEM and Devices into a single revenue growth metric that brings together revenue from its PC market-driven businesses.

**Evidence:** In the first quarter of fiscal year 2025, we made updates to our metrics in connection with the segment changes described above. || Other changes include combining Windows OEM and Devices into a single revenue growth metric that brings revenue from PC market-driven businesses together, as well as elevating our cloud revenue growth metrics to align to our strategic focus on cloud growth.

**Response:**

> In fiscal year 2025, **Windows OEM and Devices** were combined into a single revenue growth metric. This brought revenue from PC market-driven businesses together.

**Your verdict:** PASS

## cal-21
**Question:** In its fiscal year 2024 10-K risk factors, what position has the Indian tax authority asserted against Amazon, and how is Amazon responding?

**Reference answer:** The Indian tax authority has asserted that tax applies to cloud services fees paid to Amazon in the U.S., and Amazon is contesting this position.

**Evidence:** For example, the Indian tax authority has asserted that tax applies to cloud services fees paid to Amazon in the U.S. || We are contesting this position; however, if this matter is adversely resolved, we may be required to pay additional amounts with respect to current and prior periods and our taxes in the future could increase.

**Response:**

> The Indian tax authority (ITA) has asserted that tax applies to cloud services fees that Amazon receives from customers in India but that are paid to Amazon in the U.S.
> 
> Amazon is contesting this position. Its FY2024 10-K says it believes the ITA's position is without merit, is defending its position vigorously, and expects to recover the taxes it pays. In the meantime, Amazon will need to keep remitting taxes on these fees until the matter is resolved, and those payments could be significant in aggregate. The company also states that if the matter is adversely resolved, it could be required to pay additional amounts for current and prior periods and could recognize significant additional tax expense. Amazon regularly assesses the likelihood of an adverse outcome to determine whether its tax accruals are adequate.

**Your verdict:** PASS - Correct; extra detail beyond evidence but no contradiction.

## cal-22
**Question:** In its fiscal year 2025 Form 10-K risk factors, which recently acquired UnitedHealth Group business does the company cite as having been subject to a cyberattack in 2024?

**Reference answer:** Change Healthcare, which UnitedHealth Group had recently acquired, was hit by a cyberattack in 2024. The data involved contained protected health information or personally identifiable information.

**Evidence:** For example, we previously reported that our Change Healthcare business, which we had recently acquired, was subject to a cyberattack in 2024, in which the data involved contained protected health information or personally identifiable information.

**Response:**

> The business is **Change Healthcare**, which UnitedHealth Group had recently acquired. The risk factors describe it as having been subject to a cyberattack in 2024, in which the data involved contained protected health information or personally identifiable information.
> 
> The sentence naming Change Healthcare appears in the FY2024 Form 10-K risk factors. The FY2025 excerpt provided includes the general cybersecurity risk language but not that specific example, so the answer comes from the FY2024 text.

**Your verdict:** FAIL - Borderline: answer correct, but claims the sentence is in the FY2024 10-K, not FY2025 - that claim is wrong.

## cal-23
**Question:** In its fiscal year 2024 10-K risk factors, which acquisition does Exxon Mobil specifically name when discussing its ability to integrate and achieve anticipated synergies as part of operational efficiency?

**Reference answer:** Exxon Mobil specifically names the acquisition of Pioneer.

**Evidence:** Operational efficiency. || An important component of ExxonMobil's competitive performance, especially given the commodity-based nature of many of our businesses, is our ability to operate efficiently, including our ability to manage expenses, improve production || yields on an ongoing basis and successfully integrate and achieve the anticipated synergies of acquisitions, including the acquisition of Pioneer.

**Response:**

> In its FY2024 10-K risk factors, Exxon Mobil names the **Pioneer** acquisition (Pioneer Natural Resources). In the operational efficiency discussion, it says the company must "successfully integrate and achieve the anticipated synergies of acquisitions, including the acquisition of Pioneer."

**Your verdict:** PASS

## cal-24
**Question:** In fiscal year 2024, how much did Coca-Cola record in other operating charges related to the impairment of its BodyArmor trademark?

**Reference answer:** Coca-Cola recorded $760 million of other operating charges in 2024 for the impairment of its BodyArmor trademark.

**Evidence:** In 2024, the Company recorded other operating charges of $4,163 million. These charges consisted of $3,109 million related to the remeasurement of our contingent consideration liability to fair value in conjunction with our acquisition of fairlife in 2020, $760 million related to the impairment of our BodyArmor trademark, $133 million related to the Company's productivity and reinvestment program and $126 million related to the impairment of a trademark in Latin America.

**Response:**

> In fiscal 2024, Coca-Cola recorded $760 million in other operating charges related to the impairment of its BodyArmor trademark [C1][C2]. This is also confirmed in the FY2024 fair value note, which describes the $760 million asset impairment charge on the BodyArmor trademark in North America recorded in other operating charges [C5][C7].

**Your verdict:** PASS

## cal-25
**Question:** Under UnitedHealth Group's fiscal year 2024 10-K, what minimum CMS star rating must a Medicare Advantage plan have to qualify for quality bonus payments?

**Reference answer:** A Medicare Advantage plan must have a rating of four stars or higher to qualify for CMS quality bonus payments.

**Evidence:** For example, as part of the ACA, CMS has a system providing various quality bonus payments to Medicare Advantage plans meeting specified quality star ratings at the individual plan or local contract level. || Plans must have a rating of four stars or higher to qualify for bonus payments, and CMS has and may make changes to the star rating program that impact the ability of plans to achieve four-star or higher ratings.

**Response:**

> Under UnitedHealth Group's FY2024 Form 10-K, a Medicare Advantage plan must have a **four-star rating or higher** to qualify for CMS quality bonus payments.

**Your verdict:** PASS

## cal-26
**Question:** According to Coca-Cola's fiscal year 2025 10-K, where did Coca-Cola refranchise bottling operations, contributing to the decrease in its Bottling Investments segment operating income?

**Reference answer:** Coca-Cola refranchised its bottling operations in the Philippines, Bangladesh and certain territories in India.

**Evidence:** Bottling Investments' operating income for the years ended December 31, 2025 and 2024 was $426 million and $496 million, respectively. The decrease in operating income was primarily driven by the impact of refranchising our bottling operations in the Philippines, Bangladesh and certain territories in India, higher commodity costs and an unfavorable foreign currency exchange rate impact of 2%, partially offset by favorable pricing initiatives and lower operating expenses.

**Response:**

> According to the FY2025 10-K, the Bottling Investments operating income decrease was driven in part by the impact of refranchising bottling operations in the Philippines, Bangladesh and certain territories in India [C1]. The refranchising in the Philippines and Bangladesh occurred in February 2024, and the India refranchisings occurred in January, February and December 2024, plus May 2025 [C4]. The Philippines refranchising was to CCEP and a local business partner [C7].

**Your verdict:** PASS - Extra refranchising dates/CCEP detail beyond evidence, no contradiction.

## cal-27
**Question:** In its fiscal year 2024 10-K risk factors, which acquisition does Exxon Mobil specifically name when discussing its ability to integrate and achieve anticipated synergies as part of operational efficiency?

**Reference answer:** Exxon Mobil specifically names the acquisition of Pioneer.

**Evidence:** Operational efficiency. || An important component of ExxonMobil's competitive performance, especially given the commodity-based nature of many of our businesses, is our ability to operate efficiently, including our ability to manage expenses, improve production || yields on an ongoing basis and successfully integrate and achieve the anticipated synergies of acquisitions, including the acquisition of Pioneer.

**Response:**

> In the fiscal year 2024 10-K, the operational efficiency risk factor names **the acquisition of Pioneer (Pioneer Natural Resources Company)**. It says ExxonMobil's competitive performance depends on its ability to "successfully integrate and achieve the anticipated synergies of acquisitions, including the acquisition of Pioneer."
> 
> The deal closed on May 3, 2024. ExxonMobil issued 545 million shares worth $63 billion and assumed $5 billion of debt. The company says the acquisition creates an industry-leading U.S. unconventional inventory position.

**Your verdict:** PASS - Extra deal details look right.

## cal-28
**Question:** According to Apple's fiscal year 2023 10-K, what primarily drove the year-over-year growth in research and development expense in fiscal year 2023?

**Reference answer:** The growth in R&D expense in fiscal year 2023 was driven primarily by increases in headcount-related expenses.

**Evidence:** Research and Development The year-over-year growth in R&D expense in 2023 was driven primarily by increases in headcount-related expenses.

**Response:**

> According to Apple's FY2023 10-K, the year-over-year growth in research and development expense in 2023 was driven primarily by increases in headcount-related expenses. R&D expense rose 14%, from $26,251 million in 2022 to $29,915 million in 2023.

**Your verdict:** PASS

## cal-29
**Question:** What was NVIDIA's overall employee turnover rate in fiscal year 2024?

**Reference answer:** NVIDIA's overall turnover rate in fiscal year 2024 was 2.7%.

**Evidence:** In fiscal year 2024, our overall turnover rate was 2.7%.

**Response:**

> NVIDIA's overall employee turnover rate in fiscal year 2024 was **2.7%**.

**Your verdict:** PASS

## cal-30
**Question:** In its fiscal year 2025 Form 10-K risk factors, which recently acquired UnitedHealth Group business does the company cite as having been subject to a cyberattack in 2024?

**Reference answer:** Change Healthcare, which UnitedHealth Group had recently acquired, was hit by a cyberattack in 2024. The data involved contained protected health information or personally identifiable information.

**Evidence:** For example, we previously reported that our Change Healthcare business, which we had recently acquired, was subject to a cyberattack in 2024, in which the data involved contained protected health information or personally identifiable information.

**Response:**

> **The provided context does not name the business.** The UnitedHealth Group excerpt starts mid-sentence ("...attack in 2024, in which the data involved contained protected health information or personally identifiable information"), so the name of the business falls in the cut-off text.
> 
> What the excerpt does show:
> - The 2024 attack involved protected health information or personally identifiable information.
> - UnitedHealth notes "heightened vulnerabilities due to recently-acquired or non-integrated businesses," both in the past and possibly in the future.
> 
> From outside knowledge (not stated in the context), the business is almost certainly **Change Healthcare**. UnitedHealth's Optum acquired it in October 2022, and it suffered a major ransomware attack in February 2024 that exposed large amounts of health data.
> 
> Note that the VIZIO acquisition in the context belongs to Walmart's filing, not UnitedHealth's. The Activision Blizzard and Nuance acquisitions and the nation-state email attack belong to Microsoft's filings.

**Your verdict:** FAIL - Says the context doesn't name the business, then offers Change Healthcare as an outside-knowledge guess; evidence names it directly.
