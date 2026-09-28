"""Turns a pandas DataFrame result into simple bar-chart-ready JSON for the frontend."""


def to_chart_spec(df):
    if df.empty:
        return None

    label_col = next((c for c in ("county", "region") if c in df.columns), df.columns[0])
    numeric_cols = [c for c in df.columns if df[c].dtype.kind in "if"]
    if not numeric_cols:
        return None
    value_col = numeric_cols[-1]

    subset = df[[label_col, value_col]].head(20)
    return {
        "type": "bar",
        "label_field": label_col,
        "value_field": value_col,
        "labels": subset[label_col].astype(str).tolist(),
        "values": subset[value_col].tolist(),
    }
