from pathlib import Path

import yaml

from invoice_generator.client import Client, load_client, init_client, list_clients


class TestInitClient:
    def test_creates_directory_and_yaml(self, tmp_path):
        config_path = init_client("acme_corp", str(tmp_path))
        assert config_path.exists()
        assert (tmp_path / "acme_corp" / "invoices").is_dir()

        with open(config_path) as f:
            data = yaml.safe_load(f)
        assert data['name'] == "Acme Corp"
        assert data['currency'] == "EUR"

    def test_raises_if_already_exists(self, tmp_path):
        init_client("acme_corp", str(tmp_path))
        try:
            init_client("acme_corp", str(tmp_path))
            assert False, "Should have raised FileExistsError"
        except FileExistsError:
            pass


class TestLoadClient:
    def test_loads_yaml(self, tmp_path):
        client_dir = tmp_path / "test_client"
        client_dir.mkdir()
        config = {
            'name': 'Test Client',
            'company': 'Test Co',
            'currency': 'USD',
            'currency_symbol': '$',
            'daily_rate': 750.0,
            'payment_terms_days': 14,
            'payment_details': {'Bank': 'Test Bank'},
        }
        with open(client_dir / "client.yaml", 'w') as f:
            yaml.dump(config, f)

        client = load_client("test_client", str(tmp_path))
        assert client.name == "Test Client"
        assert client.company == "Test Co"
        assert client.currency == "USD"
        assert client.daily_rate == 750.0
        assert client.payment_details == {'Bank': 'Test Bank'}
        assert "invoices" in client.output_dir

    def test_raises_if_not_found(self, tmp_path):
        try:
            load_client("nonexistent", str(tmp_path))
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            pass

    def test_loads_example_client(self):
        """Verify the shipped example client.yaml is valid"""
        clients_dir = Path(__file__).parent.parent / "clients"
        client = load_client("example", str(clients_dir))
        assert client.name == "Acme Corp"
        assert client.currency == "GBP"
        assert client.daily_rate == 500.0


class TestListClients:
    def test_lists_clients(self, tmp_path):
        init_client("alpha", str(tmp_path))
        init_client("beta", str(tmp_path))
        clients = list_clients(str(tmp_path))
        assert clients == ["alpha", "beta"]

    def test_empty_dir(self, tmp_path):
        assert list_clients(str(tmp_path)) == []

    def test_missing_dir(self, tmp_path):
        assert list_clients(str(tmp_path / "nonexistent")) == []


class TestClientDataclass:
    def test_to_dict(self):
        client = Client(name="Test", company="TestCo", currency="USD",
                        currency_symbol="$", daily_rate=100.0)
        d = client.to_dict()
        assert d['name'] == "Test"
        assert d['currency'] == "USD"
        assert 'output_dir' not in d
