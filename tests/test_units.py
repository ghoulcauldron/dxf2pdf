from dxf2pdf.units import units_to_inches

def test_units_to_inches_mm():
    assert abs(units_to_inches(25.4, "mm") - 1.0) < 1e-9

def test_units_to_inches_in():
    assert abs(units_to_inches(2.0, "in") - 2.0) < 1e-9