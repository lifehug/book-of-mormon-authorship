# Chronicling America: downloading the bulk OCR batches by hand (BOM-10)

**Owner action.** Claude cannot do this part. Say "walk me through the bulk download" at your
desk and this file is the walkthrough.

## Why by hand

The per-page API route is `ingest.chronicling_america pull`, which asks the Library of
Congress's text service for one page at a time. It works, but their service is throwing HTTP
500s: 96% of pages eventually succeed, each after retries, so throughput collapsed to about
0.5 pages a minute. All 159,146 pages would take roughly 219 days.

The same OCR is published in bulk as batch tarballs, and all 159,146 pages we need sit in just
**76 batches**, about 59 GB compressed. That is hours, not months.

Scripted downloads of those tarballs are blocked by Cloudflare: the request returns a "Just a
moment..." HTML challenge instead of the file. A real browser passes that check, so a person
can download them even though the fetcher cannot. (Claude also tripped a 429 rate limit on
2026-10-16 by sizing all 76 files eight at a time. Do not request these in parallel. Two or
three at a time from a browser is fine.)

Nothing here is a workaround of a restriction: the Library of Congress publishes these files
specifically for text and data mining. The block is on automation, not on the use.

## Where to save them

```
/Volumes/bomdata/incoming/chronam
```

Already created, on the external SSD, 1.7 TB free. Point the browser's download folder there,
or drag the files across afterwards.

## What to do

1. Download the batches from the table below, **most valuable first**. Two or three at a time.
2. You do not need all 76. The table has a running total; the top 10 are about 9 GB and cover
   44% of the pages, the top 25 cover 77%.
3. A Cloudflare spinner before the download starts is expected. An error *page* instead of a
   file is not: stop and say so, because then the route is closed to people too and the next
   step is emailing the Library of Congress rather than clicking more.
4. Tell Claude as soon as **one** file has finished; no need to wait for the rest. Claude then
   verifies it against the `sha256` the portal publishes, extracts only the pages in
   `data/catalog/chronicling_america.jsonl.gz`, checks the extracted text against pages already
   fetched through the API (so we know the bulk OCR is the same text), writes the manifest, and
   deletes the tarball before moving to the next.

Portal, if you would rather browse than use direct links:
https://www.loc.gov/collections/chronicling-america/datasets/

## Stopping points

| Download | Pages covered | Rough size |
| --- | --- | --- |
| top 10 batches | 70,273 (44.2%) | ~8 GB |
| top 25 batches | 122,126 (76.7%) | ~29 GB |
| top 50 batches | 151,441 (95.2%) | ~46 GB |
| top 76 batches | 159,146 (100.0%) | ~59 GB |

## The batches

Sorted by how many of our pages each one yields. Sizes known for 71 of 76.

