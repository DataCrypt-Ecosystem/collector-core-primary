import pytest
import polars as pl
from pathlib import Path
from unittest.mock import MagicMock

from app.services.transparencia.etl import run_etl, get_db_connection

def test_get_db_connection(mocker):
    mocker.patch("os.getenv", side_effect=lambda k, d=None: "mock_url" if k == "DATABASE_URL" else d)
    mock_connect = mocker.patch("psycopg2.connect")
    
    get_db_connection()
    mock_connect.assert_called_once_with("mock_url")

def test_get_db_connection_no_url(mocker):
    mocker.patch("os.getenv", side_effect=lambda k, d=None: None if k == "DATABASE_URL" else "mock_val")
    mock_connect = mocker.patch("psycopg2.connect")
    
    get_db_connection()
    mock_connect.assert_called_once_with(
        dbname="mock_val", user="mock_val", password="mock_val", host="localhost", port="mock_val"
    )

def test_run_etl_no_parquet_dir(mocker, capsys):
    mocker.patch("pathlib.Path.exists", return_value=False)
    run_etl()
    captured = capsys.readouterr()
    assert "Nenhum arquivo Parquet encontrado" in captured.out

def test_run_etl_no_files(mocker, capsys):
    mocker.patch("pathlib.Path.exists", return_value=True)
    mocker.patch("pathlib.Path.glob", return_value=[])
    run_etl()
    captured = capsys.readouterr()
    assert "Nenhum dado novo para processar" in captured.out

def test_run_etl_success(mocker):
    mocker.patch("pathlib.Path.exists", return_value=True)
    
    mock_file = MagicMock()
    mock_file.relative_to.return_value = Path("mock/file.parquet")
    mocker.patch("pathlib.Path.glob", return_value=[mock_file])
    
    # Mock dataframe
    mock_df = pl.DataFrame({
        "tipo_beneficio": ["bf", "bf"],
        "data_referencia": ["2023-01-01", "2023-01-01"],
        "municipio_codigo_ibge": ["123", "123"],
        "valor": [100.0, 150.0],
        "quantidade_beneficiados": [10, 15]
    })
    
    mocker.patch("polars.read_parquet", return_value=mock_df)
    
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    mocker.patch("app.services.transparencia.etl.get_db_connection", return_value=mock_conn)
    
    mock_execute_values = mocker.patch("app.services.transparencia.etl.execute_values")
    mock_move = mocker.patch("shutil.move")
    mocker.patch("pathlib.Path.mkdir")
    
    run_etl()
    
    assert mock_execute_values.called
    assert mock_conn.commit.called
    assert mock_cur.close.called
    assert mock_conn.close.called
    assert mock_move.called

def test_run_etl_empty_df(mocker):
    mocker.patch("pathlib.Path.exists", return_value=True)
    mocker.patch("pathlib.Path.glob", return_value=[Path("dummy")])
    mocker.patch("polars.read_parquet", return_value=pl.DataFrame())
    
    mock_get_db = mocker.patch("app.services.transparencia.etl.get_db_connection")
    
    run_etl()
    
    # DB shouldn't be connected if df is empty
    mock_get_db.assert_not_called()

def test_run_etl_db_error(mocker, capsys):
    mocker.patch("pathlib.Path.exists", return_value=True)
    mocker.patch("pathlib.Path.glob", return_value=[Path("dummy")])
    
    mock_df = pl.DataFrame({
        "tipo_beneficio": ["bf"],
        "data_referencia": ["2023-01-01"],
        "municipio_codigo_ibge": ["123"],
        "valor": [100.0],
        "quantidade_beneficiados": [10]
    })
    mocker.patch("polars.read_parquet", return_value=mock_df)
    
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.execute.side_effect = Exception("DB Error")
    mock_conn.cursor.return_value = mock_cur
    mocker.patch("app.services.transparencia.etl.get_db_connection", return_value=mock_conn)
    
    run_etl()
    
    assert mock_conn.rollback.called
    assert mock_cur.close.called
    assert mock_conn.close.called
