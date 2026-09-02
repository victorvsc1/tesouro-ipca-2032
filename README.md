# Tesouro IPCA+ 2032 → Portfolio Performance

A small GitHub Actions feed that downloads the Tesouro Transparente Tesouro Direto CSV, selects **Tesouro IPCA+ 2032 without semiannual coupons**, and publishes a compact JSON quote history for Portfolio Performance.

## Setup

1. Create a new GitHub repository, e.g. `tesouro-ipca-2032`.
2. Copy all files from this repository into it and push them.
3. GitHub Actions will run on weekdays and update `data/ipca-2032.json`.
4. In Portfolio Performance, configure a **JSON Quote Feed** using:

   `https://raw.githubusercontent.com/YOUR_GITHUB_USER/tesouro-ipca-2032/main/data/ipca-2032.json`

   Date JSONPath: `$[*].date`

   Close JSONPath: `$[*].close`

You can also trigger the workflow manually from **Actions → Update Tesouro IPCA+ 2032 → Run workflow**.

## Selection

The script requires maturity `15/08/2032`, requires an IPCA title, and explicitly excludes titles containing `Juros Semestrais`. It therefore targets the zero-coupon **Tesouro IPCA+ 2032**, not the coupon-bearing 2032 security.

The output uses the Treasury CSV's `PU Compra` as the quote, falling back to `PU Venda` if necessary.

## Source

Tesouro Transparente dataset:
https://www.tesourotransparente.gov.br/ckan/dataset/taxas-dos-titulos-ofertados-pelo-tesouro-direto

The workflow is intentionally simple and does not require a server or database.
