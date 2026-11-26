# NEARBUY — Founding Plan (Working Draft)

**Company concept:** NEARBUY Commerce Intelligence Network  
**Stage:** Prototype / pre-validation  
**Initial market:** One local pilot area in India  
**Founder:** To be completed by founder  
**Brand/legal status:** Working name only; trademark, company-name and domain availability have not been verified.

## 1. Mission

Make practical digital commerce and inventory intelligence accessible to independent retailers, while helping customers discover products that are genuinely available in nearby shops.

## 2. Problem hypothesis

Independent retailers may have limited digital reach and fragmented tools for catalogues, stock and orders. Customers may struggle to discover nearby sellers and verify availability. These are hypotheses to validate through retailer interviews and a measurable pilot, not claims that every retailer has the same problem.

## 3. Initial solution

NEARBUY combines:
- A customer-facing local shop and product discovery experience.
- A merchant catalogue and order workspace.
- Stock availability shown from merchant-entered inventory.
- A rules-based retail intelligence screen using recent order history to estimate sales velocity, stock cover and a suggested 14-day replenishment quantity.

The current prototype's discovery is keyword-based, not generative AI. The retail insights are transparent calculations, not machine-learning forecasts.

## 4. Target users

**Primary:** Independent retailers and neighbourhood shops that want a simple digital storefront and basic stock/order visibility.

**Secondary:** Customers who prefer to discover and buy from nearby businesses.

**Initial wedge:** Recruit a small group of retailers in one locality and prove that the merchant workflow is useful before broadening the marketplace.

## 5. Value proposition

For merchants: one simple workspace to list products, receive orders and turn order history into practical stock actions.

For customers: discover nearby stores and see the stock quantity reported by each participating merchant.

## 6. Business model hypotheses

Test willingness to pay before setting prices:
1. Free pilot tier to reduce onboarding friction.
2. Paid merchant subscription for advanced catalogue, reporting and multi-user features.
3. Optional transaction or fulfilment fee only where the platform provides measurable value and applicable laws/contracts permit it.
4. Larger retailer integrations as a later enterprise offering.

## 7. Pilot scorecard

Suggested first pilot targets (targets, not current achievements):
- 10 participating shops.
- 100 registered customers.
- 200 active product listings.
- 50 completed test orders.
- Weekly stock accuracy checks with participating merchants.

Track active merchants, catalogue completeness, stock mismatch rate, order completion, repeat purchase, merchant retention and willingness to pay. Report the actual sample size and measurement period.

## 8. Competitive positioning

Do not position NEARBUY as another Amazon or instant-delivery clone. Test the narrower proposition: a practical inventory and operations layer for independent retailers, with customer discovery as the demand channel. Compare against local marketplaces, POS/inventory tools, social selling and open commerce networks during customer discovery.

## 9. Trust and safeguards

- Merchants are responsible for keeping their listed stock accurate.
- Do not promise guaranteed availability or delivery times until operationally measured.
- Do not collect card data in the prototype; checkout is a demo/cash-on-delivery flow and no payment gateway is integrated.
- Before public launch, implement HTTPS, email/phone verification, rate limiting, formal database migrations, audit logs, automated backups, privacy policy, terms, consent and applicable tax/consumer compliance.
- Use synthetic demo records only in public presentations unless real users have given informed permission.

## 9a. International readiness (v3.0.0)

The software now supports several languages, countries, currencies and time zones. Being able to *run* in another country is not the same as being ready to *operate* there. Before a non-pilot launch in a new country, confirm:
- Native-speaker review of the locale file for that language (`locales/*.json`).
- A payment provider that operates there, with the currency and refund rules it needs.
- Local tax rules for the goods sold (for example VAT, GST or sales tax) and invoice requirements.
- Local consumer-protection, data-protection and privacy requirements, and a terms-of-service page in the right language.
- Local delivery partners or a clear statement that delivery is the merchant's responsibility.

Pricing is per shop in the shop's own currency. The platform does not convert currencies or hold exchange rates; this is deliberate until a payment and FX partner is chosen.

## 10. 24-hour build and demo plan

1. Install and launch from source on the target Windows machine.
2. Create the founder/admin account using first-run setup.
3. Register a test merchant, approve the shop, add products and stock.
4. Register a test customer, place a demo order and verify stock decrement.
5. Open merchant Retail Intelligence; show sales velocity, stock cover and restock suggestion after the order exists.
6. Verify role restrictions, logout/login and persistence after restart.
7. Capture screenshots and a short screen recording; clearly label demo data and unconnected integrations.
8. Keep a clean backup of the database and source ZIP.

## 11. Immediate roadmap

**Now:** Reliable single-machine demo, merchant insights, transparent product claims and a polished workflow.

**Next:** Pilot interviews, stock accuracy process, multi-shop checkout, payment provider selection, notifications, tests and formal migrations.

**Later:** Cloud multi-tenant deployment, secure APIs, multi-location inventory, integrations, localized currencies/taxes/languages and country-by-country compliance review.

## 12. Founder decisions still required

- Final legal entity name and jurisdiction.
- Founder/co-founder roles and ownership.
- First pilot locality and merchant segment.
- Whether the long-term product is SaaS, marketplace, network infrastructure or a combination.
- Pricing validated through merchant interviews.
