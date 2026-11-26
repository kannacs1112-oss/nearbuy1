# NEARBUY — Working Software Demo Checklist

## Before presenting
- [ ] Run the latest source build on the actual presentation computer.
- [ ] Create the administrator through the first-run setup page.
- [ ] Use fictional/demo accounts and label demo data clearly.
- [ ] Approve the sample merchant shop in Admin.
- [ ] Create a merchant account and add at least three products with different stock levels.
- [ ] Create a customer account and place one demo order.
- [ ] Confirm order placement reduces stock.
- [ ] Open Merchant Dashboard → Manage Shop → Retail Intelligence.
- [ ] Show the 30-day order-history calculations and explain that they are rules-based.
- [ ] Restart the app and verify data persists.
- [ ] Keep a backup of the data folder and the source archive.

- [ ] Run `python -m pytest -q tests` on the presentation machine and keep the output.
- [ ] Confirm the Hindi and Tamil translations have been reviewed, or label them as unreviewed in the presentation.

## Suggested international demo (optional extra minute)
1. Switch the footer language to Hindi and back; the choice is remembered on refresh.
2. Register a merchant, choose the United States as the country, and show that the currency becomes USD and the time zone becomes America/New_York.
3. Add a USD product to a cart next to an Indian rupee cart: the cart shows one total per currency, never a mixed total.
4. In the admin console, show delivered value listed per currency.

## Suggested 3-minute demo
1. Customer discovers a nearby shop and checks listed availability.
2. Customer adds a product to cart and places a clearly labelled demo order.
3. Merchant sees the incoming order and updates its status.
4. Merchant opens Retail Intelligence and sees recorded units sold, stock cover and reorder suggestion.
5. Admin sees shops, users, products and order activity.

## Be transparent
- Keyword search is not generative AI.
- Retail intelligence uses simple calculations over local order history; it is not a trained predictive model.
- Checkout is simulated / cash-on-delivery demo flow; no payment gateway or real payment processing is integrated.
- Prices are in each shop's own currency. No exchange rates are applied and no tax is calculated.
- Translations are provisional until reviewed by native speakers.
- This build is local-first and single-computer. Separate computers do not synchronize automatically.
- Demo shops and transactions are fictional. Do not present them as traction.
