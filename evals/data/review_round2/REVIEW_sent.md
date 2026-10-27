# Eval set review - round 2

Only items that are new or changed since round 1 are listed. 88 items are unchanged and keep their round-1 verdict.
Write OK or the problem after each **Review:** line.

## New text items (replacements for dropped ones) (4)

### text-0037 (factual_text, test)
**Q:** According to Amazon's fiscal year 2025 MD&A, what primarily drove AWS sales growth in 2025, and what partially offset it?
**A:** AWS sales grew 20% in 2025, driven primarily by increased customer usage. This was partially offset by pricing changes, mainly from long-term customer contracts.
**Expected:** answer
**Evidence:** AWS sales increased 20% in 2025, compared to the prior year. The sales growth primarily reflects increased customer usage, partially offset by pricing changes primarily driven by long-term customer contracts.
**Review:** 

### text-0038 (factual_text, test)
**Q:** According to Johnson & Johnson's fiscal year 2024 10-K, what percentage of the company's total revenues did STELARA account for in fiscal 2024, and what does the company expect to affect STELARA sales in 2025?
**A:** STELARA (ustekinumab), J&J's second largest product, accounted for approximately 11.7% of total revenues in fiscal 2024. The company expects continued launches of biosimilar versions in Europe and the U.S. in 2025 to impact its sales.
**Expected:** answer
**Evidence:** Sales of the Company's second largest product, STELARA (ustekinumab) accounted for approximately 11.7% of the Company's total revenues for fiscal 2024. || According to patent settlement and license agreements, the Company expects continued launches of biosimilar versions of STELARA in Europe and the United States in 2025 which will impact the Company's sales of STELARA.
**Review:** 

### text-0039 (factual_text, dev)
**Q:** In which U.S. court did trade organizations led by the Mississippi Bankers Association file their December 2024 action challenging the CFPB Overdraft Rule, as described in JPMorgan Chase's fiscal year 2024 10-K?
**A:** The United States District Court for the Southern District of Mississippi. The action seeks a preliminary injunction to stay the rule's October 1, 2025 effective date.
**Expected:** answer
**Evidence:** CFPB Overdraft Rule || : An action filed by trade organizations led by the Mississippi Bankers Association against the CFPB in the United States District Court for the Southern District of Mississippi in December 2024 seeks a preliminary injunction to stay the October 1, 2025 effective date of this rule.
**Review:** 

### text-0040 (factual_text, dev)
**Q:** In fiscal year 2025, which countries' bottling operations did Coca-Cola refranchise, contributing to the decrease in its Bottling Investments segment operating income?
**A:** Coca-Cola refranchised its bottling operations in the Philippines, Bangladesh and certain territories in India.
**Expected:** answer
**Evidence:** Bottling Investments' operating income for the years ended December 31, 2025 and 2024 was $426 million and $496 million, respectively. The decrease in operating income was primarily driven by the impact of refranchising our bottling operations in the Philippines, Bangladesh and certain territories in India, higher commodity costs and an unfavorable foreign currency exchange rate impact of 2%, partially offset by favorable pricing initiatives and lower operating expenses.
**Review:** 

## Text items with re-extracted evidence (21)

### text-0001 (factual_text, dev)
**Q:** According to Apple's fiscal year 2023 Form 10-K, by when is Apple required to comply with the EU Digital Markets Act, which may force changes to its App Store?
**A:** Apple states it is required to comply with the EU Digital Markets Act by March 2024.
**Expected:** answer
**Evidence:** The Company expects to make further business changes in the future, including as a result of legislative initiatives impacting the App Store, such as the EU Digital Markets Act, which the Company is required to comply with by March 2024, or similar laws in other jurisdictions. || Apple Inc. | 2023 Form 10-K | 13
**Review:** 

### text-0003 (factual_text, dev)
**Was (text-0003):** According to Johnson & Johnson's fiscal year 2023 10-K, before what date does the company not anticipate the launch of a biosimilar version of STELARA in the United States?
**Q:** According to Johnson & Johnson's fiscal year 2023 10-K, what is the earliest date by which the company anticipates a biosimilar version of STELARA could launch in the United States?
**A:** Because of settlements and other agreements with third parties, Johnson & Johnson does not anticipate a U.S. biosimilar launch of STELARA before January 1, 2025.
**Expected:** answer
**Evidence:** As a result of settlements and other agreements with third parties, the Company does not anticipate the launch of a biosimilar version of STELARA before January 1, 2025 in the United States.
**Review:** 

