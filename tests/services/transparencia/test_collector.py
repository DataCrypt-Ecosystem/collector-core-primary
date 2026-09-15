import pytest
from unittest.mock import MagicMock, AsyncMock

from app.services.transparencia.collector import (
    _get_orgao,
    _list_orgaos,
    _insert_changed_raw_rows,
    _upsert_clean_rows,
    _collect_orgaos,
    ORGAO_COLLECTION_SPECS,
    collect_orgaos_siafi,
    collect_orgaos_siape,
    list_orgaos_siafi,
    list_orgaos_siape,
    collect_orgaos_siafi_with_new_session,
    collect_orgaos_siape_with_new_session
)

def test_list_orgaos():
    db = MagicMock()
    mock_query = MagicMock()
    db.query.return_value = mock_query
    
    mock_query.filter.return_value = mock_query
    mock_query.count.return_value = 10
    mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = ["item1"]
    
    model = MagicMock()
    total, items = _list_orgaos(db, model, codigo="123", descricao="test", status_registro="ok", elegivel_dashboard=True)
    
    assert total == 10
    assert items == ["item1"]
    assert mock_query.filter.call_count == 4

def test_insert_changed_raw_rows(mocker):
    db = MagicMock()
    model = MagicMock()
    
    # Mock current row that matches
    current = MagicMock()
    current.codigo = "1"
    current.descricao = "desc1"
    current.pagina_origem = 1
    current.payload_original_json = {}
    
    latest = {"1": current}
    
    rows = [
        {"codigo": "1", "descricao": "desc1", "pagina_origem": 1, "payload_original_json": {}}, # No change
        {"codigo": "2", "descricao": "desc2", "pagina_origem": 1, "payload_original_json": {}}  # Insert
    ]
    
    mocker.patch("app.services.transparencia.collector._raw_row_matches", side_effect=[True, False])
    
    inserted = _insert_changed_raw_rows(db, model, rows, latest_by_codigo=latest)
    
    assert inserted == 1
    assert db.add.call_count == 1
    assert db.flush.called

def test_upsert_clean_rows():
    db = MagicMock()
    model = MagicMock()
    
    current = MagicMock()
    current.codigo = "1"
    current.descricao = "desc1"
    
    existing = {"1": current}
    
    rows = [
        {"codigo": "1", "descricao": "desc2"}, # update
        {"codigo": "2", "descricao": "desc2"}  # insert
    ]
    
    inserted, updated = _upsert_clean_rows(db, model, rows, existing_by_codigo=existing)
    
    assert inserted == 1
    assert updated == 1
    assert db.add.call_count == 1
    assert db.flush.called

@pytest.mark.asyncio
async def test_collect_orgaos_success(mocker):
    db = MagicMock()
    spec = ORGAO_COLLECTION_SPECS["siafi"]
    
    mocker.patch("app.services.transparencia.collector._load_latest_raw_by_codigo", return_value={})
    mocker.patch("app.services.transparencia.collector._load_clean_by_codigo", return_value={})
    
    # Mock Client
    mock_client_instance = AsyncMock()
    async def mock_iter(*args, **kwargs):
        yield 1, [{"codigo": "123", "descricao": "teste"}]
    mock_client_instance.iter_pages = mock_iter
    mock_client_instance.__aenter__.return_value = mock_client_instance
    mock_client_instance.__aexit__.return_value = None
    
    mocker.patch("app.services.transparencia.collector.TransparenciaClient", return_value=mock_client_instance)
    mocker.patch("app.services.transparencia.collector.normalize_raw_record", return_value={"codigo": "1"})
    mocker.patch("app.services.transparencia.collector.normalize_clean_record", return_value={"codigo": "1"})
    mocker.patch("app.services.transparencia.collector._insert_changed_raw_rows", return_value=1)
    mocker.patch("app.services.transparencia.collector._upsert_clean_rows", return_value=(1, 0))
    
    summary = await _collect_orgaos(db, spec)
    
    assert summary["pages_collected"] == 1
    assert summary["records_received"] == 1
    assert summary["raw_inserted"] == 1
    assert summary["clean_inserted"] == 1
    assert db.commit.called

@pytest.mark.asyncio
async def test_collect_orgaos_error(mocker):
    db = MagicMock()
    spec = ORGAO_COLLECTION_SPECS["siafi"]
    
    mocker.patch("app.services.transparencia.collector._load_latest_raw_by_codigo", return_value={})
    mocker.patch("app.services.transparencia.collector._load_clean_by_codigo", return_value={})
    mocker.patch("app.services.transparencia.collector.TransparenciaClient", side_effect=Exception("API Error"))
    
    with pytest.raises(Exception):
        await _collect_orgaos(db, spec)
        
    assert db.rollback.called



@pytest.mark.asyncio
async def test_wrappers(mocker):
    db = MagicMock()
    mock_collect = mocker.patch("app.services.transparencia.collector._collect_orgaos")
    
    await collect_orgaos_siafi(db)
    await collect_orgaos_siape(db)
    assert mock_collect.call_count == 2
    
    mock_list = mocker.patch("app.services.transparencia.collector._list_orgaos", return_value=(0, []))
    list_orgaos_siafi(db)
    list_orgaos_siape(db)
    assert mock_list.call_count == 2
    
    mock_get = mocker.patch("app.services.transparencia.collector._get_orgao")
    from app.services.transparencia.collector import get_orgao_siafi, get_orgao_siape
    get_orgao_siafi(db, 1)
    get_orgao_siape(db, 1)
    assert mock_get.call_count == 2

@pytest.mark.asyncio
async def test_wrappers_with_session(mocker):
    mock_session = MagicMock()
    mocker.patch("app.services.transparencia.collector.SessionLocal", return_value=mock_session)
    mock_siafi = mocker.patch("app.services.transparencia.collector.collect_orgaos_siafi")
    mock_siape = mocker.patch("app.services.transparencia.collector.collect_orgaos_siape")
    
    await collect_orgaos_siafi_with_new_session()
    await collect_orgaos_siape_with_new_session()
    
    assert mock_siafi.called
    assert mock_siape.called
    assert mock_session.close.call_count == 2
