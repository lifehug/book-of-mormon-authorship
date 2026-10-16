# HathiTrust research dataset request (BOM-08)

Process, from https://www.hathitrust.org/member-libraries/resources-for-librarians/data-resources/research-datasets/ (read 2026-10-15):

1. Email a brief proposal to support@hathitrust.org: researchers (name, affiliation, country),
   dataset wanted, research to be done, result outputs, how outputs will be used, permission
   to share the proposal.
2. Sign and return the researcher agreement for the dataset (the non-Google version for us).
3. On approval, supply a static non-NAT IP address; rsync access is tied to it.
4. rsync only the wanted volumes by generating pairtree paths from the volume ID list
   (`data/catalog/hathitrust_ids_not_in_harvard.txt`); HathiTrust's instruction guide has the
   path-generation script. Each volume arrives as `<id>.mets.xml` plus `<id>.zip` of page
   text files. HathiTrust's `ht-text-prep` library (https://github.com/htrc/ht-text-prep)
   removes running headers and footers.
5. Dataset recipients receive deletion notices for volumes later found not to be public
   domain and must delete them.

Datasets:

| Dataset | Contents | Who may get it |
| --- | --- | --- |
| `ht_text_pd_open_access` | public domain, excluding Google-digitized, US researchers | anyone approved |
| `ht_text_pd` | all public domain including Google-digitized | only researchers at an institution that signed the Google Distribution Agreement |

Our 107,178 volumes not in Harvard split by digitizer: Google 75,984 (needs `ht_text_pd`, not
available to an independent researcher), Internet Archive 24,261 (fetch from the Archive
directly, BOM-09), other 6,933 (in `ht_text_pd_open_access`, and downloadable in full from
babel.hathitrust.org by anyone).

Request sent: 2026-10-15 from davidjamestaylor@gmail.com. Reply: (to fill in).

Note on the Google-digitized set: the Distribution Agreement covers researchers at a signatory institution; alumni status is not a research affiliation. A current researcher at a listed institution could be the primary requester, in which case the data stays on their servers (HathiTrust's dispersed-team rule) and that part of the analysis would run there.

Citation format once used: HathiTrust. English-language public domain print, 1780-1830
(subset). Distributed by HathiTrust (Requesting and Using Research Datasets).
https://github.com/lifehug/book-of-mormon-authorship/blob/master/data/catalog/hathitrust_ids_not_in_harvard.txt.
Accessed DATE.

## Email as sent

Subject: Research dataset request: public domain English text, 1780-1830 (ht_text_pd_open_access)

From: davidjamestaylor@gmail.com. Researchers: David Taylor, independent researcher, United States; sole user of the data.
Dataset: ht_text_pd_open_access; subset of English volumes with rights dates 1780-1830
(135,035 in the 2026-10-01 hathifile; about 31,000 after excluding Google-digitized and
Harvard-available volumes); ID list linked above. Research: pre-registered computational
study of the authorship, borrowing, and dating of the earliest Book of Mormon text against
1780-1830 English print (stylometry, text reuse, period language model); OSF
https://osf.io/6ugxc/; code public. Outputs: manifests, catalog metadata, statistical
results, alignment tables citing HathiTrust volume IDs, models that cannot reproduce text,
preprint, web explorer by citation. No re-hosting or redistribution. Permission to share the
proposal: yes. Will sign the non-Google researcher agreement and supply a static IP.
