from packages.shared.bills import display_bill_id


def test_display_bill_id_disambiguates_number_from_congress():
    assert display_bill_id("hres-11-119") == "H.Res. 11 (119th Congress)"
    assert display_bill_id("hr-22-119") == "H.R. 22 (119th Congress)"
    assert display_bill_id("s-1582-119") == "S. 1582 (119th Congress)"
    assert display_bill_id("sres-2-119") == "S.Res. 2 (119th Congress)"
