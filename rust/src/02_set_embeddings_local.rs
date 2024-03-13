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
use redis::{Commands, JsonCommands};
use dotenv::dotenv;
use utilities::get_embeddings;


fn main() -> Result<(), Box<dyn Error>> {
    dotenv().ok();

    let model_path = env::var("BERT_MODEL_PATH").expect("BERT_MODEL_PATH must be set");

    let client = redis::Client::open("redis://127.0.0.1/").unwrap();
    let mut con = client.get_connection().unwrap();

    // Get all keys
    let all_keys: Vec<String> = con.keys("movies:*")?;
    println!("Keys: {}", all_keys.len());

    // Splitting the keys into chunks of 1000
    for chunk in all_keys.chunks(1000) {
        // Convert chunk to Vec<String> as json_get might require an owned Vec
        let keys_chunk: Vec<String> = chunk.to_vec();

        // Get all titles for the current chunk
        let titles: Vec<String> = con.json_get(keys_chunk.clone(), "$.title")?;
        println!("Processing {} titles", titles.len());

        // Get embeddings for the titles
        let embeddings = get_embeddings(&titles, model_path.clone());
        if !embeddings.is_empty() {
            let vector_dimension = embeddings[0].len();
            println!("Vector dimension: {}", vector_dimension);

            // Set embeddings in Redis
            let mut pipeline = redis::pipe();
            for (key, embedding) in keys_chunk.iter().zip(embeddings.iter()) {
                let embedding_json = serde_json::to_string(&embedding).unwrap(); // Convert embedding to JSON string
                pipeline.cmd("JSON.SET").arg(key).arg("$.title_embeddings").arg(embedding_json).ignore();
            }
            pipeline.query(&mut con)?;
        } else {
            println!("No embeddings generated for the current chunk.");
        }
    }

    Ok(())
}