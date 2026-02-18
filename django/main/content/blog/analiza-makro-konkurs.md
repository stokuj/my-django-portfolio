# Tax Burden Distribution Analysis - Competition Project

## Project Overview

This project was prepared for an analytical competition.
The analysis focuses on the distribution of tax burdens in the fictional country **Fiskalia**, based on micro-level tax data.

The main goal is to examine how different income sources and tax regimes affect redistribution outcomes.

## Scope of Analysis

- Government revenue calculations for three tax types: progressive PIT, flat PIT, and capital gains tax.
- Redistribution analysis using empirical/theoretical tax wedge charts, effective tax rates by income decile, and progressivity assessment.
- Two reform scenarios (rate change and allowance plus threshold change), including effects on budget revenue and social groups.

## Tech Stack

- Language: `R`
- Libraries: `dplyr`, `ggplot2`, `gridExtra`, `kableExtra`, `bookdown`
- Report format: `RMarkdown -> PDF`

## Project Structure

```text
data.csv                                      # Input dataset
analiza.Rmd                                   # Main analysis report (RMarkdown)
analiza.pdf                                   # Rendered PDF report
bibliografia.bib                              # Bibliography
Załącznik_nr_2...                             # Competition task statement
```

## How to Run

From RStudio or the R console:

```r
rmarkdown::render("analiza.Rmd")
```

## License

This project is licensed under the MIT License. See `LICENSE` for details.

## Note

This is an educational project. Data and scenarios are fictional.
