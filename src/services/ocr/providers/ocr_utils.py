import numpy as np
import pandas as pd


def paddleocr_to_df(predict_result: dict) -> pd.DataFrame:
    """
    Converts PaddleOCR .predict result to a unified DataFrame suitable for table parsing.
    """
    rec_texts = predict_result['rec_texts']
    rec_boxes = predict_result['rec_boxes']  # shape (N, 4)
    rec_scores = predict_result.get('rec_scores', [None] * len(rec_texts))

    df = pd.DataFrame({
        "text": rec_texts,
        "x_min": rec_boxes[:, 0],
        "y_min": rec_boxes[:, 1],
        "x_max": rec_boxes[:, 2],
        "y_max": rec_boxes[:, 3],
        "score": rec_scores
    })

    return df
