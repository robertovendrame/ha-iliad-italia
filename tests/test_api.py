"""Regression tests for the Iliad HTML parser."""

from __future__ import annotations

from datetime import date
import importlib.util
from pathlib import Path
import sys
import types


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "custom_components.iliad_ita"

package = types.ModuleType(PACKAGE)
package.__path__ = [str(ROOT / "custom_components" / "iliad_ita")]
sys.modules.setdefault(PACKAGE, package)

for module_name in ("const", "api"):
    full_name = f"{PACKAGE}.{module_name}"
    if full_name not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            full_name,
            ROOT / "custom_components" / "iliad_ita" / f"{module_name}.py",
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[full_name] = module
        assert spec and spec.loader
        spec.loader.exec_module(module)

api = sys.modules[f"{PACKAGE}.api"]


REALISTIC_HTML = """
<html><body>
  <section>
    <h2>Offerta Dati 350 • Credito: 0.02€</h2>
    <p>Si rinnova il 03/09/2026 alle 00:00 a 14.99€</p>
    <p>Periodo di riferimento dal 02 Agosto 2026 al 02 Settembre 2026</p>
    <b class="red" data-cs-mask>0.02 €</b>
    <span class="red">55,08GB / 350GB</span>
    <span class="big red">294</span><span class="small red">GB</span>
  </section>
</body></html>
"""


def test_parse_realistic_offer_page() -> None:
    data = api.parse_account_page(REALISTIC_HTML)

    assert data.balance_eur == 0.02
    assert data.data_used_gb == 55.08
    assert data.data_remaining_gb == 294.0
    assert data.data_allowance_gb == 350.0
    assert data.offer_name == "Offerta Dati 350"
    assert data.offer_price_eur == 14.99
    assert data.period_start == date(2026, 8, 2)
    assert data.period_end == date(2026, 9, 2)
    assert data.renewal_date == date(2026, 9, 3)


def test_offer_name_is_read_from_its_own_dom_node() -> None:
    html = """
    <html><body>
      <section>
        <h2><strong>Offerta Dati 350</strong></h2>
        <div>Dettagli linea e metodo di pagamento</div>
        <div>Credito: 0.02€</div>
        <p>Si rinnova il 03/09/2026 alle 00:00 a 14.99€</p>
        <p>Periodo di riferimento dal 02 Agosto 2026 al 02 Settembre 2026</p>
        <b class="red" data-cs-mask>0.02 €</b>
        <span class="red">55,08GB / 350GB</span>
        <span class="big red">294</span><span class="small red">GB</span>
      </section>
    </body></html>
    """
    data = api.parse_account_page(html)
    assert data.offer_name == "Offerta Dati 350"
    assert data.data_allowance_gb == 350.0
    assert data.offer_price_eur == 14.99


def test_specific_offer_wins_over_generic_mobile_label() -> None:
    html = """
    <html><body>
      <div class="menu">offerta mobile</div>
      <section>
        <h2><span>Offerta</span> <strong>Dati 350</strong></h2>
        <div>Credito: 0.02€</div>
        <p>Si rinnova il 03/09/2026 alle 00:00 a 14.99€</p>
        <p>Periodo di riferimento dal 02 Agosto 2026 al 02 Settembre 2026</p>
        <b class="red" data-cs-mask>0.02 €</b>
        <span class="red">56,75GB / 350GB</span>
        <span class="big red">293</span><span class="small red">GB</span>
      </section>
    </body></html>
    """
    data = api.parse_account_page(html)
    assert data.offer_name == "Offerta Dati 350"


def test_renewal_falls_back_to_day_after_period_end() -> None:
    html = REALISTIC_HTML.replace(
        "Si rinnova il 03/09/2026 alle 00:00 a 14.99€",
        "Dettaglio offerta mobile",
    )
    data = api.parse_account_page(html)
    assert data.renewal_date == date(2026, 9, 3)


def test_parser_keeps_working_without_offer_metadata() -> None:
    html = """
    <html><body>
      <b class="red" data-cs-mask>1,23 €</b>
      <span class="red">53,34GB</span>
      <span class="big red">246</span><span class="small red">GB</span>
    </body></html>
    """
    data = api.parse_account_page(html)
    assert data.balance_eur == 1.23
    assert data.data_used_gb == 53.34
    assert data.data_remaining_gb == 246.0
    assert data.offer_name is None
    assert data.data_allowance_gb is None
    assert data.offer_price_eur is None
