from utils.data_loader import load_data

def test_data_loads():
    df = load_data()
    assert not df.empty
    assert "Close" in df.columns