import logging 
from dataclasses import dataclass
from typing import Tuple,List
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class FinnhubValidationResult:
    check_name: str
    passed: bool
    message: str
    severity: str

class FinnhubDataValidator:
    def __init__(self,df:pd.DataFrame):
        self.df = df

    def validate(self)-> Tuple[bool,List[FinnhubValidationResult]]:
        results = []
        not_empty = self._check_not_empty(self.df)
        results.append(not_empty)
        columns = self._check_columns(self.df)
        results.append(columns)

        
        if not_empty.passed and columns.passed:
            results.append(self._data_types(self.df))
            results.append(self._check_null(self.df))
            results.append(self._duplicate_values(self.df))
            results.append(self._check_price_sanity(self.df))
        
        for result in results:
            if result.passed:
                logger.info(f"{result.check_name}:{result.message}")
            elif result.severity == "warning":
                logger.warning(f"{result.check_name}:{result.message}")
            else:
                logger.error(f"{result.check_name}:{result.message}")
        critical_failures = [ result for result in results if not result.passed and result.severity == "critical"]
        all_passed = len(critical_failures) == 0

        if not all_passed:
            failure_messages = [failure.message for failure in critical_failures]
            logger.error(f"Validation Failed:{failure_messages}")
        return all_passed,results
    
    def _check_price_sanity(self,df:pd.DataFrame)->FinnhubValidationResult:
        price_cols = ["c","h","l","o","pc"]
        not_positive = (df[price_cols] <= 0).any(axis=1)
        high_low = df["h"]<df["l"]
        out_of_range = (df["c"] < df["l"]) | (df["c"]>df["h"])
        bad_price = (not_positive | high_low | out_of_range).sum()
        return FinnhubValidationResult(
            check_name = "Price Sanity",
            passed = bad_price == 0,
            message = f"{bad_price} row or rows failed price sanity (not-positive,high<low, or out of range)",
            severity = "critical"
        )
        
    def _check_not_empty(self, df:pd.DataFrame)-> FinnhubValidationResult:
        passed = len(df) > 0
        return FinnhubValidationResult(
            check_name = "Not Empty",
            passed = passed,
            message = f"Dataframe is not Empty and has length {len(df)}" if passed  else "Dataframe is Empty",
            severity = "critical"
        )

    def _check_columns(self, df:pd.DataFrame)-> FinnhubValidationResult:
        available_columns = {"c","d","dp","h","l","o","pc"}
        missing_columns = available_columns - set(df.columns)
        passed = len(missing_columns) == 0
        return FinnhubValidationResult(
            check_name = "Not Missing",
            passed = passed,
            message = "All Columns present" if passed  else f"The Dataframe has {missing_columns} Columns Missing.",
            severity = "critical"
        )
    
    def _data_types(self, df:pd.DataFrame)-> FinnhubValidationResult:
        data_types = {"c":float,"d":float,"dp":float,"h":float,"l":float,"o":float,"pc":float}
        for k,v in data_types.items():
            if k not in df.columns:
                continue
            if df[k].dtype != v:
                return FinnhubValidationResult(
                    check_name = "Data Types",
                    passed = False,
                    message = f" Column {k} is not of the Float Data Type",
                    severity = "critical"
                )
        return FinnhubValidationResult(
        check_name="Data Types",
        passed=True,
        message="All columns have correct data types",
        severity="critical",
    )
               
    def _check_null(self, df:pd.DataFrame) -> FinnhubValidationResult:
        null_counts = df.isnull().sum()
        total_nulls = null_counts.sum()
        cols_with_nulls = null_counts[null_counts > 0].to_dict()
        passed = total_nulls == 0
        return FinnhubValidationResult(
            check_name = "Null Values",
            passed = passed,
            message = "No null values" if passed else f"Null values: {cols_with_nulls}",
            severity = "critical"
        )

    def _duplicate_values(self, df: pd.DataFrame) -> FinnhubValidationResult:
        key = [c for c in ["symbol", "date"] if c in df.columns]
        duplicate_values = df.duplicated(subset=key).sum() if key else df.duplicated().sum()
        passed = duplicate_values == 0
        return FinnhubValidationResult(
            check_name="Duplicate Values",
            passed=passed,
            message=f"DataFrame has {duplicate_values} duplicate rows on {key or 'all columns'}",
            severity="warning",
        )
  

