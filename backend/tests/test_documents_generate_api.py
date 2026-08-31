"""HTTP-contract tests for ``POST /api/v1/documents/generate`` (ticket 02).

The central property under test: this endpoint never trusts the client's
claim that ``normalized_data`` already passed ``/survey/validate`` — every
request here calls it directly, several with data that would only be
rejected if the endpoint re-ran the structural rules itself.
"""

import io
import os
import tempfile
from pathlib import Path

from docx import Document

ENDPOINT = "/api/v1/documents/generate"
DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def test_generate_returns_a_valid_docx_with_submitted_values(client, valid_document_generate_payload):
    response = client.post(ENDPOINT, json=valid_document_generate_payload)

    assert response.status_code == 200
    assert response.headers["content-type"] == DOCX_MEDIA_TYPE
    assert "attachment" in response.headers["content-disposition"]

    document = Document(io.BytesIO(response.content))
    full_text = "\n".join(p.text for p in document.paragraphs)

    normalized = valid_document_generate_payload["normalized_data"]
    assert normalized["organization"]["company_name"] in full_text
    assert normalized["organization"]["inn"] in full_text
    assert normalized["organization"]["address"] in full_text
    assert normalized["contact"]["full_name"] in full_text
    assert normalized["contact"]["email"] in full_text
    assert normalized["equipment"]["equipment_type"] in full_text
    assert normalized["equipment"]["welding_method"] in full_text
    assert normalized["equipment"]["brand"] in full_text
    assert "SN-001" in full_text and "SN-002" in full_text
    assert "Демо-АЦ" in full_text  # resolved from the ac_registry, not echoed input

    assert "демонстрационный макет, не является официальным бланком ац" in full_text.lower()


def test_generate_independently_rejects_invalid_data_the_client_calls_already_valid(
    client, valid_document_generate_payload
):
    # No call to /survey/validate precedes this — and the data is invalid.
    # The client's request shape is otherwise well-formed; only the content
    # (a blank company name) should be rejected, proving the endpoint
    # re-validates rather than trusting the caller.
    valid_document_generate_payload["normalized_data"]["organization"]["company_name"] = "   "

    response = client.post(ENDPOINT, json=valid_document_generate_payload)

    assert response.status_code == 400
    body = response.json()
    assert body["detail"]
    assert any(
        error["field"] == "organization.company_name" and error["code"] == "required" for error in body["errors"]
    )


def test_generate_rejects_a_value_outside_the_reference_list(client, valid_document_generate_payload):
    valid_document_generate_payload["normalized_data"]["equipment"]["welding_method"] = "не из справочника"

    response = client.post(ENDPOINT, json=valid_document_generate_payload)

    assert response.status_code == 400
    body = response.json()
    assert any(
        error["field"] == "equipment.welding_method" and error["code"] == "not_in_reference_list"
        for error in body["errors"]
    )


def test_generate_rejects_mismatched_direction_between_routing_and_normalized_data(
    client, valid_document_generate_payload
):
    valid_document_generate_payload["attestation_direction"] = "materials"
    # normalized_data.attestation_direction stays "equipment" so this test
    # isolates the mismatch check from the unrelated "unsupported_direction"
    # check on the nested value.

    response = client.post(ENDPOINT, json=valid_document_generate_payload)

    assert response.status_code == 400
    body = response.json()
    assert any(
        error["field"] == "attestation_direction" and error["code"] == "mismatched_routing_field"
        for error in body["errors"]
    )


def test_generate_rejects_mismatched_ac_code_between_routing_and_normalized_data(
    client, valid_document_generate_payload
):
    valid_document_generate_payload["attestation_center_code"] = "some-other-code"

    response = client.post(ENDPOINT, json=valid_document_generate_payload)

    assert response.status_code == 400
    body = response.json()
    assert any(
        error["field"] == "attestation_center_code" and error["code"] == "mismatched_routing_field"
        for error in body["errors"]
    )


def test_generate_leaves_no_temporary_files_on_disk(client, valid_document_generate_payload):
    temp_dir = Path(tempfile.gettempdir())
    before = set(os.listdir(temp_dir))

    for _ in range(2):
        response = client.post(ENDPOINT, json=valid_document_generate_payload)
        assert response.status_code == 200

    after = set(os.listdir(temp_dir))
    assert after - before == set()
