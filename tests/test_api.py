def test_api_status(testclient):
    response = testclient.get('api/v1/')
    data = response.json()
    assert data['data'] == {}


def test_api_list_namespace(testclient):
    response = testclient.get('api/v1/namespace')
    data = response.json()
