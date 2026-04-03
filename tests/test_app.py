from io import BytesIO

def test_health_check(test_client):
    response = test_client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['service'] == 'Call Analyzer'

def test_process_audio_no_file(test_client):
    response = test_client.post('/process_audio')
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_process_audio_empty_file(test_client):
    data = {'audio_file': (BytesIO(b''), '')}
    response = test_client.post('/process_audio', data=data, content_type='multipart/form-data')
    assert response.status_code == 400

def test_process_audio_invalid_extension(test_client):
    data = {'audio_file': (BytesIO(b'dummy data'), 'test.txt')}
    response = test_client.post('/process_audio', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    json_data = response.get_json()
    assert 'Invalid file type' in json_data['error']