| # | Batch | Pages | Cumulative | % | Size | Link |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 | `vi_flyingsquirrels_ver03` | 10,096 | 10,096 | 6.3% | 0.74 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/vi_flyingsquirrels_ver03.tar.bz2) |
| 2 | `vi_greenjackets_ver02` | 8,513 | 18,609 | 11.7% | 0.81 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/vi_greenjackets_ver02.tar.bz2) |
| 3 | `vi_alpina_ver01` | 8,172 | 26,781 | 16.8% | 0.96 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/vi_alpina_ver01.tar.bz2) |
| 4 | `dlc_eel_ver01` | 7,945 | 34,726 | 21.8% | 1.23 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/dlc_eel_ver01.tar.bz2) |
| 5 | `vi_naturals_ver01` | 6,879 | 41,605 | 26.1% | ? | [download](https://chroniclingamerica.loc.gov/data/ocr/vi_naturals_ver01.tar.bz2) |
| 6 | `vi_hops_ver01` | 6,763 | 48,368 | 30.4% | 0.80 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/vi_hops_ver01.tar.bz2) |
| 7 | `nhd_avalon_ver02` | 6,457 | 54,825 | 34.4% | 1.02 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/nhd_avalon_ver02.tar.bz2) |
| 8 | `deu_kedavra_ver01` | 5,303 | 60,128 | 37.8% | 0.85 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/deu_kedavra_ver01.tar.bz2) |
| 9 | `rp_beholder_ver02` | 5,156 | 65,284 | 41.0% | 0.96 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/rp_beholder_ver02.tar.bz2) |
| 10 | `dlc_doctorteeth_ver01` | 4,989 | 70,273 | 44.2% | 1.13 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/dlc_doctorteeth_ver01.tar.bz2) |
| 11 | `vi_otters_ver02` | 4,939 | 75,212 | 47.3% | 1.10 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/vi_otters_ver02.tar.bz2) |
| 12 | `vi_mudhens_ver02` | 4,849 | 80,061 | 50.3% | 1.07 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/vi_mudhens_ver02.tar.bz2) |
| 13 | `dlc_camilla_ver01` | 4,669 | 84,730 | 53.2% | 1.41 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/dlc_camilla_ver01.tar.bz2) |
| 14 | `rp_gorgon_ver01` | 4,625 | 89,355 | 56.1% | 0.90 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/rp_gorgon_ver01.tar.bz2) |
| 15 | `vi_loons_ver01` | 4,519 | 93,874 | 59.0% | 0.93 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/vi_loons_ver01.tar.bz2) |
| 16 | `vi_isotopes_ver01` | 4,130 | 98,004 | 61.6% | 1.12 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/vi_isotopes_ver01.tar.bz2) |
| 17 | `vi_dartmoor_ver03` | 3,438 | 101,442 | 63.7% | 2.12 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/vi_dartmoor_ver03.tar.bz2) |
| 18 | `rp_froghemoth_ver01` | 3,420 | 104,862 | 65.9% | 1.22 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/rp_froghemoth_ver01.tar.bz2) |
| 19 | `nhd_eider_ver01` | 3,295 | 108,157 | 68.0% | 0.55 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/nhd_eider_ver01.tar.bz2) |
| 20 | `kyu_collie_ver01` | 2,763 | 110,920 | 69.7% | 0.95 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/kyu_collie_ver01.tar.bz2) |
| 21 | `vi_appaloosa_ver01` | 2,580 | 113,500 | 71.3% | 3.38 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/vi_appaloosa_ver01.tar.bz2) |
| 22 | `wvu_boros_ver02` | 2,377 | 115,877 | 72.8% | 1.53 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/wvu_boros_ver02.tar.bz2) |
| 23 | `me_calais_ver03` | 2,253 | 118,130 | 74.2% | 1.62 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/me_calais_ver03.tar.bz2) |
| 24 | `dlc_animal_ver02` | 2,168 | 120,298 | 75.6% | 0.58 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/dlc_animal_ver02.tar.bz2) |
| 25 | `ohi_errol_ver01` | 1,828 | 122,126 | 76.7% | 1.73 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/ohi_errol_ver01.tar.bz2) |
| 26 | `me_bangor_ver02` | 1,792 | 123,918 | 77.9% | 1.04 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/me_bangor_ver02.tar.bz2) |
| 27 | `rp_invisiblestalker_ver01` | 1,682 | 125,600 | 78.9% | 0.49 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/rp_invisiblestalker_ver01.tar.bz2) |
| 28 | `mb_circe_ver01` | 1,524 | 127,124 | 79.9% | 1.31 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/mb_circe_ver01.tar.bz2) |
| 29 | `nhd_hale_ver01` | 1,500 | 128,624 | 80.8% | 1.28 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/nhd_hale_ver01.tar.bz2) |
| 30 | `rp_azer_ver02` | 1,499 | 130,123 | 81.8% | ? | [download](https://chroniclingamerica.loc.gov/data/ocr/rp_azer_ver02.tar.bz2) |
| 31 | `kyu_dachshund_ver04` | 1,470 | 131,593 | 82.7% | 0.77 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/kyu_dachshund_ver04.tar.bz2) |
| 32 | `arhi_epidote_ver01` | 1,378 | 132,971 | 83.6% | 0.86 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/arhi_epidote_ver01.tar.bz2) |
| 33 | `iune_bismuth_ver01` | 1,282 | 134,253 | 84.4% | 0.61 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/iune_bismuth_ver01.tar.bz2) |
| 34 | `dlc_chartreux_ver01` | 1,244 | 135,497 | 85.1% | 0.12 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/dlc_chartreux_ver01.tar.bz2) |
| 35 | `dlc_beaker_ver01` | 1,242 | 136,739 | 85.9% | 0.92 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/dlc_beaker_ver01.tar.bz2) |
| 36 | `dlc_domestic_ver01` | 1,234 | 137,973 | 86.7% | 0.13 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/dlc_domestic_ver01.tar.bz2) |
| 37 | `dlc_forest_ver01` | 1,228 | 139,201 | 87.5% | 0.10 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/dlc_forest_ver01.tar.bz2) |
| 38 | `dlc_exotic_ver01` | 1,196 | 140,397 | 88.2% | 0.12 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/dlc_exotic_ver01.tar.bz2) |
| 39 | `rp_jarlstorvald_ver01` | 1,186 | 141,583 | 89.0% | 1.02 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/rp_jarlstorvald_ver01.tar.bz2) |
| 40 | `me_indianisland_ver01` | 1,103 | 142,686 | 89.7% | 1.40 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/me_indianisland_ver01.tar.bz2) |
| 41 | `wvu_hogan_ver01` | 1,086 | 143,772 | 90.3% | 0.00 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/wvu_hogan_ver01.tar.bz2) |
| 42 | `ncu_apple_ver01` | 981 | 144,753 | 91.0% | 1.19 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/ncu_apple_ver01.tar.bz2) |
| 43 | `wvu_moore_ver01` | 960 | 145,713 | 91.6% | 1.27 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/wvu_moore_ver01.tar.bz2) |
| 44 | `arhi_fluorite_ver01` | 934 | 146,647 | 92.1% | 1.68 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/arhi_fluorite_ver01.tar.bz2) |
| 45 | `ct_barnum_ver01` | 932 | 147,579 | 92.7% | 1.19 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/ct_barnum_ver01.tar.bz2) |
| 46 | `mb_artemis_ver01` | 876 | 148,455 | 93.3% | 1.37 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/mb_artemis_ver01.tar.bz2) |
| 47 | `dlc_buford_ver01` | 864 | 149,319 | 93.8% | ? | [download](https://chroniclingamerica.loc.gov/data/ocr/dlc_buford_ver01.tar.bz2) |
| 48 | `wvu_palmer_ver02` | 724 | 150,043 | 94.3% | 0.04 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/wvu_palmer_ver02.tar.bz2) |
| 49 | `rp_hobgoblin_ver02` | 699 | 150,742 | 94.7% | 0.44 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/rp_hobgoblin_ver02.tar.bz2) |
| 50 | `vi_eterna_ver01` | 699 | 151,441 | 95.2% | ? | [download](https://chroniclingamerica.loc.gov/data/ocr/vi_eterna_ver01.tar.bz2) |
| 51 | `ohi_cedric_ver01` | 689 | 152,130 | 95.6% | ? | [download](https://chroniclingamerica.loc.gov/data/ocr/ohi_cedric_ver01.tar.bz2) |
| 52 | `nhd_avocet_ver01` | 632 | 152,762 | 96.0% | 0.68 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/nhd_avocet_ver01.tar.bz2) |
| 53 | `dlc_burmese_ver01` | 568 | 153,330 | 96.3% | 0.04 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/dlc_burmese_ver01.tar.bz2) |
| 54 | `dlc_ocicat_ver01` | 532 | 153,862 | 96.7% | 0.06 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/dlc_ocicat_ver01.tar.bz2) |
| 55 | `njr_beachhaven_ver01` | 508 | 154,370 | 97.0% | 0.92 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/njr_beachhaven_ver01.tar.bz2) |
| 56 | `vi_jumboshrimp_ver01` | 434 | 154,804 | 97.3% | 0.37 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/vi_jumboshrimp_ver01.tar.bz2) |
| 57 | `nhd_jefferson_ver01` | 430 | 155,234 | 97.5% | 1.65 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/nhd_jefferson_ver01.tar.bz2) |
| 58 | `rp_distraughtsoul_ver03` | 416 | 155,650 | 97.8% | 0.59 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/rp_distraughtsoul_ver03.tar.bz2) |
| 59 | `wvu_lyle_ver01` | 412 | 156,062 | 98.1% | 0.00 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/wvu_lyle_ver01.tar.bz2) |
| 60 | `rp_annishag_ver04` | 396 | 156,458 | 98.3% | 0.53 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/rp_annishag_ver04.tar.bz2) |
| 61 | `wvu_fonda_ver01` | 394 | 156,852 | 98.6% | 0.73 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/wvu_fonda_ver01.tar.bz2) |
| 62 | `dlc_laperm_ver01` | 376 | 157,228 | 98.8% | 0.16 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/dlc_laperm_ver01.tar.bz2) |
| 63 | `dlc_anderson_ver01` | 312 | 157,540 | 99.0% | 2.36 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/dlc_anderson_ver01.tar.bz2) |
| 64 | `nhd_carrigain_ver01` | 292 | 157,832 | 99.2% | 1.77 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/nhd_carrigain_ver01.tar.bz2) |
| 65 | `wvu_jacob_ver01` | 208 | 158,040 | 99.3% | 1.16 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/wvu_jacob_ver01.tar.bz2) |
| 66 | `dlc_fozzie_ver01` | 192 | 158,232 | 99.4% | 0.02 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/dlc_fozzie_ver01.tar.bz2) |
| 67 | `wvu_monroe_ver01` | 176 | 158,408 | 99.5% | 0.00 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/wvu_monroe_ver01.tar.bz2) |
| 68 | `dlc_misctopsn83020874_ver02` | 164 | 158,572 | 99.6% | 0.02 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/dlc_misctopsn83020874_ver02.tar.bz2) |
| 69 | `arhi_elvis_ver01` | 160 | 158,732 | 99.7% | 0.00 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/arhi_elvis_ver01.tar.bz2) |
| 70 | `ct_dinomayo_ver02` | 116 | 158,848 | 99.8% | 1.14 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/ct_dinomayo_ver02.tar.bz2) |
| 71 | `dlc_abyssinian_ver01` | 104 | 158,952 | 99.9% | 0.01 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/dlc_abyssinian_ver01.tar.bz2) |
| 72 | `dlc_misctopsn83020866_ver03` | 84 | 159,036 | 99.9% | 0.01 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/dlc_misctopsn83020866_ver03.tar.bz2) |
| 73 | `dlc_fairview_ver01` | 40 | 159,076 | 100.0% | 0.02 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/dlc_fairview_ver01.tar.bz2) |
| 74 | `msar_emerald_ver02` | 35 | 159,111 | 100.0% | 0.55 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/msar_emerald_ver02.tar.bz2) |
| 75 | `vi_nomos_ver01` | 28 | 159,139 | 100.0% | 0.00 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/vi_nomos_ver01.tar.bz2) |
| 76 | `dlc_misctopsn83031193_ver01` | 7 | 159,146 | 100.0% | 0.00 GB | [download](https://chroniclingamerica.loc.gov/data/ocr/dlc_misctopsn83031193_ver01.tar.bz2) |

## After the text is in

The per-page job (`ingest.chronicling_america pull`) can be stopped once the first batch
extracts cleanly. One tarball holds more pages than it managed in a full day. Anything the
batches do not cover can be picked up later by the per-page route, which is resumable.

