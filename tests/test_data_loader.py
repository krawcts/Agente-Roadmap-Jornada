import pytest
import json
import sys
import os

# Adiciona o diretório src ao path do Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Agora importa o módulo da localização correta
from utils.data_loader import load_file, get_data_dir

# Fixture to mock the data directory
@pytest.fixture
def mock_data_dir(tmpdir, monkeypatch):
    # Create a temporary 'data' directory
    data_dir = tmpdir.mkdir("data")

    # Create test files
    # Valid TXT
    valid_txt = data_dir.join("valid.txt")
    valid_txt.write("Hello, World!")

    # Valid JSON
    valid_json = data_dir.join("valid.json")
    valid_json.write(json.dumps({"key": "value"}))

    # Invalid JSON (malformed)
    invalid_json = data_dir.join("invalid.json")
    invalid_json.write("{'key': 'value',}")  # Trailing comma

    # Mock the get_data_dir function
    monkeypatch.setattr('utils.data_loader.get_data_dir', lambda: str(data_dir))
    return data_dir

# Test Cases
def test_load_valid_txt_file(mock_data_dir, capsys):
    content = load_file("valid.txt")
    captured = capsys.readouterr()

    assert content == "Hello, World!"
    assert "Arquivo de texto 'valid.txt' carregado com sucesso." in captured.out

def test_load_valid_json_file(mock_data_dir, capsys):
    content = load_file("valid.json")
    captured = capsys.readouterr()

    assert content == {"key": "value"}
    assert "Arquivo JSON 'valid.json' carregado com sucesso." in captured.out

def test_unsupported_file_type(mock_data_dir, capsys):
    content = load_file("unsupported.xml")
    captured = capsys.readouterr()

    assert content is None
    assert "Tipo de arquivo 'xml' não suportado" in captured.out

def test_file_not_found(mock_data_dir, capsys):
    content = load_file("nonexistent.txt")
    captured = capsys.readouterr()

    assert content is None
    assert "Arquivo 'nonexistent.txt' não encontrado" in captured.out

def test_invalid_json_file(mock_data_dir, capsys):
    content = load_file("invalid.json")
    captured = capsys.readouterr()

    assert content is None
    assert "Erro ao decodificar JSON do arquivo 'invalid.json'" in captured.out

def test_uppercase_extension(mock_data_dir, capsys):
    content = load_file("VALID.TXT")
    captured = capsys.readouterr()

    assert content == "Hello, World!"
    assert "Arquivo de texto 'VALID.TXT' carregado com sucesso." in captured.out

def test_override_file_type(mock_data_dir, capsys):
    # Create a .dat file but force TXT parsing
    data_dir = mock_data_dir
    test_file = data_dir.join("custom.dat")
    test_file.write("Custom content")

    content = load_file("custom.dat", file_type="txt")
    captured = capsys.readouterr()

    assert content == "Custom content"
    assert "Arquivo de texto 'custom.dat' carregado com sucesso." in captured.out