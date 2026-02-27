use toml_edit::Value;

/// Changes the value of a TOML array element while preserving its formatting (prefix and suffix).
pub fn change_value_from_toml_array(value: &mut Value, new_value_data: &str) {
    let mut new_value = Value::from(new_value_data);
    let decor = new_value.decor_mut();

    if value.decor().suffix().is_some() {
        decor.set_suffix(value.decor().suffix().unwrap().clone())
    }
    if value.decor().prefix().is_some() {
        decor.set_prefix(value.decor().prefix().unwrap().clone())
    }

    *value = new_value;
}