### text-0004 (factual_text, dev)
**Q:** According to JPMorgan Chase's fiscal year 2025 10-K risk factors, what is the name of the intermediate holding company held by the Parent Company, and what must the Parent Company contribute to it?
**A:** The intermediate holding company is JPMorgan Chase Holdings LLC (the "IHC"), and the Parent Company must contribute to it substantially all the net proceeds it receives from securities issuances.
**Expected:** answer
**Evidence:** The Parent Company, JPMorgan Chase & Co., is a holding company that holds the stock of JPMorgan Chase Bank, N.A. and an intermediate holding company, JPMorgan Chase Holdings LLC (the "IHC"). || The Parent Company must contribute to the IHC substantially all the net proceeds that it receives from securities issuances.
**Review:** 

### text-0005 (factual_text, test)
**Q:** In Coca-Cola's fiscal year 2025 10-K risk factors, what chemical compound is identified as being formed during the manufacturing of certain types of caramel coloring used in cola-flavored beverages?
**A:** 4-methylimidazole (4-MEI), which forms during the manufacturing of certain types of caramel coloring used in cola-flavored beverages.
**Expected:** answer
**Evidence:** substances that are present in our beverage products naturally or that occur as a result of the manufacturing process, such as 4-methylimidazole (4-MEI), a chemical compound that is formed during the manufacturing of || certain types of caramel coloring used in cola-flavored beverages;
**Review:** 

### text-0006 (factual_text, dev)
**Q:** In fiscal year 2025, which two Microsoft businesses were combined into a single revenue growth metric as part of the metric updates tied to the segment changes?
**A:** Microsoft combined Windows OEM and Devices into a single revenue growth metric that brings together revenue from its PC market-driven businesses.
**Expected:** answer
**Evidence:** In the first quarter of fiscal year 2025, we made updates to our metrics in connection with the segment changes described above. || Other changes include combining Windows OEM and Devices into a single revenue growth metric that brings revenue from PC market-driven businesses together, as well as elevating our cloud revenue growth metrics to align to our strategic focus on cloud growth.
**Review:** 

### text-0010 (factual_text, dev)
**Q:** According to Apple's fiscal year 2023 10-K, what primarily drove the year-over-year growth in research and development expense in fiscal year 2023?
**A:** The growth in R&D expense in fiscal year 2023 was driven primarily by increases in headcount-related expenses.
**Expected:** answer
**Evidence:** Research and Development The year-over-year growth in R&D expense in 2023 was driven primarily by increases in headcount-related expenses.
**Review:** 

### text-0011 (factual_text, dev)
**Q:** In its fiscal year 2024 10-K risk factors, what position has the Indian tax authority asserted against Amazon, and how is Amazon responding?
**A:** The Indian tax authority has asserted that tax applies to cloud services fees paid to Amazon in the U.S., and Amazon is contesting this position.
**Expected:** answer
**Evidence:** For example, the Indian tax authority has asserted that tax applies to cloud services fees paid to Amazon in the U.S. || We are contesting this position; however, if this matter is adversely resolved, we may be required to pay additional amounts with respect to current and prior periods and our taxes in the future could increase.
**Review:** 

### text-0013 (factual_text, dev)
**Q:** In its fiscal year 2023 Form 10-K risk factors, what two channels does JPMorgan Chase identify through which climate change could manifest as a financial risk to the firm?
**A:** Climate change could manifest as a financial risk either through changes in the physical climate (physical risks) or from the process of transitioning to a low-carbon economy (transition risks).
**Expected:** answer
**Evidence:** Climate change could manifest as a financial risk to JPMorgan Chase either through changes in the physical climate or from the process of transitioning to a low-carbon economy. || Both physical risks and transition risks associated with climate change could have negative impacts on the financial condition or
**Review:** 

### text-0015 (factual_text, dev)
**Q:** In its fiscal year 2026 Form 10-K risk factors, which acquisition does Microsoft cite as an example of its acquisitions, and when was it completed?
**A:** Microsoft cites its acquisition of Activision Blizzard, Inc., which it completed in October 2023.
**Expected:** answer
**Evidence:** Acquisitions, joint ventures, and strategic alliances could have an adverse effect on our business. || We expect to continue making acquisitions and entering into joint ventures and strategic alliances as part of our long-term business strategy. For example, in October 2023 we completed our acquisition of Activision Blizzard, Inc.
**Review:** 

