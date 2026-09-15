import pytest
from unittest.mock import MagicMock

from app.services.ibge.localidades_sync_service import (
    sync_localidades,
    sync_localidades_with_new_session,
    _upsert_rows
)

def test_upsert_rows_insert_and_update(mocker):
    db = MagicMock()
    mock_model = MagicMock()
    
    # Existing object
    existing_obj = MagicMock()
    existing_obj.id_regiao = 1
    existing_obj.nome = "Sul"
    
    mock_query = MagicMock()
    mock_query.all.return_value = [existing_obj]
    db.query.return_value = mock_query
    
    # Rows to upsert
    rows = [
        {"id_regiao": 1, "nome": "Sudoeste"},  # update
        {"id_regiao": 2, "nome": "Norte"}      # insert
    ]
    
    result = _upsert_rows(db, mock_model, "id_regiao", rows)
    
    assert result["inserted"] == 1
    assert result["updated"] == 1
    assert existing_obj.nome == "Sudoeste"
    assert db.add.called
    assert db.flush.called

def test_sync_localidades_success(mocker):
    mocker.patch("app.services.ibge.localidades_sync_service.fetch_municipios", return_value=[])
    mocker.patch("app.services.ibge.localidades_sync_service.parse_localidades", return_value={
        "regioes": [{"id_regiao": 1}],
        "estados": [{"id_estado": 1}],
        "municipios": [{"id_municipio": 1}]
    })
    
    mock_upsert = mocker.patch("app.services.ibge.localidades_sync_service._upsert_rows", side_effect=[
        {"inserted": 1, "updated": 0},
        {"inserted": 1, "updated": 0},
        {"inserted": 1, "updated": 0}
    ])
    
    db = MagicMock()
    result = sync_localidades(db)
    
    assert mock_upsert.call_count == 3
    assert db.commit.called
    assert result["regioes"]["inserted"] == 1

def test_sync_localidades_error(mocker):
    mocker.patch("app.services.ibge.localidades_sync_service.fetch_municipios", return_value=[])
    mocker.patch("app.services.ibge.localidades_sync_service.parse_localidades", return_value={})
    mocker.patch("app.services.ibge.localidades_sync_service._upsert_rows", side_effect=Exception("DB Error"))
    db = MagicMock()
    
    with pytest.raises(Exception):
        sync_localidades(db)
        
    assert db.rollback.called

def test_sync_localidades_with_new_session(mocker):
    mock_session = MagicMock()
    mocker.patch("app.services.ibge.localidades_sync_service.SessionLocal", return_value=mock_session)
    mock_sync = mocker.patch("app.services.ibge.localidades_sync_service.sync_localidades", return_value="success")
    
    res = sync_localidades_with_new_session()
    
    assert res == "success"
    assert mock_session.close.called
