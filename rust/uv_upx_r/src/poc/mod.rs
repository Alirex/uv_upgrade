// use inquire::{InquireError, Select};
// use std::str::FromStr;
// use toml_edit::{DocumentMut, Value};
//
//
// pub fn poc_dependencies() {
//     let path_to_toml_str = "/home/alirex/PycharmProjects/python_lab/pyproject.toml";
//     let path_to_toml = std::path::Path::new(path_to_toml_str);
//
//     if !path_to_toml.exists() {
//         eprintln!("Error: TOML file does not exist at {}", path_to_toml_str);
//         return;
//     }
//
//     let contents = std::fs::read_to_string(path_to_toml).unwrap();
//     let mut doc = DocumentMut::from_str(&contents).unwrap();
//
//     let project_name = doc["project"]["name"].as_str().unwrap();
//     println!("Project Name: {}", project_name);
//
//     let dependencies = doc["project"]["dependencies"].as_array_mut().unwrap();
//
//     let value_data = "jupyter>=1.1.1";
//     let new_value_data = "jupyter>=2.1.1";
//
//     let mut selected_dependencies: Vec<&mut Value> = Vec::new();
//
//     for dependency in dependencies.iter_mut() {
//         if dependency.as_str().unwrap() == value_data {
//             println!("Found dependency: {}", dependency.as_str().unwrap());
//             // change_dependency_value(dependency, new_value_data);
//             selected_dependencies.push(dependency);
//
//             break;
//         }
//     }
//
//     for dependency in selected_dependencies.iter_mut() {
//         change_dependency_value(dependency, new_value_data);
//     }
//
//     let updated_contents = doc.to_string();
//     std::fs::write(path_to_toml, updated_contents).unwrap();
// }
//
// pub fn poc_select_dependencies() {
//     let options: Vec<&str> = vec![
//         "Banana",
//         "Apple",
//         "Strawberry",
//         "Grapes",
//         "Lemon",
//         "Tangerine",
//         "Watermelon",
//         "Orange",
//         "Pear",
//         "Avocado",
//         "Pineapple",
//     ];
//
//     let ans: Result<&str, InquireError> =
//         Select::new("What's your favorite fruit?", options).prompt();
//
//     match ans {
//         Ok(choice) => println!("{}! That's mine too!", choice),
//         Err(_) => println!("There was an error, please try again"),
//     }
// }
