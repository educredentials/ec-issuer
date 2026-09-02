# Implementation Plan: EDC / SD-JWT VC Issuance via ssi-agent

**Status:** Accepted
**Owner:** TBD
**Approach:** Single ssi-agent, single process. New `credential_type` parameter dispatches to OB3 or EDC path.

---

## 1. Infrastructure — rename templates for correct ordering

The bootstrap `sorted()` alphabetical order puts `european_` before `openbadge_`. Fix:

```
templates/openbadge_credential_template.json → templates/01_openbadge_credential_template.json
templates/european_credential_template.json  → templates/02_european_credential_template.json
```

Now index 0 = OB3 (default), index 1 = EDC. No code changes.

---

## 2. Infrastructure — add EDC template to Prism mock

Append EDC entry to `/v0/list-all-templates` example in `dependencies/prism/ssi-agent-mock.yaml`:

```yaml
- type: ["VerifiableCredential", "EuropeanDigitalCredential"]
  id: "EuropeanDigitalCredential"
  title: "eduCredentials European Credential"
  dataModel: "european_learning_model_v3-3"
  holderType: "individual"
  status: "published"
  visibility: "public"
  description: "eduCredentials European Digital Credential"
  display:
    name: "eduCredential EDC"
    logo:
      uri: "https://ec-static.playground.sdp.surf.nl/logo_edubadges.png"
      alt_text: "eduCredential Logo"
  tags: ["educredentials", "edc", "elm", "identity"]
```

This ensures the bootstrap finds the EDC template at startup instead of trying to create it.

---

## 3. `src/awards/models.py` — rename + add

a) Rename `Award` → `OB3Award` everywhere in the file.
b) Rename export function `award_from_badgr_api_response` → `ob3_award_from_badgr_api_response`.
c) Add optional person fields to `_BadgrAwardResponse`:

   ```python
   given_name: str | None = None
   family_name: str | None = None
   ```

d) Add new `EDCAward` dataclass:

   ```python
   @dataclass
   class EDCAward:
       given_name: str
       family_name: str
       learning_achievement: dict[str, str]
       awarding_body: dict[str, str]
       awarding_opportunity: dict[str, str]
   ```

---

## 4. `src/awards/awards_client_port.py` — return type

```python
def get(self, award_id: str, bearer_token: str) -> OB3Award:
```

---

## 5. `src/awards/http_awards_client_adapter.py` — imports

Update: `Award` → `OB3Award`.

---

## 6. `src/offers/offers_client_port.py` — split create

Replace `create(offer_id, award)` with two methods:

```python
class OffersClientPort(ABC):
    @abstractmethod
    def create_ob3(self, offer_id: str, award: OB3Award) -> str: ...

    @abstractmethod
    def create_edc(self, offer_id: str, edc_claims: dict[str, str], template_id: str) -> str: ...

    @abstractmethod
    def get(self, offer_id: str) -> Offer: ...
```

---

## 7. `src/offers/ssi_agent_offers_client_adapter.py` — implement both

a) `create_ob3()` — current `create()` logic (POST `/v0/credentials` with `asdict(award)`, POST `/v0/offers` with `templateIds=[ob3_template_id]`).

b) `create_edc()` — new: POST `/v0/credentials` with `edc_claims` (flat dict) + `templateId=template_id`, POST `/v0/offers` with `templateIds=[template_id]`.

---

## 8. `src/offers/offer_service.py` — dispatch

```python
def create_offer(
    self, award_id: str, bearer_token: str, credential_type: str = "ob3"
) -> Offer:
    # ... same access control ...
    # ... same award fetch ...
    if credential_type == "edc":
        claims = self._build_edc_claims(award)
        uri = self._offers_client.create_edc(offer_id, claims, self._edc_template_id)
    else:
        uri = self._offers_client.create_ob3(offer_id, award)
    # ... same persist ...
```

`_build_edc_claims()` maps OB3Award + person DTO fields → flat EDC claims. Person fields currently hardcoded (`"Jan"`, `"Jansen"`) with TODO.

---

## 9. `src/api/http_adapter.py` — accept credential_type

```python
@dataclass
class CreateOfferBody:
    award_id: str
    credential_type: str = "ob3"
```

Endpoint reads `raw.get("credential_type", "ob3")` and passes through.

---

## 10. Tests — rename, add, parameterize

**`tests/unit/support/test_doubles.py`** — `STUB_AWARD` → `STUB_OB3_AWARD`, add `STUB_EDC_AWARD`, update all stubs/spies to implement `create_ob3`/`create_edc`.

**`tests/unit/offers/test_offer_service.py`** — rename references, add `TestOfferServiceCreateEDCOffer` class.

**`tests/unit/offers/test_ssi_agent_offers_client_adapter.py`** — rename fixtures, add tests for `create_edc()`.

**`tests/integration/test_offer_awards_interaction.py`** — add EDC dispatch tests.

**`tests/e2e/test_offer.py`** — parameterize with `@pytest.mark.parametrize("credential_type", ["ob3", "edc"])`.

**`tests/e2e/support/admin_client.py`** — accept `credential_type` in `create_offer()`.

---

## 11. ADR

**`docs/src/adr/ADR007-edc-credential-type.md`** — record: position-based template ID mapping, flat EDC claims, same ssi-agent, default key manager.

---

## Files (17 edits, 2 new, 0 deletes)

| # | File | Action |
| --- | --- | --- |
| 1 | `templates/openbadge_credential_template.json` | → `01_openbadge_credential_template.json` |
| 2 | `templates/european_credential_template.json` | → `02_european_credential_template.json` |
| 3 | `dependencies/prism/ssi-agent-mock.yaml` | Edit: add EDC to templates list |
| 4 | `src/awards/models.py` | Edit: rename Award→OB3Award, add person fields, add EDCAward |
| 5 | `src/awards/awards_client_port.py` | Edit: return OB3Award |
| 6 | `src/awards/http_awards_client_adapter.py` | Edit: import OB3Award |
| 7 | `src/offers/offers_client_port.py` | Edit: split create → create_ob3/create_edc |
| 8 | `src/offers/ssi_agent_offers_client_adapter.py` | Edit: implement both paths |
| 9 | `src/offers/offer_service.py` | Edit: dispatch by credential_type |
| 10 | `src/api/http_adapter.py` | Edit: accept credential_type |
| 11 | `tests/unit/support/test_doubles.py` | Edit: rename, add EDC |
| 12 | `tests/unit/offers/test_offer_service.py` | Edit: rename + add EDC tests |
| 13 | `tests/unit/offers/test_ssi_agent_offers_client_adapter.py` | Edit: rename + add EDC tests |
| 14 | `tests/integration/test_offer_awards_interaction.py` | Edit: add EDC tests |
| 15 | `tests/e2e/test_offer.py` | Edit: parameterize |
| 16 | `tests/e2e/support/admin_client.py` | Edit: accept credential_type |
| 17 | `docs/src/adr/ADR007-edc-credential-type.md` | New ✅ |
| 18 | `impl_plan_edc.md` | Update status to accepted ✅ |
