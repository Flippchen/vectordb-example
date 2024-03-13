mod utilities;

extern crate tokio;
extern crate redis;
extern crate csv;
extern crate serde;
extern crate dotenv;
extern crate postgres;
extern crate rust_decimal;
extern crate rust_bert;
extern crate tch;

use std::{env};
use std::{error::Error};
use dotenv::dotenv;
use utilities::get_embeddings;
use serde::{Deserialize, Serialize};
use std::fs::File;
use redis::{Commands};
use byteorder::{ByteOrder, LittleEndian};

#[derive(Serialize, Deserialize, Debug)]
struct QueryResult {
    score: f32,
    title: String,
    runtime: u32,
    budget: u32,
    revenue: u32,
    overview: String,
}



fn main() -> Result<(), Box<dyn Error>> {
    dotenv().ok();

    let model_path = env::var("BERT_MODEL_PATH").expect("BERT_MODEL_PATH must be set");


    let client = redis::Client::open("redis://127.0.0.1/").unwrap();
    let mut con = client.get_connection().unwrap();

    let query_text = "Bene";
    let num_results = 10;

    let embeddings = get_embeddings(&vec![query_text.to_string()], model_path.clone());
    let query_vector = embeddings[0].clone();

    let mut query_vector_bytes = vec![0u8; 768 * 4];
    LittleEndian::write_f32_into(&query_vector, &mut query_vector_bytes);

    let result: Vec<String> = redis::cmd("FT.SEARCH")
        .arg("idx:movies_vss")
        .arg(format!("*=>[KNN {} @title_embeddings $query_vector AS vector_score]", num_results))
        .arg("PARAMS 1 query_vector")
        .arg(query_vector)
        .arg("RETURN 6 vector_score title overview runtime budget revenue title_embeddings")
        .arg("SORTBY vector_score")
        .arg("DIALECT 2")
        .query(&mut con)?;


    println!("{:?}", result);

    // Output results to CSV
    let file = File::create("queries_table.csv")?;
    let mut wtr = csv::Writer::from_writer(file);
    for result in result.iter() {
        wtr.serialize(result)?;
    }
    wtr.flush()?;

    Ok(())

}