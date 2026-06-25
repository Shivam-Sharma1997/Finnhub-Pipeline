

import requests
import pandas as pd
from airflow.exceptions import AirflowException
from unittest.mock import MagicMock,patch
from FInnhubDataValidator import FinnhubDataValidator
from Basehook import FinnhubAPI




SAMPLE_QUOTE = pd.DataFrame([{
    "c": 250.10, "d": 2.50, "dp": 1.01,
    "h": 252.00, "l": 248.50, "o": 249.00,
    "pc": 247.60
}])
EMPTY_QUOTE = pd.DataFrame(columns =
   [ "c", "d", "dp",  
    "h", "l", "o", "pc"]
)
ZERO_QUOTE = pd.DataFrame([{
    "c": 0.0, "d": 0.0, "dp": 0.0, "h": 0.0, "l": 0.0, "o": 0.0, "pc": 0.0
}])   

def test_session(client,mocker):
    mock_session = MagicMock()
    mock_session.status_code = 200
    mock_session.json.return_value = {"c":250.10}
    mock_session.raise_for_status.return_value = None
    mocker.patch("requests.Session.get",return_value = mock_session)
    assert client.fetch_data("AAPL")["c"] == 250.10

class TestValidators:
    def test_check_not_empty_passes(self):
        result = FinnhubDataValidator(SAMPLE_QUOTE)._check_not_empty(SAMPLE_QUOTE)
        assert result.passed == True
        assert "length" in result.message

    def test_check_not_empty_fails(self):
        result = FinnhubDataValidator(EMPTY_QUOTE)._check_not_empty(EMPTY_QUOTE)
        assert result.passed == False
        assert result.severity == "critical"

    def test_check_columns_passes(self):
        result = FinnhubDataValidator(SAMPLE_QUOTE)._check_columns(SAMPLE_QUOTE)
        assert result.passed == True
    
    def test_check_columns_fails(self):
        bad_df = SAMPLE_QUOTE.drop(columns = ["c"])
        result = FinnhubDataValidator(bad_df)._check_columns(bad_df)
        assert result.passed == False
        assert "Missing" in result.message

    def test_duplicate_values_passes(self):
        result = FinnhubDataValidator(SAMPLE_QUOTE)._duplicate_values(SAMPLE_QUOTE)
        assert result.passed == True
    
    def test_duplicate_values_detected(self):
        dup_df = pd.concat([SAMPLE_QUOTE, SAMPLE_QUOTE], ignore_index=True)
        result = FinnhubDataValidator(dup_df)._duplicate_values(dup_df)
        assert result.passed == False
        
    def test_validate_warning_only_passes(self):
        dup_df = pd.concat([SAMPLE_QUOTE, SAMPLE_QUOTE], ignore_index=True)
        passed, _ = FinnhubDataValidator(dup_df).validate()
        assert passed == True

    

        

class TestFetchData:
    def test_fetch_success(self, client, mocker):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"c": 250.10}
        mocker.patch("requests.Session.get", return_value=mock_resp)
        assert client.fetch_data("AAPL")["c"] == 250.10

    
    def test_return_none_404_error(self, client, mocker):
        err_resp = MagicMock()
        err_resp.status_code = 404
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.raise_for_status.side_effect = requests.HTTPError(response=err_resp)
        mocker.patch("requests.Session.get", return_value=mock_resp)
        assert client.fetch_data("BAD") is None
       
