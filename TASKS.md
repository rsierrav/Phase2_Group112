### Need done
- [ ] Update input parsing to follow strict order: code, dataset, model.
  - Always split into three slots, even if blank.
  - Only produce output rows for models.
  - If dataset is shared (only first model has explicit link), infer from README for subsequent models.
  - If dataset is missing or invalid, set dataset-related metrics to -1.
  - If code is missing, set code-related metrics to -1.
- [ ] Add tracking mechanism for seen datasets (so duplicates aren’t re-ingested).
- [ ] Use LLM (GenAI API) when dataset link is outside HuggingFace, to extract metadata.