### text-0016 (factual_text, dev)
**Q:** What was the size of the charge associated with H20 excess inventory and purchase obligations that contributed to NVIDIA's gross margin decrease in fiscal year 2026?
**A:** NVIDIA recorded a $4.5 billion charge associated with H20 excess inventory and purchase obligations in fiscal year 2026.
**Expected:** answer
**Evidence:** Gross margin decreased in fiscal year 2026 as our business model transitioned from offering Hopper HGX systems to Blackwell full-scale datacenter solutions. || The gross margin decrease was also impacted by a $4.5 billion charge associated with H20 excess inventory and purchase obligations.
**Review:** 

### text-0018 (factual_text, dev)
**Q:** What long-term debt rating did Moody's Investors Service assign to Walmart as of January 31, 2024, as reported in Walmart's fiscal year 2024 10-K?
**A:** Moody's assigned Walmart's long-term debt a rating of Aa2 (and P-1 for commercial paper).
**Expected:** answer
**Evidence:** As of January 31, 2024, the ratings assigned to our commercial paper and rated series of our outstanding long-term debt were as follows: || Rating agency || Commercial paper || Long-term debt || Moody's Investors Service || P-1 || Aa2
**Review:** 

### text-0019 (factual_text, test)
**Q:** According to Apple's fiscal year 2024 Form 10-K, in which fiscal quarter has Apple historically experienced higher net sales, and why?
**A:** Apple has historically experienced higher net sales in its first fiscal quarter, due in part to seasonal holiday demand.
**Expected:** answer
**Evidence:** The Company has historically experienced higher net sales in its first quarter compared to other quarters in its fiscal year due in part to seasonal holiday demand. || Apple Inc. | 2024 Form 10-K | 15
**Review:** 

### text-0020 (factual_text, dev)
**Q:** In its fiscal year 2023 10-K risk factors, what program does Amazon describe under which it may reimburse customers when third-party sellers fail to deliver products or deliver products materially different from their descriptions?
**A:** The A-to-z Guarantee, under which Amazon may reimburse customers for payments up to certain limits; its cost will increase as third-party seller sales grow.
**Expected:** answer
**Evidence:** Under our seller programs, we maintain policies and processes designed to prevent sellers from collecting payments, fraudulently or otherwise, when buyers never receive the products they ordered or when the products received are materially different from the sellers' descriptions, and to prevent sellers in our stores or through other stores from selling unlawful, counterfeit, pirated, or stolen goods, selling goods in an unlawful or unethical manner, violating the proprietary rights of others, or otherwise violating our policies. || Under our A-to-z Guarantee, we may reimburse customers for payments up to certain limits in these situations, and as our third-party seller sales grow, the cost of this program will increase and could negatively affect our operating results.
**Review:** 

### text-0023 (factual_text, test)
**Q:** In its fiscal year 2024 10-K risk factors, what does Coca-Cola say data localization or residency laws require, and what cost impact does it identify from them?
**A:** Coca-Cola says these laws require certain data to be maintained, stored and/or processed within the country of origin, and that maintaining local data centers in individual countries could significantly increase its operating costs.
**Expected:** answer
**Evidence:** In addition, some countries are considering or have enacted data localization or residency laws, which require that certain data be maintained, stored and/or processed within their country of origin. || Maintaining local data centers in individual countries could increase our operating costs significantly.
**Review:** 

### text-0025 (factual_text, dev)
**Q:** According to NVIDIA's fiscal year 2025 10-K, how long is the delayed compliance period before the USG's "AI Diffusion" interim final rule imposes its worldwide licensing requirement, and on what date was the rule published?
**A:** The AI Diffusion IFR was published in the Federal Register on January 15, 2025. Its worldwide licensing requirement takes effect after a 120-day delayed compliance period, unless the rule is modified.
**Expected:** answer
**Evidence:** On January 15, 2025, the USG published the "AI Diffusion" IFR in the Federal Register. || After a 120-day delayed compliance period, the IFR will, unless modified, impose a worldwide licensing requirement on all products classified under Export Control Classification Numbers, or ECCNs, 3A090.a, 4A090.a, or corresponding.z ECCNs, including all related software and technology.
**Review:** 

### text-0026 (factual_text, dev)
**Q:** Under UnitedHealth Group's fiscal year 2024 10-K, what minimum CMS star rating must a Medicare Advantage plan have to qualify for quality bonus payments?
**A:** A Medicare Advantage plan must have a rating of four stars or higher to qualify for CMS quality bonus payments.
**Expected:** answer
**Evidence:** For example, as part of the ACA, CMS has a system providing various quality bonus payments to Medicare Advantage plans meeting specified quality star ratings at the individual plan or local contract level. || Plans must have a rating of four stars or higher to qualify for bonus payments, and CMS has and may make changes to the star rating program that impact the ability of plans to achieve four-star or higher ratings.
**Review:** 

