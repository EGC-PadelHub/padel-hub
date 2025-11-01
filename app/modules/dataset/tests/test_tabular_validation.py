import os
import tempfile
from app.modules.dataset.types.tabular import TabularDataset


def write_file(path, content, encoding='utf-8'):
    with open(path, 'w', encoding=encoding) as f:
        f.write(content)


def test_validate_syntax_valid_ascii():
    content = "name,score\nJuan,3\nMaria,4\nPedro,2\n"
    fd, path = tempfile.mkstemp(suffix='.csv')
    os.close(fd)
    try:
        write_file(path, content, encoding='utf-8')
        res = TabularDataset(None).validate_syntax(path)
        assert res.get('valid') is True
        assert 'encoding' in res
    finally:
        os.remove(path)


def test_validate_syntax_syntax_error():
    # unclosed quote on second data line
    content = 'name,score\nJuan,3\nMaria,"4\nPedro,2\n'
    fd, path = tempfile.mkstemp(suffix='.csv')
    os.close(fd)
    try:
        write_file(path, content, encoding='utf-8')
        res = TabularDataset(None).validate_syntax(path)
        assert res.get('valid') is False
        assert 'line' in res
        assert 'message' in res
        # snippet should be present to help user
        assert res.get('snippet') is not None
    finally:
        os.remove(path)


def test_validate_syntax_encoding_fallback():
    # create bytes that are invalid utf-8 but valid latin-1
    # for example, 0xE9 is 'é' in latin-1
    content = 'name,city\nAlice,Sev\xe9lla\nBob,Malaga\n'
    fd, path = tempfile.mkstemp(suffix='.csv')
    os.close(fd)
    try:
        # write bytes directly to simulate legacy encoding
        with open(path, 'wb') as f:
            f.write(content.encode('latin-1'))
        res = TabularDataset(None).validate_syntax(path)
        # should accept with latin-1
        assert res.get('valid') is True
        assert res.get('encoding') in ('latin-1', 'cp1252')
    finally:
        os.remove(path)
