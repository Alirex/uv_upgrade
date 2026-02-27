use super::normalize_package_name;
use rstest::rstest;

#[rstest]
#[case("foo", "foo")]
#[case("Foo", "foo")]
#[case("FoO", "foo")]
//
#[case("FoO-bar", "foo-bar")]
#[case("FoO_bar", "foo-bar")]
#[case("TOMLKit", "tomlkit")]
#[case("Pydantic", "pydantic")]
#[case("pyTEST_BenchMark", "pytest-benchmark")]
fn test_package_name_normalization(#[case] package_name: &str, #[case] expected: &str) {
    let result: String = normalize_package_name(package_name).into();
    assert_eq!(result, expected);
}