### text-0027 (factual_text, dev)
**Q:** In its fiscal year 2024 10-K risk factors, which acquisition does Exxon Mobil specifically name when discussing its ability to integrate and achieve anticipated synergies as part of operational efficiency?
**A:** Exxon Mobil specifically names the acquisition of Pioneer.
**Expected:** answer
**Evidence:** Operational efficiency. || An important component of ExxonMobil's competitive performance, especially given the commodity-based nature of many of our businesses, is our ability to operate efficiently, including our ability to manage expenses, improve production || yields on an ongoing basis and successfully integrate and achieve the anticipated synergies of acquisitions, including the acquisition of Pioneer.
**Review:** 

### text-0030 (factual_text, dev)
**Q:** In fiscal year 2025, which constitutional amendments did Johnson & Johnson's subsidiary Janssen claim the IRA's Medicare Drug Price Negotiation Program violates in its litigation against HHS and CMS?
**A:** Janssen sought a declaration that the IRA violates its rights under the First Amendment and the Fifth Amendment to the Constitution.
**Expected:** answer
**Evidence:** In July 2023, Janssen Pharmaceuticals, Inc. (Janssen) filed litigation against the U.S. Department of Health and Human Services as well as the Centers for Medicare and Medicaid Services challenging the constitutionality of the IRA's Medicare Drug Price Negotiation Program. || The litigation requests a declaration that the IRA violates Janssen's rights under the First Amendment and the Fifth Amendment to the Constitution and therefore that Janssen is not subject to the IRA's mandatory pricing scheme.
**Review:** 

### text-0031 (factual_text, dev)
**Q:** In how many countries were JPMorgan Chase's employees located as of the end of fiscal year 2023, and what percentage of its employees were based in the U.S.?
**A:** As of December 31, 2023, JPMorgan Chase's employees were located in 65 countries, with 60% of them located in the U.S.
**Expected:** answer
**Evidence:** As of December 31, 2023, JPMorgan Chase had 309,926 employees globally, an increase of 16,203 employees from the prior year. || The Firm's employees are located in 65 countries, with 60% of the Firm's employees located in the U.S.
**Review:** 

### text-0032 (factual_text, dev)
**Q:** In fiscal year 2024, how much did Coca-Cola record in other operating charges related to the impairment of its BodyArmor trademark?
**A:** Coca-Cola recorded $760 million of other operating charges in 2024 for the impairment of its BodyArmor trademark.
**Expected:** answer
**Evidence:** In 2024, the Company recorded other operating charges of $4,163 million. These charges consisted of $3,109 million related to the remeasurement of our contingent consideration liability to fair value in conjunction with our acquisition of fairlife in 2020, $760 million related to the impairment of our BodyArmor trademark, $133 million related to the Company's productivity and reinvestment program and $126 million related to the impairment of a trademark in Latin America.
**Review:** 

### text-0033 (factual_text, test)
**Q:** In Microsoft's fiscal year 2026 MD&A, what drove the 29% decline in XBOX hardware revenue?
**A:** XBOX hardware revenue decreased 29% driven by a lower volume of consoles sold.
**Expected:** answer
**Evidence:** Fiscal Year 2026 Compared with Fiscal Year 2025 || XBOX hardware revenue decreased 29% driven by lower volume of consoles sold.
**Review:** 

## Template rewording, code-generated items (37)

Systematic wording changes from round-1 feedback (net income 'attributable to', XOM/JPM
revenue labels, fiscal year-end dates in comparisons). Skim; answers are unchanged.

