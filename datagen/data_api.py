from fastapi import APIRouter, Depends, Query
import os
from typing import List, Optional
from pydantic import BaseModel
from time import time
from fastapi import FastAPI
import pandas as pd
from datetime import datetime

import json

from dotenv import load_dotenv
import mmap

load_dotenv()

app = FastAPI()


class BookReview(BaseModel):
    asin: Optional[str] = None
    review_date: Optional[datetime] = None
    rating: Optional[int] = None
    review_text: Optional[str] = None


BATCH_SIZE = 100000


class LoadReviews:
    def __init__(self, file_path, batch_size=BATCH_SIZE):
        self.batch_size = batch_size
        self.offset_file = "offset.txt"
        self.current_offset = self._load_offset()
        self.file_path = file_path
        self.file_offsets = self.compute_offsets()

    def compute_offsets(self):
        offsets = []
        with open(self.file_path, "r+b") as f:
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            position = 0

            while True:
                offsets.append(position)
                line = mm.readline()
                if not line:
                    break
                position = mm.tell()

            mm.close()

        return offsets

    def read_json_using_offsets(self):
        with open(self.file_path, "r+b") as f:
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            mm.seek(
                self.file_offsets[self.current_offset]
            )  # Jump directly to the start line

            lines = []
            for _ in range(self.batch_size):
                line = mm.readline()
                if not line:
                    break
                lines.append(json.loads(line.strip()))

            mm.close()

        return lines

    def _load_offset(self):
        if os.path.exists(self.offset_file):
            with open(self.offset_file, "r") as f:
                return int(f.read().strip())
        return 0

    def _save_offset(self):
        with open(self.offset_file, "w") as f:
            f.write(str(self.current_offset))

    def execute(self):
        chunk = self.read_json_using_offsets()
        df = pd.DataFrame(chunk)
        df["review_date"] = pd.to_datetime(df["unixReviewTime"], unit="s")
        df.drop(
            columns=[
                "image",
                "reviewTime",
                "reviewerID",
                "reviewerName",
                "summary",
                "verified",
                "vote",
                "unixReviewTime",
            ],
            errors="ignore",
            inplace=True,
        )
        print(f"Length of the Dataframe is {len(df)}")
        print(f"Current head is at is {self.current_offset}")

        self.current_offset += len(df)
        self._save_offset()

        return df


load_reviews = LoadReviews(file_path="/opt/data/Books_5.json", batch_size=BATCH_SIZE)


@app.get(
    "/reviews",
    tags=["get"],
    response_model=List[BookReview],
)
async def execution_events():
    """
    This route will be pinged every 5 minutes and will be expected to post 10,000
    reviews.
    """
    start = time()
    df = load_reviews.execute()

    df = df.where(pd.notnull(df), None)
    output = df.apply(
        lambda row: BookReview(
            asin=row["asin"],
            review_date=row["review_date"],
            rating=int(row["overall"]),
            review_text=row["reviewText"],
        ),
        axis=1,
    ).tolist()
    print(f"Time taken: {time() - start}")

    return output
