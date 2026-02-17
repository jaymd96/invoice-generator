#!/usr/bin/env python3
"""
Client YAML configuration management
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any

import yaml


@dataclass
class Client:
    name: str
    company: str
    contact: str = ""
    email: str = ""
    address: List[str] = field(default_factory=list)
    currency: str = "EUR"
    currency_symbol: str = "\u20ac"
    daily_rate: float = 0.0
    payment_terms_days: int = 30
    payment_details: Dict[str, str] = field(default_factory=dict)
    output_dir: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'company': self.company,
            'contact': self.contact,
            'email': self.email,
            'address': self.address,
            'currency': self.currency,
            'currency_symbol': self.currency_symbol,
            'daily_rate': self.daily_rate,
            'payment_terms_days': self.payment_terms_days,
            'payment_details': self.payment_details,
        }


def load_client(name: str, clients_dir: str = "clients") -> Client:
    """Load a client from its YAML config file"""
    config_path = Path(clients_dir) / name / "client.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Client config not found: {config_path}")

    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)

    return Client(
        name=data.get('name', name),
        company=data.get('company', ''),
        contact=data.get('contact', ''),
        email=data.get('email', ''),
        address=data.get('address', []),
        currency=data.get('currency', 'EUR'),
        currency_symbol=data.get('currency_symbol', '\u20ac'),
        daily_rate=float(data.get('daily_rate', 0)),
        payment_terms_days=int(data.get('payment_terms_days', 30)),
        payment_details=data.get('payment_details', {}),
        output_dir=str(Path(clients_dir) / name / "invoices"),
    )


def init_client(name: str, clients_dir: str = "clients") -> Path:
    """Create a new client directory with template YAML config"""
    client_dir = Path(clients_dir) / name
    client_dir.mkdir(parents=True, exist_ok=True)
    (client_dir / "invoices").mkdir(exist_ok=True)

    config_path = client_dir / "client.yaml"
    if config_path.exists():
        raise FileExistsError(f"Client config already exists: {config_path}")

    template = {
        'name': name.replace('_', ' ').title(),
        'company': '',
        'contact': '',
        'email': '',
        'address': ['123 Business St', 'City, Country'],
        'currency': 'EUR',
        'currency_symbol': '\u20ac',
        'daily_rate': 0.0,
        'payment_terms_days': 30,
        'payment_details': {
            'Bank': '',
            'IBAN': '',
            'BIC': '',
            'Reference': 'Please use invoice number',
        },
    }

    with open(config_path, 'w') as f:
        yaml.dump(template, f, default_flow_style=False, sort_keys=False)

    return config_path


def list_clients(clients_dir: str = "clients") -> List[str]:
    """List all configured client names"""
    clients_path = Path(clients_dir)
    if not clients_path.exists():
        return []

    return sorted([
        d.name for d in clients_path.iterdir()
        if d.is_dir() and (d / "client.yaml").exists()
    ])