- num-0003: What was net income attributable to Johnson & Johnson for fiscal year 2023?
- num-0012: What was net income attributable to Amazon for fiscal year 2024?
- num-0014: What was net income attributable to JPMorgan Chase for fiscal year 2023?
- num-0020: What was net income attributable to Exxon Mobil for fiscal year 2024?
- num-0031: What was net income attributable to Apple for fiscal year 2025?
- num-0039: What was net income attributable to Walmart for fiscal year 2026?
- num-0040: What were Exxon Mobil's total revenues and other income for fiscal year 2023?
- num-0045: What was net income attributable to Coca-Cola for fiscal year 2023?
- calc-0003: By what percentage did Exxon Mobil's total revenues and other income change from fiscal year 2023 to fiscal year 2024?
- calc-0005: By what percentage did net income attributable to Coca-Cola change from fiscal year 2023 to fiscal year 2024?
- calc-0006: By what percentage did net income attributable to JPMorgan Chase change from fiscal year 2024 to fiscal year 2025?
- calc-0010: By what percentage did net income attributable to Johnson & Johnson change from fiscal year 2023 to fiscal year 2024?
- calc-0011: What was Exxon Mobil's net profit margin (net income attributable to Exxon Mobil as a percentage of total revenues and other income) for fiscal year 2025?
- calc-0012: What was Coca-Cola's net profit margin (net income attributable to Coca-Cola as a percentage of total revenue) for fiscal year 2024?
- calc-0013: What was Johnson & Johnson's net profit margin (net income attributable to Johnson & Johnson as a percentage of total revenue) for fiscal year 2024?
- calc-0014: What was Amazon's net profit margin (net income attributable to Amazon as a percentage of total revenue) for fiscal year 2023?
- calc-0015: What was JPMorgan Chase's net profit margin (net income attributable to JPMorgan Chase as a percentage of total net revenue) for fiscal year 2023?
- calc-0016: What was Walmart's net profit margin (net income attributable to Walmart as a percentage of total revenue) for fiscal year 2025?
- calc-0017: What was Microsoft's net profit margin (net income attributable to Microsoft as a percentage of total revenue) for fiscal year 2024?
- calc-0018: What was NVIDIA's net profit margin (net income attributable to NVIDIA as a percentage of total revenue) for fiscal year 2026?
- calc-0019: What was UnitedHealth Group's net profit margin (net income attributable to UnitedHealth Group as a percentage of total revenue) for fiscal year 2025?
- calc-0020: What was Apple's net profit margin (net income attributable to Apple as a percentage of total revenue) for fiscal year 2025?
- comp-0001: Which company reported higher total revenue for its fiscal year 2025: Walmart (fiscal year ended January 31, 2025) or NVIDIA (fiscal year ended January 26, 2025)?
- comp-0002: Which company reported higher total assets for its fiscal year 2024: Exxon Mobil (fiscal year ended December 31, 2024) or JPMorgan Chase (fiscal year ended December 31, 2024)?
- comp-0003: Which company reported higher total assets for its fiscal year 2024: Microsoft (fiscal year ended June 30, 2024) or Coca-Cola (fiscal year ended December 31, 2024)?
- comp-0004: Which company reported higher total revenue for its fiscal year 2024: Coca-Cola (fiscal year ended December 31, 2024) or Johnson & Johnson (fiscal year ended December 29, 2024)?
- comp-0005: Which company reported higher total assets for its fiscal year 2023: JPMorgan Chase (fiscal year ended December 31, 2023) or Amazon (fiscal year ended December 31, 2023)?
- comp-0006: Which company reported higher net cash provided by operating activities for its fiscal year 2025: Walmart (fiscal year ended January 31, 2025) or Exxon Mobil (fiscal year ended December 31, 2025)?
- comp-0007: Which company reported higher net income attributable to each company for its fiscal year 2026: Microsoft (fiscal year ended June 30, 2026) or Walmart (fiscal year ended January 31, 2026)?
- comp-0008: Which company reported higher net income attributable to each company for its fiscal year 2025: UnitedHealth Group (fiscal year ended December 31, 2025) or Walmart (fiscal year ended January 31, 2025)?
- comp-0009: Which company reported higher net income attributable to each company for its fiscal year 2025: Walmart (fiscal year ended January 31, 2025) or Apple (fiscal year ended September 27, 2025)?
- comp-0010: Which company reported higher research and development expense for its fiscal year 2024: Exxon Mobil (fiscal year ended December 31, 2024) or NVIDIA (fiscal year ended January 28, 2024)?
- comp-0011: Which company reported higher net income attributable to each company for its fiscal year 2024: UnitedHealth Group (fiscal year ended December 31, 2024) or JPMorgan Chase (fiscal year ended December 31, 2024)?
- comp-0012: Which company reported higher total assets for its fiscal year 2024: Coca-Cola (fiscal year ended December 31, 2024) or Walmart (fiscal year ended January 31, 2024)?
- comp-0013: Which company reported higher net cash provided by operating activities for its fiscal year 2024: Johnson & Johnson (fiscal year ended December 29, 2024) or Coca-Cola (fiscal year ended December 31, 2024)?
- comp-0014: Which company reported higher total assets for its fiscal year 2025: Coca-Cola (fiscal year ended December 31, 2025) or Amazon (fiscal year ended December 31, 2025)?
- comp-0015: Which company reported higher net cash provided by operating activities for its fiscal year 2024: Exxon Mobil (fiscal year ended December 31, 2024) or Walmart (fiscal year ended January 31, 2024)?
