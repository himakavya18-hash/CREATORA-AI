from services import LicensingService

def test_licensing_compliance_check():
    report = LicensingService.check_commercial_compatibility(
        tools_list=['Runway Gen-3', 'Midjourney v6'],
        asset_sources='Original generative output under commercial plan',
        declaration='Full commercial exploitation licensed',
        commercial_required=True,
        paid_ads=True
    )
    assert report['status'] == 'Compatible Based on Recorded Information'
    assert len(report['passed_checks']) >= 2
    assert 'disclaimer' in report

def test_licensing_insufficient_info():
    report = LicensingService.check_commercial_compatibility(
        tools_list=[],
        asset_sources='',
        declaration=''
    )
    assert report['status'] == 'Insufficient Information'
