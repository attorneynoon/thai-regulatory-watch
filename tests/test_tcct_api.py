"""Offline TCCT contracts; recovered fixtures declare their synthetic provenance."""
import copy
import json
from pathlib import Path
import unittest

try:
    from regwatch import tcct_api
except ImportError:
    tcct_api = None

FIXTURES = Path(__file__).parent / "fixtures" / "tcct-api"


def fixture(key="verdict"):
    return json.loads((FIXTURES / (key + ".json")).read_text("utf-8"))


def pages(total=13, key="verdict"):
    sample = fixture(key)
    result = {}
    count = (total + 11) // 12
    for page in range(1, count + 1):
        records = []
        for number in range((page - 1) * 12, min(page * 12, total)):
            record = copy.deepcopy(sample["records"][0])
            record["id"] = "record-" + str(number)
            record["code"] = "CODE-" + str(number)
            records.append(record)
        result[page] = {"status": "success", "data": {
            "contents": records, "category": sample["listing_category"],
            "meta": {"total": total, "page": page, "limit": 12,
                     "totalPages": count, "hasNextPage": page < count,
                     "hasPreviousPage": page > 1}}}
    return result


class TcctApiTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(tcct_api, "Offline TCCT parser has not been implemented")

    def test_observed_verdict_contract_preserves_identity_raw_date_and_false_public_flag(self):
        row = tcct_api.normalize_record(fixture()["records"][0], "verdict")
        self.assertEqual(row["id"], "75ad3a91-53ed-4ac0-ac65-27f357b38ee3")
        self.assertEqual(row["code"], "CTN260920125848")
        self.assertEqual(row["source_start_date"], "2026-09-17T00:00:00.000Z")
        self.assertEqual(row["category_years_buddhist"], [2569])
        self.assertEqual(row["downloads"][0]["fileUrl"], "https://api.tcct.or.th/upload/f0b69f4d-257c-4acc-8434-5111573e0058")
        self.assertIs(row["downloads"][0]["isPublic"], False)
        self.assertEqual(row["downloads"][0]["file_size"], 36090254)
        self.assertNotIn("published_at", row)
        self.assertNotIn("detail_url", row)

    def test_each_reconstructed_fixture_preserves_every_membership_and_download(self):
        expected = {
            "verdict": ("75ad3a91-53ed-4ac0-ac65-27f357b38ee3", 2, 1),
            "verdict-mergers": ("b05d6e3b-96a9-45b4-abbc-2558f0420adc", 3, 1),
            "draft-principles-hearing": ("03802ed9-c6e3-4a3d-ac83-338e973df5c0", 1, 0),
            "tcct-draft-laws-hearing": ("1014bc1b-a6ff-4ee5-9c69-e563567a76f4", 1, 0),
            "giveaway-news-2569": ("92650bd5-818c-40ea-8682-85f02769085f", 1, 1),
            "activity-news-2569": ("a3990e8a-a6e5-4dbd-9eaf-d5c45df472a7", 1, 0),
        }
        for key, (ident, memberships, downloads) in expected.items():
            with self.subTest(key=key):
                rows = [tcct_api.normalize_record(r, key) for r in fixture(key)["records"]]
                self.assertEqual(rows[0]["id"], ident)
                self.assertEqual(len(rows[0]["categories"]), memberships)
                self.assertEqual(len(rows[0]["downloads"]), downloads)

    def test_all_files_survive_including_extensionless_download_urls(self):
        row = tcct_api.normalize_record(fixture("tcct-draft-laws-hearing")["records"][1], "tcct-draft-laws-hearing")
        self.assertEqual(row["id"], "2884944d-6154-442f-b942-127e62665275")
        self.assertEqual(len(row["downloads"]), 2)
        self.assertTrue(all("/upload/" in f["fileUrl"] for f in row["downloads"]))
        self.assertTrue(all(f["isPublic"] is False for f in row["downloads"]))

    def test_duplicate_category_memberships_are_preserved(self):
        record = fixture()["records"][0]
        record["categories"].append(copy.deepcopy(record["categories"][0]))
        row = tcct_api.normalize_record(record, "verdict")
        self.assertEqual(len(row["categories"]), 3)
        self.assertEqual(row["categories"][0], row["categories"][2])

    def test_external_reference_and_body_hrefs_are_preserved_without_detail_url(self):
        record = fixture("draft-principles-hearing")["records"][0]
        row = tcct_api.normalize_record(record, "draft-principles-hearing")
        self.assertEqual(row["url_link"], "https://sites.google.com/view/hearing-trustee/hearing-trustee")
        self.assertIn(row["url_link"], [r["url"] for r in row["reference_links"]])
        record["content"] = '<p>Source <a href="https://docs.google.com/forms/example?a=1&amp;b=2">form</a></p><script>private()</script>'
        row = tcct_api.normalize_record(record, "draft-principles-hearing")
        self.assertEqual(row["body_text"], "Source form")
        self.assertEqual(row["body_links"][0]["raw_url"], "https://docs.google.com/forms/example?a=1&b=2")
        self.assertNotIn("private", row["body_text"])
        self.assertNotIn("url", row)

    def test_unsafe_body_reference_is_inert_evidence_and_never_upgraded(self):
        record = fixture("activity-news-2569")["records"][1]
        row = tcct_api.normalize_record(record, "activity-news-2569")
        denied = [r for r in row["body_links"] if not r["accepted"]]
        self.assertEqual(len(denied), 1)
        self.assertTrue(denied[0]["raw_url"].startswith("http://www.tcct.or.th/"))
        self.assertNotIn(denied[0]["raw_url"], [r["url"] for r in row["reference_links"]])
        self.assertIn("rejected_reference", row["warnings"])

    def test_empty_content_is_retained_with_missing_content_warning(self):
        record = fixture("tcct-draft-laws-hearing")["records"][0]
        record.update(content=None, description=None, file_list=[], url_link=None, is_reference_link=False)
        row = tcct_api.normalize_record(record, "tcct-draft-laws-hearing")
        self.assertEqual(row["body_text"], "")
        self.assertIn("content_missing", row["warnings"])

    def test_category_year_mismatch_does_not_rewrite_source_date(self):
        record = fixture()["records"][0]
        record["start_date"] = "2020-02-03T07:04:05+07:00"
        row = tcct_api.normalize_record(record, "verdict")
        self.assertEqual(row["source_start_date"], "2020-02-03T07:04:05+07:00")
        self.assertEqual(row["category_years_buddhist"], [2569])
        self.assertIn("source_start_year_differs_from_category_year", row["warnings"])

    def test_cms_owner_counters_and_update_timestamps_do_not_change_semantic_hash(self):
        record = fixture()["records"][0]
        before = tcct_api.normalize_record(record, "verdict")
        record.update(owner={"id": "cms-user", "email": "do-not-export@example.org"}, view_count=999, share_count=123, download_count=456)
        record["categories"][0]["category"].update(create_id="cms-user", update_id="other", update_date="2030-01-01")
        record["file_list"][0]["update_date"] = "2030-01-01"
        after = tcct_api.normalize_record(record, "verdict")
        self.assertEqual(before, after)
        self.assertNotIn("cms-user", json.dumps(after))
        record["title"] += " corrected"
        self.assertNotEqual(before["content_sha256"], tcct_api.normalize_record(record, "verdict")["content_sha256"])

    def test_unsafe_usable_reference_urls_fail_closed(self):
        for url in ("http://example.org/a", "https://user:secret@example.org/a", "https://localhost/a", "https://host.local/a", "https://127.0.0.1/a", "https://[::1]/a", "https://10.0.0.1/a", "https://224.0.0.1/a", "https://[ff0e::1]/a", "https://example.org:444/a", "https://2130706433/a", "https://example.org\\@127.0.0.1/a"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                record = fixture()["records"][0]
                record["file_list"][0]["fileUrl"] = url
                tcct_api.normalize_record(record, "verdict")

    def test_complete_set_accepts_partial_last_page(self):
        result = tcct_api.qualify_page_set("verdict", pages())
        self.assertTrue(result["complete"])
        self.assertEqual(result["status"], "complete")
        self.assertEqual((result["total"], result["pages_expected"], result["pages_received"]), (13, 2, 2))
        self.assertEqual(len(result["records"]), 13)
        self.assertEqual(result["duplicates"], [])

    def test_missing_page_never_yields_partial_complete_records(self):
        payloads = pages()
        del payloads[2]
        result = tcct_api.qualify_page_set("verdict", payloads)
        self.assertFalse(result["complete"])
        self.assertEqual(result["records"], [])
        self.assertTrue(any("missing" in e.lower() for e in result["errors"]))

    def test_page_number_mismatch_is_rejected(self):
        payloads = pages()
        payloads[2]["data"]["meta"]["page"] = 1
        self.assertFalse(tcct_api.qualify_page_set("verdict", payloads)["complete"])

    def test_total_limit_or_category_metadata_drift_is_rejected(self):
        for field, value in (("total", 14), ("limit", 13)):
            with self.subTest(field=field):
                payloads = pages()
                payloads[2]["data"]["meta"][field] = value
                result = tcct_api.qualify_page_set("verdict", payloads)
                self.assertFalse(result["complete"])
                self.assertEqual(result["records"], [])
        payloads = pages()
        payloads[2]["data"]["category"] = copy.deepcopy(payloads[2]["data"]["category"])
        payloads[2]["data"]["category"]["name"] = "Changed category name"
        self.assertFalse(tcct_api.qualify_page_set("verdict", payloads)["complete"])

    def test_bool_cannot_pass_as_integer_pagination_or_record_size(self):
        for field in ("total", "page", "limit", "totalPages"):
            with self.subTest(field=field):
                payloads = pages(1)
                payloads[1]["data"]["meta"][field] = True
                self.assertFalse(tcct_api.qualify_page_set("verdict", payloads)["complete"])
        record = fixture()["records"][0]
        record["file_list"][0]["file_size"] = True
        with self.assertRaises(ValueError):
            tcct_api.normalize_record(record, "verdict")

    def test_pagination_booleans_and_arithmetic_must_match(self):
        for field, value in (("hasNextPage", False), ("hasPreviousPage", True), ("hasNextPage", 1), ("totalPages", 3)):
            with self.subTest(field=field, value=value):
                payloads = pages()
                payloads[1]["data"]["meta"][field] = value
                self.assertFalse(tcct_api.qualify_page_set("verdict", payloads)["complete"])

    def test_short_nonfinal_or_overfull_final_page_is_rejected(self):
        payloads = pages()
        payloads[1]["data"]["contents"].pop()
        self.assertFalse(tcct_api.qualify_page_set("verdict", payloads)["complete"])
        payloads = pages()
        payloads[2]["data"]["contents"].append(copy.deepcopy(payloads[1]["data"]["contents"][0]))
        self.assertFalse(tcct_api.qualify_page_set("verdict", payloads)["complete"])

    def test_inactive_draft_or_wrong_category_row_rejects_whole_scope(self):
        for field, value in (("is_active", False), ("is_active", 1), ("is_draft", True), ("is_draft", 0)):
            with self.subTest(field=field, value=value):
                payloads = pages()
                payloads[2]["data"]["contents"][0][field] = value
                result = tcct_api.qualify_page_set("verdict", payloads)
                self.assertFalse(result["complete"])
                self.assertEqual(result["records"], [])
        payloads = pages()
        payloads[2]["data"]["contents"][0] = fixture("verdict-mergers")["records"][0]
        self.assertFalse(tcct_api.qualify_page_set("verdict", payloads)["complete"])

    def test_inconsistent_nested_category_identity_is_rejected(self):
        record = fixture()["records"][0]
        record["categories"][0]["category_id"] = "wrong-id"
        with self.assertRaises(ValueError):
            tcct_api.normalize_record(record, "verdict")

    def test_duplicate_id_on_another_page_rejects_whole_scope(self):
        payloads = pages()
        payloads[2]["data"]["contents"][0]["id"] = "record-0"
        result = tcct_api.qualify_page_set("verdict", payloads)
        self.assertFalse(result["complete"])
        self.assertEqual(result["duplicates"], ["record-0"])
        self.assertEqual(result["records"], [])

    def test_extra_page_wrong_envelope_and_json_are_fail_closed(self):
        cases = [pages(), {1: b'{"status":"error","data":{}}'}, {1: b'{broken'}, {}]
        cases[0][3] = copy.deepcopy(cases[0][2])
        for payloads in cases:
            with self.subTest(pages=list(payloads)):
                result = tcct_api.qualify_page_set("verdict", payloads)
                self.assertFalse(result["complete"])
                self.assertEqual(result["records"], [])

    def test_duplicate_json_keys_are_not_silently_accepted(self):
        raw = json.dumps(pages(1)[1]).replace('"status": "success"', '"status":"error","status":"success"')
        self.assertFalse(tcct_api.qualify_page_set("verdict", {1: raw})["complete"])

    def test_missing_nullable_evidence_fields_fail_but_explicit_null_is_allowed(self):
        nullable_fields = ("start_date", "end_date", "content", "description", "document_number", "url_link", "sub_category_id")
        for field in nullable_fields:
            with self.subTest(field=field):
                payloads = pages(3, "draft-principles-hearing")
                record = payloads[1]["data"]["contents"][0]
                record["is_reference_link"] = False
                record[field] = None
                self.assertTrue(tcct_api.qualify_page_set("draft-principles-hearing", payloads)["complete"])
                del record[field]
                result = tcct_api.qualify_page_set("draft-principles-hearing", payloads)
                self.assertFalse(result["complete"])
                self.assertEqual(result["records"], [])

    def test_missing_membership_null_field_is_not_treated_as_explicit_null(self):
        for field in ("sub_category_id", "sub_category"):
            with self.subTest(field=field):
                payloads = pages(3, "draft-principles-hearing")
                del payloads[1]["data"]["contents"][0]["categories"][0][field]
                self.assertFalse(tcct_api.qualify_page_set("draft-principles-hearing", payloads)["complete"])

    def test_category_parent_requires_presence_but_allows_explicit_null(self):
        def replace_parent(value, remove=False):
            if isinstance(value, dict):
                if value.get("key") == "draft-principles-hearing":
                    if remove:
                        value.pop("parent_id")
                    else:
                        value["parent_id"] = None
                for child in value.values():
                    replace_parent(child, remove)
            elif isinstance(value, list):
                for child in value:
                    replace_parent(child, remove)

        payloads = pages(3, "draft-principles-hearing")
        replace_parent(payloads)
        self.assertTrue(tcct_api.qualify_page_set("draft-principles-hearing", payloads)["complete"])
        replace_parent(payloads, remove=True)
        result = tcct_api.qualify_page_set("draft-principles-hearing", payloads)
        self.assertFalse(result["complete"])
        self.assertEqual(result["records"], [])

    def test_top_level_subcategory_can_be_absent_as_in_captured_hearings(self):
        payloads = pages(3, "draft-principles-hearing")
        for record in payloads[1]["data"]["contents"]:
            record.pop("sub_category", None)
        self.assertTrue(tcct_api.qualify_page_set("draft-principles-hearing", payloads)["complete"])

    def test_nonstandard_json_constants_fail_even_in_ignored_counter(self):
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant):
                payload = pages(1)[1]
                payload["data"]["contents"][0]["view_count"] = "constant-marker"
                raw = json.dumps(payload).replace('"constant-marker"', constant)
                result = tcct_api.qualify_page_set("verdict", {1: raw})
                self.assertFalse(result["complete"])
                self.assertEqual(result["records"], [])

    def test_record_normalization_does_not_modify_input(self):
        record = fixture()["records"][0]
        before = copy.deepcopy(record)
        tcct_api.normalize_record(record, "verdict")
        self.assertEqual(record, before)


if __name__ == "__main__":
    unittest.main()
