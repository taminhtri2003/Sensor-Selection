# Root cause: why the pipeline silently produced a 15-participant, 1-session result

The manuscript claimed 43 participants across 3 sessions. The feature cache contains 15
participants and session 1 only. Three independent defects combined, none of which raised an error.

## Defect 1 — the pipeline reads a partial copy of the dataset

`scripts/05_extract_features_fast.py:25`

```python
raw_dir = Path("data/raw/grabmyo")
```

That directory is an **incomplete S3 download**:

| Location | Session 1 | Session 2 | Session 3 | Files |
|---|---|---|---|---|
| `data/raw/grabmyo/` (used by pipeline) | 29 participants | **0** | **0** | 5,840 |
| repo root `Session1/2/3/` (ignored) | 43 | 43 | 43 | 30,702 |

The complete, correct dataset was already on disk at the repository root the whole time. The
pipeline never looked at it. This alone caps the study at session 1 and ≤29 participants, and makes
every cross-session claim (CS1/CS2, ρ = 0.82) arithmetically impossible from the available inputs.

## Defect 2 — silent exception swallowing

`scripts/05_extract_features_fast.py:69-71`

```python
    except Exception as e:
        pass

    return rows
```

Any recording that fails to load, filter, window, or featurise returns an empty list that is
indistinguishable from a recording legitimately yielding no windows. Combined with:

```python
if signal is None or signal.shape[1] < 16:
    return rows
```

…a missing `.dat`, a short record, or a channel-count surprise is discarded without a single
warning. This is what reduced the 29 available participants to 15. **14 participants disappeared
with no log line.**

## Defect 3 — no cohort assertion anywhere downstream

The aggregation step accepts whatever it gets:

```python
if all_rows:
    df_feat = pd.DataFrame(all_rows)
    ...
    print(f"  [OK] Saved {len(df_feat)} windows to {out_p}")
```

It prints `[OK]` for any non-empty result. No stage — extraction, baselines, statistics, or
verification — ever asserts that the analysed cohort matches the intended cohort. The manuscript's
participant count was instead written as a hardcoded macro (`\SampleSubjectsGRABMyo{43}`), so the
gap between 15 analysed and 43 claimed could never surface.

## Fixes required before re-running

1. Point ingestion at the verified root `Session1/`, `Session2/`, `Session3/` trees (or complete
   the `data/raw/grabmyo` sync); never at a partial mirror.
2. Replace `except Exception: pass` with per-record failure capture written to a QC table; a
   recording may only be dropped with a logged, inspectable reason.
3. Assert the realised cohort against an expected manifest (43 × 3 × 17 × 7) and fail loudly on
   any shortfall.
4. Derive every cohort/count macro from the result files, never from a literal.
